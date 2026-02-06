"""
Audio Matcher - 音频匹配器

功能：
1. 将外部音频文件匹配到视频文件
2. 三级匹配策略：显式 → 时间戳 → 波形
3. 计算音频偏移量

用于处理"外录音频 + 画面"的场景
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
import subprocess
import json
from datetime import datetime


@dataclass
class AudioMatch:
    """音频匹配结果"""
    video_asset_id: str
    audio_asset_id: Optional[str]
    match_method: str  # "explicit", "timestamp", "waveform", "none"
    confidence: float  # 0-1
    audio_offset_sec: float  # 音频相对视频的偏移（秒）
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_asset_id": self.video_asset_id,
            "audio_asset_id": self.audio_asset_id,
            "match_method": self.match_method,
            "confidence": self.confidence,
            "audio_offset_sec": self.audio_offset_sec
        }


class AudioMatcher:
    """音频匹配器"""
    
    def __init__(self):
        self.timestamp_tolerance_minutes = 5  # 时间戳容差（分钟）
    
    def match_audio_to_videos(
        self,
        video_assets: List[Dict[str, Any]],
        audio_assets: List[Dict[str, Any]]
    ) -> List[AudioMatch]:
        """
        将音频文件匹配到视频文件
        
        Args:
            video_assets: 视频资源列表
            audio_assets: 音频资源列表
        
        Returns:
            匹配结果列表
        """
        matches = []
        
        for video in video_assets:
            match = self._match_single_video(video, audio_assets)
            matches.append(match)
        
        return matches
    
    def _match_single_video(
        self,
        video: Dict[str, Any],
        audio_assets: List[Dict[str, Any]]
    ) -> AudioMatch:
        """
        为单个视频匹配音频
        
        三级匹配策略：
        1. 显式匹配（文件名/同目录）
        2. 时间戳匹配（创建时间）
        3. 波形匹配（互相关）
        """
        video_id = video["asset_id"]
        video_path = video["path"]
        
        # 策略 1: 显式匹配
        match = self._explicit_match(video, audio_assets)
        if match:
            return AudioMatch(
                video_asset_id=video_id,
                audio_asset_id=match["asset_id"],
                match_method="explicit",
                confidence=0.95,
                audio_offset_sec=0.0
            )
        
        # 策略 2: 时间戳匹配
        match = self._timestamp_match(video, audio_assets)
        if match:
            return AudioMatch(
                video_asset_id=video_id,
                audio_asset_id=match["asset_id"],
                match_method="timestamp",
                confidence=0.8,
                audio_offset_sec=match["offset"]
            )
        
        # 策略 3: 波形匹配（可选，较慢）
        # match = self._waveform_match(video, audio_assets)
        # if match:
        #     return AudioMatch(...)
        
        # 无匹配
        return AudioMatch(
            video_asset_id=video_id,
            audio_asset_id=None,
            match_method="none",
            confidence=0.0,
            audio_offset_sec=0.0
        )
    
    def _explicit_match(
        self,
        video: Dict[str, Any],
        audio_assets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        显式匹配：文件名或同目录规则
        
        规则：
        - A001.mp4 ↔ A001.wav
        - 同目录下最近创建的音频文件
        """
        video_path = Path(video["path"])
        video_stem = video_path.stem  # 不含扩展名的文件名
        video_dir = video_path.parent
        
        # 规则 1: 文件名匹配
        for audio in audio_assets:
            audio_path = Path(audio["path"])
            audio_stem = audio_path.stem
            
            # 完全匹配
            if audio_stem == video_stem:
                return audio
            
            # 前缀匹配（A001_video.mp4 ↔ A001_audio.wav）
            if audio_stem.startswith(video_stem) or video_stem.startswith(audio_stem):
                return audio
        
        # 规则 2: 同目录最近文件
        same_dir_audios = [
            audio for audio in audio_assets
            if Path(audio["path"]).parent == video_dir
        ]
        
        if same_dir_audios:
            # 按创建时间排序，选择最近的
            same_dir_audios.sort(
                key=lambda a: abs(
                    self._get_creation_time(a["path"]) - 
                    self._get_creation_time(video["path"])
                )
            )
            return same_dir_audios[0]
        
        return None
    
    def _timestamp_match(
        self,
        video: Dict[str, Any],
        audio_assets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        时间戳匹配：根据创建时间/拍摄时间戳
        
        规则：
        - 音频创建时间与视频创建时间差 < X 分钟
        - 多个候选时选差值最小
        """
        video_time = self._get_creation_time(video["path"])
        
        candidates = []
        
        for audio in audio_assets:
            audio_time = self._get_creation_time(audio["path"])
            
            # 计算时间差（分钟）
            time_diff_minutes = abs(audio_time - video_time) / 60
            
            # 在容差范围内
            if time_diff_minutes <= self.timestamp_tolerance_minutes:
                candidates.append({
                    "asset": audio,
                    "time_diff": time_diff_minutes,
                    "offset": audio_time - video_time  # 音频相对视频的偏移
                })
        
        if not candidates:
            return None
        
        # 选择时间差最小的
        best = min(candidates, key=lambda c: c["time_diff"])
        
        return {
            "asset_id": best["asset"]["asset_id"],
            "offset": best["offset"]
        }
    
    def _get_creation_time(self, file_path: str) -> float:
        """
        获取文件创建时间（Unix 时间戳）
        
        优先级：
        1. 媒体文件的拍摄时间（metadata）
        2. 文件系统创建时间
        """
        # 尝试从媒体元数据获取
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format_tags=creation_time",
                "-of", "json",
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            data = json.loads(result.stdout)
            creation_time_str = data.get("format", {}).get("tags", {}).get("creation_time")
            
            if creation_time_str:
                # 解析 ISO 8601 时间
                dt = datetime.fromisoformat(creation_time_str.replace("Z", "+00:00"))
                return dt.timestamp()
        
        except:
            pass
        
        # 回退到文件系统时间
        try:
            stat = os.stat(file_path)
            return stat.st_ctime  # Windows: 创建时间, Unix: 状态改变时间
        except:
            return 0.0
    
    def _waveform_match(
        self,
        video: Dict[str, Any],
        audio_assets: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        波形匹配：互相关（cross-correlation）
        
        步骤：
        1. 从视频提取低码率音轨
        2. 与外置音频做互相关
        3. 找最佳对齐，得到 offset
        
        注意：这个方法较慢，作为最后手段
        """
        # TODO: 实现波形匹配
        # 需要 librosa 或 scipy
        return None


def match_audio_to_videos(
    video_assets: List[Dict[str, Any]],
    audio_assets: List[Dict[str, Any]]
) -> List[AudioMatch]:
    """
    快捷函数：匹配音频到视频
    
    Args:
        video_assets: 视频资源列表
        audio_assets: 音频资源列表
    
    Returns:
        匹配结果列表
    """
    matcher = AudioMatcher()
    return matcher.match_audio_to_videos(video_assets, audio_assets)
