"""
视觉分析器工厂 - 自动选择最佳分析器

根据配置自动选择：
- 本地模型（Ollama）- 零成本，快速，推荐
- 云端模型（OpenAI GPT-4o Vision）- 高质量，有成本

v2.0: 集成 RuntimeProfile 和 ExecutionPolicy
"""
from typing import Optional, Literal
from ..config import settings
from ..models.schemas import ScenesJSON


def get_visual_analyzer(
    force_local: Optional[bool] = None,
    force_cloud: Optional[bool] = None,
    model: Optional[str] = None,
    use_policy: bool = True
):
    """
    获取视觉分析器实例
    
    Args:
        force_local: 强制使用本地模型
        force_cloud: 强制使用云端模型
        model: 指定模型名称（本地：moondream/llava-phi3，云端：gpt-4o）
        use_policy: 是否使用执行策略（推荐）
    
    Returns:
        视觉分析器实例
    """
    # 优先级：force_cloud > force_local > ExecutionPolicy > 配置文件
    use_local = settings.USE_LOCAL_VISION
    selected_model = model
    local_backend = settings.LOCAL_VISION_PROVIDER  # ollama 或 lmstudio
    
    # 如果启用策略，从 ExecutionPolicy 获取配置
    if use_policy and not force_local and not force_cloud and not model:
        try:
            from ..core.execution_policy import get_execution_policy
            policy = get_execution_policy()
            
            use_local = (policy.vision.provider == "local")
            selected_model = policy.vision.model
            local_backend = policy.vision.local_backend or local_backend
            
            print(f"📊 使用执行策略: provider={policy.vision.provider}, backend={local_backend}, model={selected_model}")
        except Exception as e:
            print(f"⚠️  无法获取执行策略，使用默认配置: {e}")
    
    # 强制参数覆盖
    if force_cloud:
        use_local = False
    elif force_local:
        use_local = True
    
    if model:
        selected_model = model
    
    if use_local:
        # 使用本地模型
        if local_backend == "lmstudio":
            # 使用 LM Studio
            from .visual_analyzer_lmstudio import LMStudioVisualAnalyzer
            
            lmstudio_model = selected_model or settings.LMSTUDIO_MODEL
            
            print(f"🏠 使用 LM Studio 视觉模型: {lmstudio_model}")
            
            return LMStudioVisualAnalyzer(
                base_url=settings.LMSTUDIO_HOST,
                model=lmstudio_model
            )
        else:
            # 使用 Ollama
            from .visual_analyzer_local import LocalVisualAnalyzer
            
            local_model = selected_model or settings.LOCAL_VISION_MODEL
            
            # 检查是否应该使用 CPU 模式
            device = "auto"
            try:
                from ..core.runtime_monitor import get_runtime_monitor
                monitor = get_runtime_monitor()
                if monitor.should_use_cpu_for_vision():
                    device = "cpu"
                    print(f"⚠️  资源紧张，强制使用 CPU 模式")
            except:
                pass
            
            print(f"🏠 使用 Ollama 视觉模型: {local_model} (device={device})")
            
            return LocalVisualAnalyzer(
                model=local_model,
                ollama_host=settings.OLLAMA_HOST
            )
    else:
        # 使用云端模型
        from .visual_analyzer import VisualAnalyzer
        
        cloud_model = selected_model or "gpt-4o"
        print(f"☁️  使用云端视觉模型: {cloud_model}")
        return VisualAnalyzer()


def analyze_scenes_auto(
    scenes_data: ScenesJSON,
    video_path: str,
    max_scenes: Optional[int] = None,
    force_local: Optional[bool] = None,
    force_cloud: Optional[bool] = None,
    model: Optional[str] = None,
    use_policy: bool = True
) -> ScenesJSON:
    """
    自动选择最佳分析器进行场景分析
    
    Args:
        scenes_data: 场景数据
        video_path: 视频文件路径
        max_scenes: 限制分析数量（如果为 None，从 ExecutionPolicy 获取）
        force_local: 强制使用本地模型
        force_cloud: 强制使用云端模型
        model: 指定模型名称
        use_policy: 是否使用执行策略（推荐）
    
    Returns:
        更新后的场景数据
    """
    # 如果未指定 max_scenes，从 ExecutionPolicy 获取
    if max_scenes is None and use_policy:
        try:
            from ..core.execution_policy import get_execution_policy
            policy = get_execution_policy()
            max_scenes = policy.vision.max_scenes
            print(f"📊 从执行策略获取 max_scenes: {max_scenes}")
        except:
            pass
    
    analyzer = get_visual_analyzer(
        force_local=force_local,
        force_cloud=force_cloud,
        model=model,
        use_policy=use_policy
    )
    
    # 记录任务结果
    try:
        result = analyzer.analyze_scene_visuals(
            scenes_data,
            video_path,
            max_scenes
        )
        
        # 记录成功
        try:
            from ..core.runtime_monitor import get_runtime_monitor
            monitor = get_runtime_monitor()
            monitor.record_task_result(success=True)
        except:
            pass
        
        return result
    
    except Exception as e:
        # 记录失败
        try:
            from ..core.runtime_monitor import get_runtime_monitor
            monitor = get_runtime_monitor()
            monitor.record_task_result(success=False)
        except:
            pass
        
        raise e
