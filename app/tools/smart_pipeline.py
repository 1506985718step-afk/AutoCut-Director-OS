"""
Smart Pipeline - 智能处理流水线

完整流程：
Step 0: 模态分析（超快）
Step 1: 粗切镜头（轻量）
Step 2A: ASR 主路径（大多数情况）
Step 2B: Vision 补充路径（只在必要时）
Step 3: 融合生成 ShotCards

主流程：Ingest → Triage → Segment → ASR/Vision → Fuse
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import json

from .modality_analyzer import ModalityAnalyzer, should_run_vision
from .audio_matcher import AudioMatcher


class SmartPipeline:
    """智能处理流水线"""
    
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir
        self.input_dir = job_dir / "input"
        self.output_dir = job_dir / "output"
        self.temp_dir = job_dir / "temp"
        
        # 确保目录存在
        self.input_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
        
        # 初始化分析器
        self.modality_analyzer = ModalityAnalyzer()
        self.audio_matcher = AudioMatcher()
    
    def run(self, input_paths: List[str]) -> Dict[str, Any]:
        """
        运行完整流水线
        
        Args:
            input_paths: 输入文件路径列表
        
        Returns:
            处理结果
        """
        print("\n" + "="*60)
        print("🚀 Smart Pipeline 启动")
        print("="*60)
        
        # Step 1: Ingest & Index
        print("\n📦 Step 1: Ingest & Index")
        assets = self._build_assets_manifest(input_paths)
        self._save_json("assets_manifest.json", assets)
        print(f"✓ 发现 {len(assets['videos'])} 个视频, {len(assets['audios'])} 个音频")
        
        # Step 2: Triage (cheap quality check)
        print("\n🔍 Step 2: Quick Quality Triage")
        assets = self._quick_quality_triage(assets)
        self._save_json("assets_manifest_with_triage.json", assets)
        usable_count = sum(1 for v in assets['videos'] if v.get('quality', {}).get('usable', True))
        print(f"✓ {usable_count}/{len(assets['videos'])} 个视频可用")
        
        # Step 3: Match external audio to video
        print("\n🎵 Step 3: Match Audio to Video")
        assets = self._match_audio_to_video(assets)
        self._save_json("assets_manifest_with_matching.json", assets)
        matched_count = sum(1 for v in assets['videos'] if v.get('matched_audio_asset_id'))
        print(f"✓ {matched_count} 个视频匹配到外部音频")
        
        # Step 4: Decide modality per asset
        print("\n🧠 Step 4: Modality Analysis")
        policies = self._decide_modality_policies(assets)
        self._save_json("modality_policy.json", policies)
        self._print_modality_summary(policies)
        
        # Step 5: Segment assets
        print("\n✂️  Step 5: Segment Assets")
        segments = self._segment_assets(assets, policies)
        self._save_json("segments.json", segments)
        print(f"✓ 生成 {len(segments)} 个可剪辑段")
        
        # Step 6A: ASR pass
        print("\n🎤 Step 6A: ASR Recognition")
        transcripts = self._run_asr_pass(segments, policies)
        self._save_json("transcripts.json", transcripts)
        print(f"✓ 转录 {len(transcripts)} 个语音段")
        
        # Step 6B: Vision pass (only when needed)
        print("\n👁️  Step 6B: Vision Analysis (selective)")
        vision_caps = self._run_vision_pass(segments, policies, transcripts)
        self._save_json("vision_captions.json", vision_caps)
        print(f"✓ 分析 {len(vision_caps)} 个视觉段")
        
        # Step 6C: Cloud structuring
        print("\n🧠 Step 6C: Structure Vision Data")
        vision_meta = self._structure_vision_data(vision_caps)
        self._save_json("vision_meta.json", vision_meta)
        print(f"✓ 结构化 {len(vision_meta)} 个视觉元数据")
        
        # Step 7: Fuse into ShotCards
        print("\n🎬 Step 7: Generate ShotCards")
        shotcards = self._generate_shotcards(segments, transcripts, vision_meta, assets)
        self._save_json("shotcards.json", shotcards)
        print(f"✓ 生成 {len(shotcards)} 个 ShotCard")
        
        print("\n" + "="*60)
        print("✅ Smart Pipeline 完成")
        print("="*60 + "\n")
        
        return {
            "job_dir": str(self.job_dir),
            "assets": assets,
            "policies": policies,
            "segments": segments,
            "transcripts": transcripts,
            "vision_meta": vision_meta,
            "shotcards": shotcards
        }
    
    def _build_assets_manifest(self, input_paths: List[str]) -> Dict[str, Any]:
        """构建资源清单"""
        videos = []
        audios = []
        
        for path in input_paths:
            p = Path(path)
            
            if not p.exists():
                print(f"⚠️  文件不存在: {path}")
                continue
            
            # 判断文件类型
            ext = p.suffix.lower()
            
            if ext in ['.mp4', '.mov', '.avi', '.mkv', '.mts', '.m4v']:
                videos.append({
                    "asset_id": f"V{len(videos)+1:03d}",
                    "type": "video",
                    "path": str(p.absolute()),
                    "filename": p.name,
                    "size_mb": p.stat().st_size / (1024*1024)
                })
            
            elif ext in ['.wav', '.mp3', '.aac', '.m4a', '.flac']:
                audios.append({
                    "asset_id": f"A{len(audios)+1:03d}",
                    "type": "audio",
                    "path": str(p.absolute()),
                    "filename": p.name,
                    "size_mb": p.stat().st_size / (1024*1024)
                })
        
        return {
            "videos": videos,
            "audios": audios
        }
    
    def _quick_quality_triage(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        """快速质量筛选（无需 AI）"""
        for video in assets["videos"]:
            # 简单规则：文件大小 < 1MB 可能损坏
            usable = video["size_mb"] >= 1.0
            
            video["quality"] = {
                "usable": usable,
                "reason": "文件过小" if not usable else "OK"
            }
        
        return assets
    
    def _match_audio_to_video(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        """匹配外部音频到视频"""
        if not assets["audios"]:
            return assets
        
        matches = self.audio_matcher.match_audio_to_videos(
            assets["videos"],
            assets["audios"]
        )
        
        # 更新视频资源
        for match in matches:
            for video in assets["videos"]:
                if video["asset_id"] == match.video_asset_id:
                    video["matched_audio_asset_id"] = match.audio_asset_id
                    video["audio_match_method"] = match.match_method
                    video["audio_match_confidence"] = match.confidence
                    video["audio_offset_sec"] = match.audio_offset_sec
                    break
        
        return assets
    
    def _decide_modality_policies(self, assets: Dict[str, Any]) -> Dict[str, Any]:
        """决定每个资源的模态策略"""
        policies = {}
        
        for video in assets["videos"]:
            if not video.get("quality", {}).get("usable", True):
                policies[video["asset_id"]] = {
                    "mode": "SKIP",
                    "reason": "质量不可用"
                }
                continue
            
            # 获取音频路径
            audio_path = None
            if video.get("matched_audio_asset_id"):
                for audio in assets["audios"]:
                    if audio["asset_id"] == video["matched_audio_asset_id"]:
                        audio_path = audio["path"]
                        break
            
            # 分析模态
            analysis = self.modality_analyzer.analyze(
                video["path"],
                audio_path
            )
            
            policies[video["asset_id"]] = {
                "mode": analysis.recommended_mode,
                "confidence": analysis.confidence,
                "has_voice": analysis.has_voice,
                "speech_ratio": analysis.speech_ratio,
                "likely_talking_head": analysis.likely_talking_head
            }
        
        return policies
    
    def _print_modality_summary(self, policies: Dict[str, Any]):
        """打印模态分析摘要"""
        mode_counts = {}
        for policy in policies.values():
            mode = policy["mode"]
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        for mode, count in mode_counts.items():
            print(f"  {mode}: {count} 个")
    
    def _segment_assets(
        self,
        assets: Dict[str, Any],
        policies: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """分割资源为可剪辑段"""
        segments = []
        
        for video in assets["videos"]:
            asset_id = video["asset_id"]
            policy = policies.get(asset_id, {})
            mode = policy.get("mode", "SKIP")
            
            if mode == "SKIP":
                continue
            
            # 简化版：固定时长分段（实际应该用 VAD 或场景检测）
            # TODO: 实现基于 VAD 的智能分段
            segments.append({
                "seg_id": f"{asset_id}_S001",
                "asset_id": asset_id,
                "start_sec": 0,
                "end_sec": 999999,  # 整个视频
                "priority": "high" if mode == "ASR_PRIMARY" else "medium"
            })
        
        return segments
    
    def _run_asr_pass(
        self,
        segments: List[Dict[str, Any]],
        policies: Dict[str, Any]
    ) -> Dict[str, Any]:
        """ASR 识别（仅对选定段）"""
        transcripts = {}
        
        for seg in segments:
            asset_id = seg["asset_id"]
            policy = policies.get(asset_id, {})
            mode = policy.get("mode", "SKIP")
            
            # 只对 ASR_PRIMARY 和 HYBRID 运行 ASR
            if mode not in ["ASR_PRIMARY", "HYBRID"]:
                continue
            
            # TODO: 实际调用 Whisper ASR
            # 这里用占位符
            transcripts[seg["seg_id"]] = {
                "text": "[ASR placeholder]",
                "confidence": 0.9,
                "words": []
            }
        
        return transcripts
    
    def _run_vision_pass(
        self,
        segments: List[Dict[str, Any]],
        policies: Dict[str, Any],
        transcripts: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Vision 分析（仅在必要时）"""
        vision_caps = {}
        
        for seg in segments:
            asset_id = seg["asset_id"]
            seg_id = seg["seg_id"]
            policy = policies.get(asset_id, {})
            
            # 构建模态分析对象（简化版）
            from .modality_analyzer import ModalityAnalysis
            modality = ModalityAnalysis(
                has_voice=policy.get("has_voice", False),
                speech_ratio=policy.get("speech_ratio", 0.0),
                music_ratio=0.0,
                silence_ratio=1.0 - policy.get("speech_ratio", 0.0),
                likely_talking_head=policy.get("likely_talking_head", False),
                recommended_mode=policy.get("mode", "SKIP"),
                confidence=policy.get("confidence", 0.0),
                audio_present=policy.get("has_voice", False),
                avg_volume_db=-20,
                volume_variance=10,
                speech_segments=0
            )
            
            # 判断是否应该运行 Vision
            has_transcript = seg_id in transcripts
            transcript_conf = transcripts.get(seg_id, {}).get("confidence", 1.0)
            
            if should_run_vision(modality, has_transcript, transcript_conf):
                # TODO: 实际调用 Vision 分析
                # 这里用占位符
                vision_caps[seg_id] = "[Vision caption placeholder]"
        
        return vision_caps
    
    def _structure_vision_data(self, vision_caps: Dict[str, Any]) -> Dict[str, Any]:
        """结构化 Vision 数据（使用 LLM）"""
        vision_meta = {}
        
        for seg_id, caption in vision_caps.items():
            # TODO: 实际调用 DeepSeek 结构化
            # 这里用占位符
            vision_meta[seg_id] = {
                "summary": caption,
                "shot_type": "中景",
                "subjects": ["人物"],
                "mood": "中性",
                "quality_score": 7
            }
        
        return vision_meta
    
    def _generate_shotcards(
        self,
        segments: List[Dict[str, Any]],
        transcripts: Dict[str, Any],
        vision_meta: Dict[str, Any],
        assets: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """生成 ShotCards"""
        shotcards = []
        
        for seg in segments:
            seg_id = seg["seg_id"]
            
            shotcard = {
                "shotcard_id": seg_id,
                "asset_id": seg["asset_id"],
                "start_sec": seg["start_sec"],
                "end_sec": seg["end_sec"],
                "transcript": transcripts.get(seg_id),
                "vision": vision_meta.get(seg_id),
                "usable": True,
                "score": 7.0,
                "intent_tags": [],
                "entities": []
            }
            
            # 应用丢弃规则
            shotcard = self._apply_drop_rules(shotcard)
            
            if shotcard["usable"]:
                shotcards.append(shotcard)
        
        return shotcards
    
    def _apply_drop_rules(self, shotcard: Dict[str, Any]) -> Dict[str, Any]:
        """应用丢弃规则"""
        # 规则 1: 无内容
        if not shotcard["transcript"] and not shotcard["vision"]:
            shotcard["usable"] = False
            shotcard["drop_reason"] = "无内容"
        
        return shotcard
    
    def _save_json(self, filename: str, data: Any):
        """保存 JSON 文件"""
        path = self.temp_dir / filename
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def run_smart_pipeline(job_dir: Path, input_paths: List[str]) -> Dict[str, Any]:
    """
    快捷函数：运行智能流水线
    
    Args:
        job_dir: Job 目录
        input_paths: 输入文件路径列表
    
    Returns:
        处理结果
    """
    pipeline = SmartPipeline(job_dir)
    return pipeline.run(input_paths)
