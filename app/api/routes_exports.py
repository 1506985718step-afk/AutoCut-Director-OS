"""
产品级 API - 导出管理
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import Optional
import json
import subprocess
from datetime import datetime

router = APIRouter(prefix="/api/exports", tags=["exports"])

# 导出任务状态
export_tasks = {}


@router.post("/")
async def create_export(
    background_tasks: BackgroundTasks,
    project_id: str,
    version: Optional[int] = None,
    quality: str = "1080p"
):
    """
    创建导出任务
    
    Args:
        project_id: 项目 ID
        version: 版本号（可选，默认最新版本）
        quality: 导出质量 (1080p/4k)
    
    Returns:
        {
            "export_id": "export_xxx",
            "status": "exporting",
            "message": "正在导出..."
        }
    """
    try:
        # 1. 生成导出 ID
        export_id = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 2. 确定项目路径
        project_path = Path("jobs") / project_id
        if version:
            project_path = Path("jobs") / f"{project_id}_v{version}"
        
        if not project_path.exists():
            raise HTTPException(status_code=404, detail="项目不存在")
        
        # 3. 检查输出文件
        output_path = project_path / "output" / "final.mp4"
        if not output_path.exists():
            raise HTTPException(status_code=404, detail="输出文件不存在，请先完成剪辑")
        
        # 4. 创建导出任务
        export_tasks[export_id] = {
            "export_id": export_id,
            "project_id": project_id,
            "version": version,
            "quality": quality,
            "status": "exporting",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "source_path": str(output_path),
            "output_path": None
        }
        
        # 5. 启动后台导出
        background_tasks.add_task(
            export_video,
            export_id,
            str(output_path),
            quality
        )
        
        return JSONResponse(content={
            "export_id": export_id,
            "status": "exporting",
            "message": "正在导出..."
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建导出任务失败: {str(e)}")


async def export_video(export_id: str, source_path: str, quality: str):
    """
    后台导出视频
    
    Args:
        export_id: 导出 ID
        source_path: 源视频路径
        quality: 导出质量
    """
    try:
        # 更新状态
        export_tasks[export_id]["status"] = "exporting"
        export_tasks[export_id]["progress"] = 10
        
        # 确定输出路径
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        
        output_filename = f"{export_id}_{quality}.mp4"
        output_path = exports_dir / output_filename
        
        # 根据质量设置参数
        if quality == "4k":
            # 4K 导出
            export_tasks[export_id]["progress"] = 30
            cmd = [
                "ffmpeg",
                "-i", source_path,
                "-vf", "scale=3840:2160",
                "-c:v", "libx264",
                "-preset", "slow",
                "-crf", "18",
                "-c:a", "aac",
                "-b:a", "192k",
                "-movflags", "+faststart",
                "-y",
                str(output_path)
            ]
        else:
            # 1080p 导出（默认）
            export_tasks[export_id]["progress"] = 30
            # 如果源文件已经是 1080p，直接复制
            import shutil
            shutil.copy(source_path, output_path)
            export_tasks[export_id]["progress"] = 90
        
        # 执行 ffmpeg（如果需要）
        if quality == "4k":
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"导出失败: {process.stderr}")
            
            export_tasks[export_id]["progress"] = 90
        
        # 完成
        export_tasks[export_id]["status"] = "completed"
        export_tasks[export_id]["progress"] = 100
        export_tasks[export_id]["output_path"] = str(output_path)
        export_tasks[export_id]["download_url"] = f"/api/exports/{export_id}/download"
        
    except Exception as e:
        export_tasks[export_id]["status"] = "error"
        export_tasks[export_id]["error"] = str(e)


@router.get("/{export_id}/status")
async def get_export_status(export_id: str):
    """
    获取导出状态
    
    Args:
        export_id: 导出 ID
    
    Returns:
        导出状态信息
    """
    if export_id not in export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    
    return JSONResponse(content=export_tasks[export_id])


@router.get("/{export_id}/download")
async def download_export(export_id: str):
    """
    下载导出的视频
    
    Args:
        export_id: 导出 ID
    
    Returns:
        视频文件流
    """
    if export_id not in export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    
    task = export_tasks[export_id]
    
    if task["status"] != "completed":
        raise HTTPException(status_code=400, detail="导出尚未完成")
    
    output_path = Path(task["output_path"])
    
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="导出文件不存在")
    
    return FileResponse(
        output_path,
        media_type="video/mp4",
        filename=f"autocut_{export_id}.mp4"
    )


@router.delete("/{export_id}")
async def delete_export(export_id: str):
    """
    删除导出任务和文件
    
    Args:
        export_id: 导出 ID
    
    Returns:
        删除结果
    """
    if export_id not in export_tasks:
        raise HTTPException(status_code=404, detail="导出任务不存在")
    
    task = export_tasks[export_id]
    
    # 删除文件
    if task.get("output_path"):
        output_path = Path(task["output_path"])
        if output_path.exists():
            output_path.unlink()
    
    # 删除任务
    del export_tasks[export_id]
    
    return JSONResponse(content={
        "export_id": export_id,
        "message": "导出已删除"
    })
