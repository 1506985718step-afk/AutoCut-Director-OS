"""动作定义（数据驱动设计）- Executor 只跑动作"""
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class Action:
    """
    动作数据类
    
    Attributes:
        name: 动作名称（CreateTimeline, AppendScene, ImportSRT, AddMusic, ExportMP4）
        params: 动作参数字典
    """
    name: str
    params: Dict[str, Any]
    
    def __str__(self):
        return f"{self.name}({', '.join(f'{k}={v}' for k, v in self.params.items())})"


# ============================================================================
# 动作工厂函数
# ============================================================================

def create_timeline(name: str, fps: float, resolution: dict = None) -> Action:
    """
    创建时间线动作
    
    Args:
        name: 时间线名称
        fps: 帧率
        resolution: 分辨率字典 {"width": 1920, "height": 1080}
    """
    return Action("CreateTimeline", {
        "name": name,
        "fps": fps,
        "resolution": resolution or {"width": 1920, "height": 1080}
    })


def append_scene(scene_id: str, in_frame: int, out_frame: int, source: str) -> Action:
    """
    添加场景片段动作
    
    Args:
        scene_id: 场景 ID（用于日志）
        in_frame: 入点帧数
        out_frame: 出点帧数
        source: 媒体文件路径
    """
    return Action("AppendScene", {
        "scene_id": scene_id,
        "in_frame": in_frame,
        "out_frame": out_frame,
        "source": source
    })


def import_srt(path: str) -> Action:
    """
    导入 SRT 字幕动作
    
    Args:
        path: SRT 文件路径
    """
    return Action("ImportSRT", {
        "path": path
    })


def add_music(path: str, volume_db: float) -> Action:
    """
    添加背景音乐动作
    
    Args:
        path: 音频文件路径
        volume_db: 音量（dB）
    """
    return Action("AddMusic", {
        "path": path,
        "volume_db": volume_db
    })


def export_mp4(path: str, resolution: str) -> Action:
    """
    导出 MP4 动作
    
    Args:
        path: 输出文件路径
        resolution: 分辨率字符串（如 "1080x1920"）
    """
    return Action("ExportMP4", {
        "path": path,
        "resolution": resolution
    })


def add_text_overlay(text: str, start_frame: int, duration_frames: int, style: dict = None) -> Action:
    """
    添加文字叠加动作（overlay_text）
    
    Args:
        text: 文字内容
        start_frame: 开始帧
        duration_frames: 持续帧数
        style: 文字样式字典（可选）
    """
    return Action("AddTextOverlay", {
        "text": text,
        "start_frame": start_frame,
        "duration_frames": duration_frames,
        "style": style or {}
    })


def render_subtitles(transcript_segments: list, fps: float, style: str = "bold_yellow") -> Action:
    """
    渲染字幕动作（从 transcript 生成，使用 SRT 方案）
    
    Args:
        transcript_segments: transcript.json 中的 segments 列表
        fps: 时间线帧率
        style: 字幕样式预设（用于文档说明）
            - bold_yellow: 抖音风格（粗体黄字黑边）
            - clean_white: 简洁白字
            - elegant_black: 优雅黑字
    
    注意: 实际样式需要在 DaVinci Resolve 中手动设置或应用预设
    """
    return Action("RenderSubtitles", {
        "transcript_segments": transcript_segments,
        "fps": fps,
        "style": style
    })


def create_text_layer(text_items: list, track_index: int = 3) -> Action:
    """
    创建文字叠加层动作（批量处理 overlay_text，使用 SRT 方案）
    
    Args:
        text_items: 文字列表，格式：[
            {
                "content": "第一步就错了",
                "start_frame": 30,
                "duration_frames": 60
            },
            ...
        ]
        track_index: 字幕轨道索引
    
    这是处理 DSL 中 overlay_text 的推荐方法
    """
    return Action("CreateTextLayer", {
        "text_items": text_items,
        "track_index": track_index
    })


# ============================================================================
# 动作执行器映射
# ============================================================================

def execute_action(action: Action, adapter) -> Any:
    """
    执行动作（根据动作名称调用对应的 adapter 方法）
    
    Args:
        action: Action 对象
        adapter: ResolveAdapter 实例
        
    Returns:
        执行结果
        
    Raises:
        ValueError: 未知的动作名称
    """
    if action.name == "CreateTimeline":
        return adapter.create_timeline(
            name=action.params["name"],
            framerate=action.params["fps"],
            resolution=action.params["resolution"]
        )
    
    elif action.name == "AppendScene":
        # 将帧数转换为秒
        fps = float(adapter.current_timeline.GetSetting("timelineFrameRate"))
        start_sec = action.params["in_frame"] / fps
        end_sec = action.params["out_frame"] / fps
        
        return adapter.append_clip(
            source=action.params["source"],
            start=start_sec,
            end=end_sec,
            track=1
        )
    
    elif action.name == "ImportSRT":
        return adapter.import_srt(
            srt_path=action.params["path"],
            track=2
        )
    
    elif action.name == "AddMusic":
        # 将 dB 转换为线性音量
        volume_linear = 10 ** (action.params["volume_db"] / 20)
        
        return adapter.add_audio(
            audio_path=action.params["path"],
            start=0,
            volume=volume_linear
        )
    
    elif action.name == "ExportMP4":
        return adapter.export(
            output_path=action.params["path"],
            preset="H.264",
            quality="high"
        )
    
    elif action.name == "AddTextOverlay":
        return adapter.add_text_overlay(
            text=action.params["text"],
            start_frame=action.params["start_frame"],
            duration_frames=action.params["duration_frames"],
            track=2,
            style=action.params.get("style")
        )
    
    elif action.name == "RenderSubtitles":
        return adapter.render_subtitles_from_transcript(
            transcript_segments=action.params["transcript_segments"],
            fps=action.params["fps"],
            style=action.params.get("style", "bold_yellow")
        )
    
    elif action.name == "CreateTextLayer":
        return adapter.create_text_layer_from_dsl(
            text_items=action.params["text_items"],
            track_index=action.params.get("track_index", 3)
        )
    
    else:
        raise ValueError(f"Unknown action: {action.name}")
