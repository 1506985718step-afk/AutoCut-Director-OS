"""三个核心协议文件的 Pydantic 模型定义"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ============================================================================
# 1. scenes.json (MVP v1)
# ============================================================================

class ScenesMeta(BaseModel):
    schema_: str = Field(alias="schema", default="scenes.v1")
    fps: float = 30.0
    source: str = "davinci/edl"


class ScenesMedia(BaseModel):
    primary_clip_path: str


# ============================================================================
# 视觉元数据模型（AI 视觉分析结果）
# ============================================================================

class VisualMetadata(BaseModel):
    """AI 视觉分析结果 - 让导演能"看懂"画面"""
    summary: str = Field(..., description="画面内容的一句话描述")
    shot_type: str = Field(..., description="景别：特写/近景/中景/全景/远景")
    subjects: List[str] = Field(default_factory=list, description="画面主体：人/猫/汽车/手机")
    action: str = Field(default="", description="主体动作：跑步/说话/静止")
    mood: str = Field(default="", description="画面情绪：开心/压抑/紧张/平静")
    lighting: str = Field(default="", description="光线：自然光/室内/暗调/过曝")
    quality_score: int = Field(default=8, ge=1, le=10, description="画面质量评分 1-10")


class Scene(BaseModel):
    scene_id: str
    start_frame: int
    end_frame: int
    start_tc: str
    end_tc: str
    # 新增：视觉信息（Optional，兼容旧数据）
    visual: Optional[VisualMetadata] = None


class ScenesJSON(BaseModel):
    meta: ScenesMeta
    media: ScenesMedia
    scenes: List[Scene]
    
    class Config:
        populate_by_name = True


# ============================================================================
# 2. transcript.json (MVP v1)
# ============================================================================

class TranscriptMeta(BaseModel):
    schema_: str = Field(alias="schema", default="transcript.v1")
    language: str = "zh"


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class TranscriptJSON(BaseModel):
    meta: TranscriptMeta
    segments: List[TranscriptSegment]
    
    class Config:
        populate_by_name = True


# ============================================================================
# 3. editing_dsl.json (AI 输出，唯一指挥通道)
# ============================================================================

class EditingDSLMeta(BaseModel):
    schema_: str = Field(alias="schema", default="editing_dsl.v1")
    target: str = "douyin"  # douyin, bilibili, youtube
    aspect: str = "9:16"  # 9:16, 16:9, 1:1


class TimelineItem(BaseModel):
    order: int
    scene_id: str
    trim_frames: List[int] = Field(..., min_length=2, max_length=2)  # [in_frame, out_frame] - 内部统一用 frame
    purpose: str  # hook, content, cta
    overlay_text: Optional[str] = None
    broll: List[str] = Field(default_factory=list)  # B-roll 素材列表（必须为空或来自素材库）


class Subtitles(BaseModel):
    mode: str = "from_transcript"  # from_transcript, none, custom


class Music(BaseModel):
    track_path: str
    volume_db: float = -18.0


class EditingPlan(BaseModel):
    timeline: List[TimelineItem]
    subtitles: Subtitles
    music: Music


class Export(BaseModel):
    resolution: str = "1080x1920"  # 1080x1920 (9:16), 1920x1080 (16:9)
    format: str = "mp4"


class EditingDSL(BaseModel):
    meta: EditingDSLMeta
    editing_plan: EditingPlan
    export: Export
    
    class Config:
        populate_by_name = True


# ============================================================================
# 验证器：导入独立的 DSLValidator
# ============================================================================

# 导入独立的验证器（包含 JSON Schema + 两条铁律）
from .dsl_validator import DSLValidator

# 保留旧的验证器类作为兼容性别名
class _LegacyDSLValidator:
    """
    硬规则验证器：防止 AI 幻觉
    
    铁律 1: 不允许"未提供素材库却要求素材调用"
    铁律 2: 坐标体系统一 - 内部只用 frame，对外展示可附带 TC
    """
    
    @staticmethod
    def validate_dsl_against_scenes(
        dsl: Dict[str, Any], 
        scenes_data: Dict[str, Any],
        broll_library: Optional[List[str]] = None
    ) -> List[str]:
        """
        验证 DSL 是否符合 scenes 约束 + 两条铁律
        
        Args:
            dsl: editing_dsl.json 数据
            scenes_data: scenes.json 数据
            broll_library: B-roll 素材库列表（可选）
        
        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []
        
        # 提取 fps（铁律 2：统一坐标体系）
        fps = scenes_data.get("meta", {}).get("fps")
        if not fps:
            errors.append("铁律 2 违反: scenes.json 必须包含 fps")
            return errors
        
        # 构建 scene_id -> Scene 映射
        scenes = scenes_data.get("scenes", [])
        scene_map = {scene["scene_id"]: scene for scene in scenes}
        
        # 验证每个 timeline item
        timeline = dsl.get("editing_plan", {}).get("timeline", [])
        
        for item in timeline:
            scene_id = item.get("scene_id")
            order = item.get("order", "?")
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 基础验证：scene_id 存在性
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            if not scene_id:
                errors.append(f"Timeline item {order}: 缺少 scene_id")
                continue
            
            if scene_id not in scene_map:
                errors.append(
                    f"Timeline item {order}: Scene ID '{scene_id}' 不存在于 scenes.json"
                )
                continue
            
            scene = scene_map[scene_id]
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 铁律 2: 坐标体系统一 - 只用 frame
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            trim_frames = item.get("trim_frames")
            
            if not trim_frames or len(trim_frames) != 2:
                errors.append(
                    f"Timeline item {order}: trim_frames 必须是 [in_frame, out_frame] 格式"
                )
                continue
            
            trim_start, trim_end = trim_frames
            
            # 检查是否使用了 frame（不是 timecode）
            if not isinstance(trim_start, int) or not isinstance(trim_end, int):
                errors.append(
                    f"Timeline item {order}: 铁律 2 违反 - trim_frames 必须是整数帧号，不能是 timecode"
                )
                continue
            
            # 检查 trim_frames 是否在场景范围内
            scene_start = scene.get("start_frame")
            scene_end = scene.get("end_frame")
            
            if trim_start < scene_start:
                errors.append(
                    f"Timeline item {order} ('{scene_id}'): "
                    f"trim_start {trim_start} < scene start {scene_start}"
                )
            
            if trim_end > scene_end:
                errors.append(
                    f"Timeline item {order} ('{scene_id}'): "
                    f"trim_end {trim_end} > scene end {scene_end}"
                )
            
            # 检查 trim_frames 顺序
            if trim_start >= trim_end:
                errors.append(
                    f"Timeline item {order} ('{scene_id}'): "
                    f"trim_start {trim_start} >= trim_end {trim_end}"
                )
            
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            # 铁律 1: 不允许"未提供素材库却要求素材调用"
            # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            broll = item.get("broll", [])
            
            if broll:
                # 如果 DSL 中有 broll 要求
                if not broll_library:
                    # 没有提供素材库 → 违反铁律 1
                    errors.append(
                        f"Timeline item {order}: 铁律 1 违反 - "
                        f"要求 B-roll 素材 {broll}，但未提供素材库。"
                        f"必须降级为 broll: [] + assumptions"
                    )
                else:
                    # 检查每个 broll 是否在素材库中
                    for broll_id in broll:
                        if broll_id not in broll_library:
                            errors.append(
                                f"Timeline item {order}: 铁律 1 违反 - "
                                f"B-roll '{broll_id}' 不存在于素材库中"
                            )
        
        return errors
    
    @staticmethod
    def validate_scenes_has_fps(scenes_data: Dict[str, Any]) -> bool:
        """
        验证 scenes.json 是否包含 fps（铁律 2）
        
        Args:
            scenes_data: scenes.json 数据
        
        Returns:
            是否包含 fps
        """
        fps = scenes_data.get("meta", {}).get("fps")
        return fps is not None and fps > 0
    
    @staticmethod
    def frames_to_timecode(frame: int, fps: float) -> str:
        """
        将帧号转换为 timecode（用于对外展示）
        
        Args:
            frame: 帧号
            fps: 帧率
        
        Returns:
            timecode 字符串 (HH:MM:SS:FF)
        """
        total_seconds = frame / fps
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frames = int(frame % fps)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"
    
    @staticmethod
    def timecode_to_frames(timecode: str, fps: float) -> int:
        """
        将 timecode 转换为帧号（用于输入处理）
        
        Args:
            timecode: timecode 字符串 (HH:MM:SS:FF)
            fps: 帧率
        
        Returns:
            帧号
        """
        parts = timecode.split(":")
        if len(parts) != 4:
            raise ValueError(f"Invalid timecode format: {timecode}")
        
        hours, minutes, seconds, frames = map(int, parts)
        
        total_frames = (
            hours * 3600 * fps +
            minutes * 60 * fps +
            seconds * fps +
            frames
        )
        
        return int(total_frames)
