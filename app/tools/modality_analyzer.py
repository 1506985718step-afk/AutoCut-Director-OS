"""
Content Modality Analyzer - 内容模态分析器

功能：
1. 分析视频/音频内容类型
2. 决定使用 ASR 还是 Vision 为主
3. 极轻量、无需 AI、基于规则

这是 0 号步骤，在抽帧和 ASR 之前运行
"""
import numpy as np
from pathlib import Path
from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass, asdict
import subprocess
import json


@dataclass
class ModalityAnalysis:
    """模态分析结果"""
    has_voice: bool
    speech_ratio: float  # 语音占比
    music_ratio: float   # 音乐占比
    silence_ratio: float # 静音占比
    likely_talking_head: bool  # 可能是口播
    recommended_mode: Literal["ASR_PRIMARY", "VISION_PRIMARY", "HYBRID", "SKIP"]
    confidence: float  # 置信度 0-1
    
    # 详细指标
    audio_present: bool
    avg_volume_db: float
    volume_variance: float
    speech_segments: int
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ModalityAnalyzer:
    """内容模态分析器"""
    
    def __init__(self):
        self.silence_threshold_db = -40  # 静音阈值
        self.speech_min_duration = 0.5   # 最小语音段长度（秒）
        self.talking_head_threshold = 0.3  # 口播判断阈值
    
    def analyze(
        self,
        video_path: str,
        audio_path: Optional[str] = None
    ) -> ModalityAnalysis:
        """
        分析视频/音频内容模态
        
        Args:
            video_path: 视频文件路径
            audio_path: 外部音频文件路径（可选）
        
        Returns:
            模态分析结果
        """
        # 1. 提取音频特征（极轻量）
        audio_features = self._extract_audio_features(video_path, audio_path)
        
        # 2. 分析音频类型
        has_voice = audio_features["has_audio"]
        speech_ratio = audio_features["speech_ratio"]
        music_ratio = audio_features["music_ratio"]
        silence_ratio = audio_features["silence_ratio"]
        
        # 3. 判断是否口播
        likely_talking_head = self._is_likely_talking_head(audio_features)
        
        # 4. 决定推荐模式
        recommended_mode, confidence = self._decide_mode(
            has_voice,
            speech_ratio,
            music_ratio,
            silence_ratio,
            likely_talking_head
        )
        
        return ModalityAnalysis(
            has_voice=has_voice,
            speech_ratio=speech_ratio,
            music_ratio=music_ratio,
            silence_ratio=silence_ratio,
            likely_talking_head=likely_talking_head,
            recommended_mode=recommended_mode,
            confidence=confidence,
            audio_present=audio_features["has_audio"],
            avg_volume_db=audio_features["avg_volume_db"],
            volume_variance=audio_features["volume_variance"],
            speech_segments=audio_features["speech_segments"]
        )
    
    def _extract_audio_features(
        self,
        video_path: str,
        audio_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        提取音频特征（极轻量，不需要 AI）
        
        使用 ffmpeg 提取音频统计信息
        """
        # 选择音频源
        source_path = audio_path if audio_path else video_path
        
        try:
            # 使用 ffmpeg 提取音频统计
            # volumedetect: 音量检测
            # silencedetect: 静音检测
            cmd = [
                "ffmpeg",
                "-i", source_path,
                "-af", f"silencedetect=noise={self.silence_threshold_db}dB:d={self.speech_min_duration},volumedetect",
                "-f", "null",
                "-"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            output = result.stderr
            
            # 解析音频统计
            features = self._parse_audio_stats(output)
            
            # 获取音频时长
            duration = self._get_duration(source_path)
            features["duration"] = duration
            
            # 计算比例
            if duration > 0:
                silence_duration = features["silence_duration"]
                features["silence_ratio"] = silence_duration / duration
                features["speech_ratio"] = 1.0 - features["silence_ratio"]
                
                # 简单的音乐检测（基于音量方差）
                # 音乐通常音量更稳定，语音波动更大
                if features["volume_variance"] < 5.0:
                    features["music_ratio"] = min(0.3, features["speech_ratio"] * 0.3)
                    features["speech_ratio"] -= features["music_ratio"]
                else:
                    features["music_ratio"] = 0.0
            else:
                features["silence_ratio"] = 1.0
                features["speech_ratio"] = 0.0
                features["music_ratio"] = 0.0
            
            return features
        
        except Exception as e:
            print(f"⚠️  音频特征提取失败: {e}")
            # 返回默认值
            return {
                "has_audio": False,
                "avg_volume_db": -100,
                "volume_variance": 0,
                "silence_duration": 0,
                "speech_segments": 0,
                "duration": 0,
                "silence_ratio": 1.0,
                "speech_ratio": 0.0,
                "music_ratio": 0.0
            }
    
    def _parse_audio_stats(self, ffmpeg_output: str) -> Dict[str, Any]:
        """解析 ffmpeg 输出的音频统计"""
        features = {
            "has_audio": False,
            "avg_volume_db": -100,
            "volume_variance": 0,
            "silence_duration": 0,
            "speech_segments": 0
        }
        
        # 解析音量信息
        if "mean_volume:" in ffmpeg_output:
            features["has_audio"] = True
            
            # 提取平均音量
            for line in ffmpeg_output.split("\n"):
                if "mean_volume:" in line:
                    try:
                        volume = float(line.split("mean_volume:")[1].split("dB")[0].strip())
                        features["avg_volume_db"] = volume
                    except:
                        pass
                
                if "max_volume:" in line:
                    try:
                        max_vol = float(line.split("max_volume:")[1].split("dB")[0].strip())
                        # 计算音量方差（简化版）
                        features["volume_variance"] = abs(max_vol - features["avg_volume_db"])
                    except:
                        pass
        
        # 解析静音段
        silence_starts = []
        silence_ends = []
        
        for line in ffmpeg_output.split("\n"):
            if "silence_start:" in line:
                try:
                    start = float(line.split("silence_start:")[1].split()[0])
                    silence_starts.append(start)
                except:
                    pass
            
            if "silence_end:" in line:
                try:
                    end = float(line.split("silence_end:")[1].split("|")[0].strip())
                    silence_ends.append(end)
                except:
                    pass
        
        # 计算静音总时长
        silence_duration = 0
        for start, end in zip(silence_starts, silence_ends):
            silence_duration += (end - start)
        
        features["silence_duration"] = silence_duration
        features["speech_segments"] = len(silence_starts)  # 语音段数 ≈ 静音段数
        
        return features
    
    def _get_duration(self, file_path: str) -> float:
        """获取音频/视频时长"""
        try:
            cmd = [
                "ffprobe",
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "json",
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            data = json.loads(result.stdout)
            duration = float(data["format"]["duration"])
            return duration
        
        except Exception as e:
            print(f"⚠️  获取时长失败: {e}")
            return 0.0
    
    def _is_likely_talking_head(self, audio_features: Dict[str, Any]) -> bool:
        """
        判断是否可能是口播视频
        
        口播特征：
        - 连续语音 > 30%
        - 语音段数较多（说话有停顿）
        - 音量方差较大（人声波动）
        """
        speech_ratio = audio_features["speech_ratio"]
        speech_segments = audio_features["speech_segments"]
        volume_variance = audio_features["volume_variance"]
        duration = audio_features["duration"]
        
        # 规则 1: 语音占比 > 30%
        if speech_ratio < self.talking_head_threshold:
            return False
        
        # 规则 2: 语音段数合理（每分钟 > 5 段）
        if duration > 0:
            segments_per_minute = (speech_segments / duration) * 60
            if segments_per_minute < 5:
                return False
        
        # 规则 3: 音量方差 > 5dB（人声波动）
        if volume_variance < 5.0:
            return False
        
        return True
    
    def _decide_mode(
        self,
        has_voice: bool,
        speech_ratio: float,
        music_ratio: float,
        silence_ratio: float,
        likely_talking_head: bool
    ) -> tuple[str, float]:
        """
        决定推荐模式
        
        决策矩阵（写死规则）：
        
        | 素材类型 | 主要理解方式 | Vision 频率 |
        |---------|------------|-----------|
        | 出镜口播 | ASR | 低 |
        | 教程解说 | ASR | 低 |
        | Vlog | ASR | 中 |
        | 产品展示 | Vision | 高 |
        | B-roll | Vision | 高 |
        | 无声素材 | Vision | 必须 |
        | 外录音频+画面 | ASR（音频）| 补充 |
        
        Returns:
            (推荐模式, 置信度)
        """
        # 规则 1: 无音频 → VISION_PRIMARY
        if not has_voice or speech_ratio < 0.05:
            return "VISION_PRIMARY", 0.95
        
        # 规则 2: 口播 → ASR_PRIMARY
        if likely_talking_head and speech_ratio > 0.5:
            return "ASR_PRIMARY", 0.9
        
        # 规则 3: 高语音占比 → ASR_PRIMARY
        if speech_ratio > 0.7:
            return "ASR_PRIMARY", 0.85
        
        # 规则 4: 中等语音占比 → HYBRID
        if 0.3 <= speech_ratio <= 0.7:
            return "HYBRID", 0.7
        
        # 规则 5: 低语音占比 → VISION_PRIMARY
        if speech_ratio < 0.3:
            return "VISION_PRIMARY", 0.8
        
        # 规则 6: 音乐为主 → VISION_PRIMARY
        if music_ratio > 0.5:
            return "VISION_PRIMARY", 0.75
        
        # 默认: HYBRID
        return "HYBRID", 0.5


def analyze_modality(
    video_path: str,
    audio_path: Optional[str] = None
) -> ModalityAnalysis:
    """
    快捷函数：分析内容模态
    
    Args:
        video_path: 视频文件路径
        audio_path: 外部音频文件路径（可选）
    
    Returns:
        模态分析结果
    """
    analyzer = ModalityAnalyzer()
    return analyzer.analyze(video_path, audio_path)


def should_run_vision(
    modality: ModalityAnalysis,
    segment_has_transcript: bool = False,
    transcript_confidence: float = 1.0
) -> bool:
    """
    判断是否应该运行 Vision 分析
    
    Vision 必须是"补充"，不能默认跑
    
    Args:
        modality: 模态分析结果
        segment_has_transcript: 该段是否有转录
        transcript_confidence: 转录置信度
    
    Returns:
        是否应该运行 Vision
    """
    mode = modality.recommended_mode
    
    # 规则 1: VISION_PRIMARY → 必须跑
    if mode == "VISION_PRIMARY":
        return True
    
    # 规则 2: ASR_PRIMARY → 只在必要时跑
    if mode == "ASR_PRIMARY":
        # 2.1 没有转录 → 跑 Vision
        if not segment_has_transcript:
            return True
        
        # 2.2 转录置信度低 → 跑 Vision
        if transcript_confidence < 0.6:
            return True
        
        # 2.3 其他情况 → 不跑
        return False
    
    # 规则 3: HYBRID → 选择性跑
    if mode == "HYBRID":
        # 如果没有转录或置信度低 → 跑
        if not segment_has_transcript or transcript_confidence < 0.7:
            return True
        return False
    
    # 规则 4: SKIP → 不跑
    return False
