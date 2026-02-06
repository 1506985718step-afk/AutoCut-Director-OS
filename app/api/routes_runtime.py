"""
Runtime Profile API - 运行时配置文件接口

功能：
1. 获取运行时配置文件
2. 获取执行策略
3. 获取监控状态
4. 手动触发降级
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..core.runtime_profile import (
    get_runtime_profile,
    save_runtime_profile,
    load_runtime_profile
)
from ..core.execution_policy import (
    get_execution_policy,
    degrade_execution_policy
)
from ..core.runtime_monitor import get_runtime_monitor
from ..config import settings

router = APIRouter(prefix="/runtime", tags=["runtime"])


@router.get("/profile")
def get_profile() -> Dict[str, Any]:
    """
    获取运行时配置文件
    
    Returns:
        运行时配置文件（包含硬件信息、AI 运行时、编辑器等）
    """
    profile = get_runtime_profile()
    
    return {
        "profile": profile.to_dict(),
        "explanation": profile.get_explanation()
    }


@router.get("/profile/reload")
def reload_profile() -> Dict[str, Any]:
    """
    重新检测运行时配置文件
    
    Returns:
        更新后的运行时配置文件
    """
    profile = get_runtime_profile(force_reload=True)
    
    # 保存到磁盘
    profile_path = settings.BASE_DIR / "runtime_profile.json"
    save_runtime_profile(profile_path)
    
    return {
        "profile": profile.to_dict(),
        "explanation": profile.get_explanation(),
        "saved_to": str(profile_path)
    }


@router.get("/policy")
def get_policy() -> Dict[str, Any]:
    """
    获取执行策略
    
    Returns:
        执行策略（包含 Vision、Planning、Editing 策略）
    """
    policy = get_execution_policy()
    
    return {
        "policy": policy.to_dict()
    }


@router.get("/policy/reload")
def reload_policy() -> Dict[str, Any]:
    """
    重新生成执行策略
    
    Returns:
        更新后的执行策略
    """
    policy = get_execution_policy(force_reload=True)
    
    return {
        "policy": policy.to_dict()
    }


@router.post("/policy/degrade")
def degrade_policy(reason: str = "手动降级") -> Dict[str, Any]:
    """
    手动触发策略降级
    
    Args:
        reason: 降级原因
    
    Returns:
        降级后的执行策略
    """
    policy = degrade_execution_policy(reason)
    
    return {
        "policy": policy.to_dict(),
        "message": f"已降级: {reason}"
    }


@router.get("/monitor")
def get_monitor_status() -> Dict[str, Any]:
    """
    获取运行时监控状态
    
    Returns:
        监控状态（包含 GPU、内存、CPU、任务统计等）
    """
    monitor = get_runtime_monitor()
    
    return monitor.get_status()


@router.get("/monitor/metrics/history")
def get_metrics_history(minutes: int = 5) -> Dict[str, Any]:
    """
    获取历史监控指标
    
    Args:
        minutes: 获取最近 N 分钟的数据
    
    Returns:
        历史监控指标
    """
    monitor = get_runtime_monitor()
    history = monitor.get_metrics_history(minutes)
    
    return {
        "minutes": minutes,
        "count": len(history),
        "metrics": [
            {
                "timestamp": m.timestamp.isoformat(),
                "gpu_vram_used_percent": round(m.gpu_vram_used_percent, 1),
                "memory_used_percent": round(m.memory_used_percent, 1),
                "cpu_percent": round(m.cpu_percent, 1),
                "resolve_busy": m.resolve_busy
            }
            for m in history
        ]
    }


@router.get("/status")
def get_runtime_status() -> Dict[str, Any]:
    """
    获取完整的运行时状态（Profile + Policy + Monitor）
    
    Returns:
        完整的运行时状态
    """
    profile = get_runtime_profile()
    policy = get_execution_policy()
    monitor = get_runtime_monitor()
    
    return {
        "profile": {
            "class": profile.profile_class,
            "degraded": profile.degraded,
            "degradation_reason": profile.degradation_reason,
            "explanation": profile.get_explanation()
        },
        "policy": policy.to_dict(),
        "monitor": monitor.get_status(),
        "recommendations": _get_recommendations(profile, policy, monitor)
    }


def _get_recommendations(profile, policy, monitor) -> list[str]:
    """生成运行建议"""
    recommendations = []
    
    # 检查 Ollama
    if not profile.ai_runtime.ollama:
        recommendations.append("建议安装 Ollama 以使用本地视觉模型（零成本）")
    elif not profile.ai_runtime.ollama_models:
        recommendations.append("建议下载 Moondream 模型: ollama pull moondream")
    
    # 检查 GPU
    if not profile.gpu or not profile.gpu.cuda:
        recommendations.append("未检测到 NVIDIA GPU，将使用 CPU 模式（速度较慢）")
    elif profile.gpu.vram_gb < 6:
        recommendations.append(f"GPU 显存较小 ({profile.gpu.vram_gb}GB)，建议使用 Moondream 轻量模型")
    
    # 检查内存
    if profile.memory.available_gb < 8:
        recommendations.append(f"可用内存较少 ({profile.memory.available_gb:.1f}GB)，建议关闭其他应用")
    
    # 检查监控状态
    current = monitor.get_current_metrics()
    if current:
        if current.gpu_vram_used_percent > 70:
            recommendations.append(f"GPU 显存使用率较高 ({current.gpu_vram_used_percent:.1f}%)，可能影响性能")
        
        if current.memory_available_gb < 4:
            recommendations.append(f"可用内存不足 ({current.memory_available_gb:.1f}GB)，建议释放内存")
    
    # 检查降级状态
    if profile.degraded:
        recommendations.append(f"⚠️  系统已降级: {profile.degradation_reason}")
    
    return recommendations
