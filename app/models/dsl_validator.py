"""
DSL 验证器 - 使用 JSON Schema 验证 + 两条铁律
"""
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import jsonschema


class DSLValidator:
    """
    DSL 验证器
    
    验证层次：
    1. JSON Schema 验证（格式和类型）
    2. 两条铁律验证
    3. 业务规则验证（scene_id 存在性、trim_frames 范围等）
    """
    
    # 加载 JSON Schema
    _schema_path = Path(__file__).parent / "dsl_schema.json"
    with open(_schema_path, 'r', encoding='utf-8') as f:
        _schema = json.load(f)
    
    @classmethod
    def validate_schema(cls, dsl: Dict[str, Any]) -> List[str]:
        """
        验证 DSL 是否符合 JSON Schema
        
        Args:
            dsl: editing_dsl.json 数据
        
        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []
        
        try:
            jsonschema.validate(instance=dsl, schema=cls._schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema 验证失败: {e.message}")
            # 添加详细路径
            if e.path:
                path = ".".join(str(p) for p in e.path)
                errors.append(f"  位置: {path}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema 定义错误: {e.message}")
        
        return errors
    
    @classmethod
    def validate_dsl_against_scenes(
        cls,
        dsl: Dict[str, Any],
        scenes_data: Dict[str, Any],
        broll_library: Optional[List[str]] = None
    ) -> List[str]:
        """
        完整验证：Schema + 两条铁律 + 业务规则
        
        Args:
            dsl: editing_dsl.json 数据
            scenes_data: scenes.json 数据
            broll_library: B-roll 素材库列表（可选）
        
        Returns:
            错误列表（空列表表示验证通过）
        """
        errors = []
        
        # 1. JSON Schema 验证
        schema_errors = cls.validate_schema(dsl)
        errors.extend(schema_errors)
        
        # 如果 Schema 验证失败，不继续后续验证
        if schema_errors:
            return errors
        
        # 2. 铁律 2：验证 scenes.json 必须包含 fps
        fps = scenes_data.get("meta", {}).get("fps")
        if not fps:
            errors.append("铁律 2 违反: scenes.json 必须包含 fps")
            return errors
        
        # 3. 构建 scene_id -> Scene 映射
        scenes = scenes_data.get("scenes", [])
        scene_map = {scene["scene_id"]: scene for scene in scenes}
        
        # 4. 验证每个 timeline item
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
    
    @classmethod
    def validate_scenes_has_fps(cls, scenes_data: Dict[str, Any]) -> bool:
        """
        验证 scenes.json 是否包含 fps（铁律 2）
        
        Args:
            scenes_data: scenes.json 数据
        
        Returns:
            是否包含 fps
        """
        fps = scenes_data.get("meta", {}).get("fps")
        return fps is not None and fps > 0
    
    @classmethod
    def frames_to_timecode(cls, frame: int, fps: float) -> str:
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
    
    @classmethod
    def timecode_to_frames(cls, timecode: str, fps: float) -> int:
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


# 便捷函数
def validate_dsl(
    dsl: Dict[str, Any],
    scenes_data: Dict[str, Any],
    broll_library: Optional[List[str]] = None
) -> List[str]:
    """
    便捷函数：验证 DSL
    
    Args:
        dsl: editing_dsl.json 数据
        scenes_data: scenes.json 数据
        broll_library: B-roll 素材库列表（可选）
    
    Returns:
        错误列表（空列表表示验证通过）
    """
    return DSLValidator.validate_dsl_against_scenes(dsl, scenes_data, broll_library)
