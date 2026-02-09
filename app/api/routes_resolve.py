"""
DaVinci Resolve API - 自动导入和场景检测
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Optional, Dict, Any
import shutil
from datetime import datetime

from ..tools.resolve_importer import get_importer

router = APIRouter(prefix="/api/resolve", tags=["resolve"])

# 获取 Resolve Importer 单例
resolve_importer = get_importer()


@router.get("/status")
async def get_resolve_status():
    """
    获取 DaVinci Resolve 状态
    
    Returns:
        {
            "connected": bool,
            "project_name": str,
            "media_pool_items": int,
            "message": str
        }
    """
    try:
        status = resolve_importer.check_resolve_status()
        return JSONResponse(content=status)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "connected": False,
                "project_name": None,
                "media_pool_items": 0,
                "message": f"检查状态失败: {str(e)}"
            }
        )


@router.post("/import")
async def import_media(
    files: List[str] = Form(...),
):
    """
    导入媒体到 DaVinci Resolve Media Pool
    
    Args:
        files: 文件路径列表（JSON 字符串数组）
    
    Returns:
        {
            "success": bool,
            "imported": [...],
            "failed": [...],
            "message": str
        }
    """
    try:
        import json
        # 解析文件路径列表
        if isinstance(files, str):
            file_paths = json.loads(files)
        else:
            file_paths = files
        
        result = resolve_importer.import_media(file_paths)
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入失败: {str(e)}")


@router.post("/import-and-detect")
async def import_and_detect_scenes(
    background_tasks: BackgroundTasks,
    video_file: str = Form(...),
    timeline_name: Optional[str] = Form(None),
    framerate: float = Form(30.0)
):
    """
    自动导入视频并检测场景切点 (使用 fuscript.exe 桥接)
    
    完整工作流程:
    1. 调用 fuscript.exe 运行 resolve_bridge.py
    2. 桥接脚本导入媒体到 Media Pool
    3. 创建新时间线并添加媒体
    4. 调用 DetectSceneCuts() API
    5. 返回场景切点信息
    
    Args:
        video_file: 视频文件路径
        timeline_name: 时间线名称（可选,桥接脚本会自动生成）
        framerate: 时间线帧率（默认 30fps）
    
    Returns:
        {
            "success": bool,
            "timeline_name": str,
            "clips_count": int,
            "project_name": str,
            "message": str
        }
    """
    try:
        # 验证文件存在
        video_path = Path(video_file)
        if not video_path.exists():
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {video_file}")
        
        # 使用 fuscript.exe 桥接
        from ..tools.resolve_bridge_wrapper import get_resolve_bridge
        
        bridge = get_resolve_bridge()
        result = bridge.import_and_detect_scenes(
            video_path=str(video_path),
            framerate=framerate
        )
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自动导入和场景检测失败: {str(e)}")


@router.post("/upload-and-detect")
async def upload_and_detect(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    timeline_name: Optional[str] = Form(None),
    framerate: float = Form(30.0)
):
    """
    上传视频并自动导入到 Resolve + 场景检测
    
    这是一个完整的端点,用户可以直接上传视频文件
    
    Args:
        video: 上传的视频文件
        project_id: 项目 ID（可选,用于保存到特定项目目录）
        timeline_name: 时间线名称（可选）
        framerate: 时间线帧率（默认 30fps）
    
    Returns:
        {
            "success": bool,
            "timeline_name": str,
            "clips_count": int,
            "scene_cuts_detected": bool,
            "video_path": str,
            "message": str
        }
    """
    try:
        # 1. 确定保存路径
        if project_id:
            save_dir = Path("jobs") / project_id / "input"
        else:
            # 创建临时目录
            temp_id = f"temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            save_dir = Path("jobs") / temp_id / "input"
        
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 保存上传的视频
        video_path = save_dir / video.filename
        with video_path.open("wb") as f:
            shutil.copyfileobj(video.file, f)
        
        print(f"✓ 视频已保存: {video_path}")
        
        # 3. 调用自动导入和场景检测
        result = resolve_importer.import_and_detect_scenes(
            file_paths=[str(video_path)],
            timeline_name=timeline_name,
            framerate=framerate
        )
        
        # 4. 添加视频路径到结果
        result["video_path"] = str(video_path)
        result["project_id"] = project_id if project_id else temp_id
        
        return JSONResponse(content=result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"上传和处理失败: {str(e)}")


@router.get("/timelines")
async def get_timelines():
    """
    获取当前项目的所有时间线
    
    Returns:
        {
            "success": bool,
            "timelines": [...],
            "message": str
        }
    """
    try:
        # TODO: 实现获取时间线列表
        # 需要在 resolve_importer 中添加相应方法
        return JSONResponse(content={
            "success": False,
            "timelines": [],
            "message": "功能开发中"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间线失败: {str(e)}")


@router.get("/media-pool")
async def get_media_pool_items():
    """
    获取 Media Pool 中的所有素材
    
    Returns:
        {
            "success": bool,
            "items": [...],
            "count": int,
            "message": str
        }
    """
    try:
        items = resolve_importer.get_media_pool_items()
        
        return JSONResponse(content={
            "success": True,
            "items": [str(item) for item in items],  # 转换为字符串
            "count": len(items),
            "message": f"找到 {len(items)} 个素材"
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取素材失败: {str(e)}")
