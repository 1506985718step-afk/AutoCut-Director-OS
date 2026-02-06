"""
Job 管理 API 路由
"""
from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, StreamingResponse
from pathlib import Path
import subprocess
from typing import Optional

from ..core.job_store import JobStore

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

# 初始化
job_store = JobStore()


@router.get("/{job_id}")
async def get_job_status(job_id: str):
    """
    获取 job 状态 + artifacts 列表 + 最近 trace 摘要
    
    Args:
        job_id: job 标识
    
    Returns:
        {
            "job_id": "...",
            "status": "...",
            "progress": 0-100,
            "created_at": "...",
            "updated_at": "...",
            "artifacts": {
                "input": [...],
                "temp": [...],
                "output": [...]
            },
            "trace_summary": {
                "total_actions": 10,
                "successful": 9,
                "failed": 1,
                "total_time_ms": 5432
            }
        }
    """
    # 获取基本信息
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 获取 artifacts
    artifacts = job_store.get_job_artifacts(job_id)
    
    # 获取 trace 摘要
    trace = job_store.get_job_trace(job_id)
    trace_summary = None
    
    if trace:
        trace_summary = {
            "total_actions": trace.get("total_actions", 0),
            "successful": trace.get("successful", 0),
            "failed": trace.get("failed", 0),
            "total_time_ms": trace.get("total_time_ms", 0)
        }
    
    return {
        "job_id": job_id,
        "status": job_data.get("status"),
        "progress": job_data.get("progress", 0),
        "created_at": job_data.get("created_at"),
        "updated_at": job_data.get("updated_at"),
        "error": job_data.get("error"),
        "artifacts": artifacts,
        "trace_summary": trace_summary
    }


@router.get("/{job_id}/artifacts")
async def get_job_artifacts(job_id: str):
    """
    获取 job 的所有产物文件列表
    
    Args:
        job_id: job 标识
    
    Returns:
        {
            "input": [...],
            "temp": [...],
            "output": [...]
        }
    """
    # 检查 job 是否存在
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 获取 artifacts
    artifacts = job_store.get_job_artifacts(job_id)
    
    return artifacts


@router.get("/{job_id}/trace")
async def get_job_trace(job_id: str):
    """
    获取 job 的完整执行 trace
    
    Args:
        job_id: job 标识
    
    Returns:
        {
            "total_actions": 10,
            "successful": 9,
            "failed": 1,
            "total_time_ms": 5432,
            "actions": [...]
        }
    """
    # 检查 job 是否存在
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 获取 trace
    trace = job_store.get_job_trace(job_id)
    
    if not trace:
        raise HTTPException(status_code=404, detail=f"Trace 不存在: {job_id}")
    
    return trace


@router.get("/{job_id}/preview")
async def get_job_preview(
    job_id: str,
    quality: Optional[str] = "480p"
):
    """
    获取 job 的低码率预览视频（480p）
    
    Args:
        job_id: job 标识
        quality: 预览质量（480p/720p）
    
    Returns:
        视频文件流
    """
    # 检查 job 是否存在
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 查找输出视频
    job_dir = Path("jobs") / job_id
    output_dir = job_dir / "output"
    
    # 查找 final.mp4 或其他视频文件
    video_files = list(output_dir.glob("*.mp4"))
    
    if not video_files:
        raise HTTPException(status_code=404, detail="未找到输出视频")
    
    original_video = video_files[0]
    
    # 生成预览文件路径
    preview_dir = job_dir / "temp"
    preview_dir.mkdir(exist_ok=True)
    
    preview_file = preview_dir / f"preview_{quality}.mp4"
    
    # 如果预览文件已存在，直接返回
    if preview_file.exists():
        return FileResponse(
            preview_file,
            media_type="video/mp4",
            filename=f"preview_{quality}.mp4"
        )
    
    # 生成预览视频（使用 ffmpeg）
    try:
        await generate_preview(
            str(original_video),
            str(preview_file),
            quality
        )
        
        return FileResponse(
            preview_file,
            media_type="video/mp4",
            filename=f"preview_{quality}.mp4"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"生成预览失败: {str(e)}"
        )


@router.get("/{job_id}/download/{category}/{filename}")
async def download_artifact(
    job_id: str,
    category: str,
    filename: str
):
    """
    下载 job 的产物文件
    
    Args:
        job_id: job 标识
        category: 文件类别（input/temp/output）
        filename: 文件名
    
    Returns:
        文件流
    """
    # 检查 job 是否存在
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 检查类别
    if category not in ["input", "temp", "output"]:
        raise HTTPException(status_code=400, detail="无效的类别")
    
    # 构建文件路径
    file_path = Path("jobs") / job_id / category / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    # 返回文件
    return FileResponse(
        file_path,
        filename=filename
    )


async def generate_preview(
    input_path: str,
    output_path: str,
    quality: str = "480p"
):
    """
    使用 ffmpeg 生成低码率预览视频
    
    Args:
        input_path: 输入视频路径
        output_path: 输出预览路径
        quality: 预览质量（480p/720p）
    """
    # 根据质量设置分辨率和码率
    quality_settings = {
        "480p": {
            "scale": "scale=-2:480",
            "bitrate": "500k"
        },
        "720p": {
            "scale": "scale=-2:720",
            "bitrate": "1000k"
        }
    }
    
    settings = quality_settings.get(quality, quality_settings["480p"])
    
    # 构建 ffmpeg 命令
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", settings["scale"],
        "-b:v", settings["bitrate"],
        "-c:v", "libx264",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",  # 优化流式播放
        "-y",
        output_path
    ]
    
    # 执行 ffmpeg
    process = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    if process.returncode != 0:
        raise RuntimeError(f"ffmpeg 执行失败: {process.stderr}")
    
    return output_path


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """
    删除 job 及其所有文件
    
    Args:
        job_id: job 标识
    
    Returns:
        删除结果
    """
    # 检查 job 是否存在
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 删除 job
    try:
        job_store.delete_job(job_id)
        return {
            "job_id": job_id,
            "message": "Job 已删除"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


@router.get("/")
async def list_jobs(limit: int = 50):
    """
    列出所有 jobs
    
    Args:
        limit: 返回数量限制
    
    Returns:
        jobs 列表
    """
    jobs = job_store.list_jobs(limit=limit)
    
    return {
        "total": len(jobs),
        "jobs": jobs
    }
