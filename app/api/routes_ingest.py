"""
Ingest API 路由 - 素材预处理接口
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from pathlib import Path
import shutil
from datetime import datetime
from typing import Optional

from ..tools.media_ingest import MediaIngest
from ..core.job_store import JobStore

router = APIRouter(prefix="/api/ingest", tags=["ingest"])

# 初始化
ingest_manager = MediaIngest(job_dir="jobs")
job_store = JobStore()


@router.post("/upload")
async def upload_video(
    video: UploadFile = File(...),
    job_id: Optional[str] = Form(None)
):
    """
    上传视频文件并创建 job
    
    Args:
        video: 视频文件
        job_id: job 标识（可选，自动生成）
    
    Returns:
        {
            "job_id": "...",
            "job_path": "...",
            "video_path": "...",
            "message": "..."
        }
    """
    # 生成 job_id
    if not job_id:
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # 创建 job 目录
    job_path = ingest_manager.create_job(job_id)
    
    # 保存视频文件
    video_path = job_path / "input" / video.filename
    
    try:
        with video_path.open("wb") as f:
            shutil.copyfileobj(video.file, f)
        
        # 记录 job
        job_store.create_job(job_id, {
            "video_path": str(video_path),
            "status": "uploaded"
        })
        
        return {
            "job_id": job_id,
            "job_path": str(job_path),
            "video_path": str(video_path),
            "message": "视频上传成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/extract-audio")
async def extract_audio(
    job_id: str = Form(...),
    format: str = Form("wav"),
    sample_rate: int = Form(16000)
):
    """
    从视频提取音频
    
    Args:
        job_id: job 标识
        format: 音频格式（wav/mp3）
        sample_rate: 采样率
    
    Returns:
        {
            "job_id": "...",
            "audio_path": "...",
            "message": "..."
        }
    """
    # 获取 job 信息
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    video_path = job_data.get("video_path")
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 提取音频
    job_path = Path("jobs") / job_id
    audio_path = job_path / "temp" / f"{Path(video_path).stem}.{format}"
    
    try:
        audio_output = ingest_manager.extract_audio(
            video_path,
            str(audio_path),
            format=format,
            sample_rate=sample_rate
        )
        
        # 更新 job
        job_store.update_job(job_id, {
            "audio_path": audio_output,
            "status": "audio_extracted"
        })
        
        return {
            "job_id": job_id,
            "audio_path": audio_output,
            "message": "音频提取成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音频提取失败: {str(e)}")


@router.post("/scene-detection-info")
async def get_scene_detection_info(job_id: str = Form(...)):
    """
    获取场景切点检测指引
    
    Args:
        job_id: job 标识
    
    Returns:
        场景切点检测指引信息
    """
    # 获取 job 信息
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    video_path = job_data.get("video_path")
    if not video_path:
        raise HTTPException(status_code=404, detail="视频文件不存在")
    
    # 生成指引
    info = ingest_manager.prompt_scene_detection(video_path)
    
    return {
        "job_id": job_id,
        "scene_detection_info": info,
        "edl_save_path": str(Path("jobs") / job_id / "input"),
        "message": "请在 DaVinci Resolve 中完成场景切点检测"
    }


@router.post("/upload-edl")
async def upload_edl(
    job_id: str = Form(...),
    edl_file: UploadFile = File(...)
):
    """
    上传 EDL/XML 文件
    
    Args:
        job_id: job 标识
        edl_file: EDL 或 XML 文件
    
    Returns:
        {
            "job_id": "...",
            "edl_path": "...",
            "message": "..."
        }
    """
    # 获取 job 信息
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    # 保存 EDL 文件
    job_path = Path("jobs") / job_id
    edl_path = job_path / "input" / edl_file.filename
    
    try:
        with edl_path.open("wb") as f:
            shutil.copyfileobj(edl_file.file, f)
        
        # 更新 job
        job_store.update_job(job_id, {
            "edl_path": str(edl_path),
            "status": "edl_uploaded"
        })
        
        return {
            "job_id": job_id,
            "edl_path": str(edl_path),
            "message": "EDL 文件上传成功"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/")
async def ingest_complete(
    video: UploadFile = File(...),
    job_id: Optional[str] = Form(None),
    extract_audio: bool = Form(True)
):
    """
    完整的 Ingest 流程（一步到位）
    
    Args:
        video: 视频文件
        job_id: job 标识（可选）
        extract_audio: 是否提取音频
    
    Returns:
        {
            "job_id": "...",
            "job_path": "...",
            "video_path": "...",
            "audio_path": "..." (可选),
            "scene_detection_info": {...},
            "message": "..."
        }
    """
    # 1. 上传视频
    upload_result = await upload_video(video, job_id)
    job_id = upload_result["job_id"]
    
    result = {
        "job_id": job_id,
        "job_path": upload_result["job_path"],
        "video_path": upload_result["video_path"]
    }
    
    # 2. 提取音频
    if extract_audio:
        try:
            audio_result = await extract_audio(job_id)
            result["audio_path"] = audio_result["audio_path"]
        except Exception as e:
            result["audio_path"] = None
            result["audio_error"] = str(e)
    
    # 3. 场景切点检测指引
    try:
        scene_info = await get_scene_detection_info(job_id)
        result["scene_detection_info"] = scene_info["scene_detection_info"]
        result["edl_save_path"] = scene_info["edl_save_path"]
    except Exception as e:
        result["scene_detection_error"] = str(e)
    
    result["message"] = "Ingest 完成，请在 Resolve 中完成场景切点检测并上传 EDL"
    
    return result


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """
    获取 job 状态
    
    Args:
        job_id: job 标识
    
    Returns:
        job 详细信息
    """
    job_data = job_store.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job 不存在: {job_id}")
    
    return {
        "job_id": job_id,
        "job_data": job_data
    }
