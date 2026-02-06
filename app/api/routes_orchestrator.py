"""
Orchestrator API 路由 - 系统状态和资源管理
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional

from ..core.orchestrator import get_orchestrator, JobState
from ..core.job_store import JobStore

router = APIRouter(prefix="/api/orchestrator", tags=["orchestrator"])
job_store = JobStore()


@router.get("/status")
async def get_system_status():
    """
    获取系统状态
    
    Returns:
        {
            "resource_locks": {...},
            "active_jobs": {...},
            "system": {...}
        }
    """
    orchestrator = get_orchestrator()
    status = orchestrator.get_system_status()
    
    return JSONResponse(content={
        "success": True,
        "status": status
    })


@router.post("/jobs/{job_id}/transition")
async def transition_job_state(
    job_id: str,
    target_state: str,
    force: bool = False
):
    """
    转换 Job 状态
    
    Args:
        job_id: 任务 ID
        target_state: 目标状态
        force: 是否强制转换
    
    Returns:
        {
            "success": true,
            "message": "已转换到 analyzing"
        }
    """
    try:
        # 验证状态
        try:
            state = JobState(target_state)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"无效的状态: {target_state}"
            )
        
        # 转换状态
        success, message = job_store.transition_state(job_id, state, force=force)
        
        if not success:
            raise HTTPException(status_code=400, detail=message)
        
        return JSONResponse(content={
            "success": True,
            "message": message
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/jobs/{job_id}/state")
async def get_job_state(job_id: str):
    """
    获取 Job 状态
    
    Returns:
        {
            "job_id": "job_xxx",
            "current_state": "analyzing",
            "state_history": [...]
        }
    """
    job = job_store.get_job(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return JSONResponse(content={
        "success": True,
        "job_id": job_id,
        "current_state": job.get("state", "unknown"),
        "state_history": job.get("state_history", [])
    })


@router.post("/resource-locks/release")
async def release_resource_locks(resource: Optional[str] = None):
    """
    释放资源锁（紧急用）
    
    Args:
        resource: 资源名称（可选，不指定则释放所有）
    
    Returns:
        {
            "success": true,
            "released": ["GPU_HEAVY", "RESOLVE_BUSY"]
        }
    """
    orchestrator = get_orchestrator()
    
    if resource:
        orchestrator.resource_lock.release(resource)
        released = [resource]
    else:
        # 释放所有锁
        for res in ["GPU_HEAVY", "RESOLVE_BUSY"]:
            orchestrator.resource_lock.release(res)
        
        # 重新启用 Vision 和 AI
        orchestrator.resource_lock.acquire("VISION_ALLOWED")
        orchestrator.resource_lock.acquire("AI_ALLOWED")
        
        released = ["GPU_HEAVY", "RESOLVE_BUSY"]
    
    return JSONResponse(content={
        "success": True,
        "released": released,
        "current_status": orchestrator.resource_lock.get_status()
    })


@router.get("/health")
async def health_check():
    """
    健康检查
    
    Returns:
        {
            "healthy": true,
            "issues": []
        }
    """
    orchestrator = get_orchestrator()
    status = orchestrator.get_system_status()
    
    issues = []
    
    # 检查 CPU 使用率
    if status["system"]["cpu_percent"] > 90:
        issues.append("CPU 使用率过高")
    
    # 检查内存使用率
    if status["system"]["memory_percent"] > 85:
        issues.append("内存使用率过高")
    
    # 检查资源锁死锁
    locks = status["resource_locks"]
    if locks["GPU_HEAVY"] and locks["VISION_ALLOWED"]:
        issues.append("资源锁冲突：GPU_HEAVY 和 VISION_ALLOWED 同时为 True")
    
    return JSONResponse(content={
        "healthy": len(issues) == 0,
        "issues": issues,
        "status": status
    })
