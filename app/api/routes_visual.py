"""
视觉分析路由 - 为场景添加视觉元数据

支持本地模型（Ollama）和云端模型（OpenAI）
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import shutil
from typing import Optional

from ..config import settings
from ..tools.visual_analyzer_factory import analyze_scenes_auto
from ..models.schemas import ScenesJSON

router = APIRouter(prefix="/api/visual", tags=["visual"])


@router.post("/analyze")
async def analyze_visual(
    scenes_file: UploadFile = File(...),
    video_file: UploadFile = File(...),
    max_scenes: Optional[int] = Form(None),
    use_local: Optional[bool] = Form(None),
    model: Optional[str] = Form(None)
):
    """
    为场景数据添加视觉分析
    
    Args:
        scenes_file: scenes.json 文件
        video_file: 视频文件
        max_scenes: 限制分析数量（可选，用于测试）
        use_local: 是否使用本地模型（可选，默认根据配置）
        model: 指定模型（可选：moondream/llava-phi3/gpt-4o）
    
    Returns:
        {
            "success": true,
            "model_used": "moondream",
            "scenes_with_visual": {...},
            "stats": {
                "total_scenes": 10,
                "analyzed_scenes": 10,
                "avg_quality": 8.2
            }
        }
    """
    try:
        # 1. 保存上传的文件
        temp_dir = settings.UPLOADS_DIR / "temp_visual"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        scenes_path = temp_dir / scenes_file.filename
        video_path = temp_dir / video_file.filename
        with open(scenes_path, "wb") as f:
            shutil.copyfileobj(scenes_file.file, f)
        
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video_file.file, f)
        
        # 2. 加载 scenes.json
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        
        # 3. 使用工厂方法自动选择分析器
        force_local = use_local if use_local is not None else None
        force_cloud = (not use_local) if use_local is not None else None
        
        updated_scenes = analyze_scenes_auto(
            scenes_data,
            str(video_path),
            max_scenes=max_scenes,
            force_local=force_local,
            force_cloud=force_cloud,
            model=model
        )
        
        # 4. 确定使用的模型
        model_used = model or (settings.LOCAL_VISION_MODEL if settings.USE_LOCAL_VISION else "gpt-4o")
        
        # 5. 计算统计信息
        total_scenes = len(updated_scenes.scenes)
        analyzed_scenes = sum(1 for scene in updated_scenes.scenes if scene.visual)
        
        quality_scores = [
            scene.visual.quality_score
            for scene in updated_scenes.scenes
            if scene.visual
        ]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        stats = {
            "total_scenes": total_scenes,
            "analyzed_scenes": analyzed_scenes,
            "avg_quality": round(avg_quality, 1),
            "quality_distribution": {
                "high (8-10)": sum(1 for q in quality_scores if q >= 8),
                "medium (5-7)": sum(1 for q in quality_scores if 5 <= q < 8),
                "low (1-4)": sum(1 for q in quality_scores if q < 5)
            }
        }
        
        # 6. 清理临时文件
        try:
            scenes_path.unlink()
            video_path.unlink()
        except:
            pass
        
        return JSONResponse(content={
            "success": True,
            "model_used": model_used,
            "scenes_with_visual": updated_scenes.model_dump(),
            "stats": stats,
            "message": f"成功分析 {analyzed_scenes}/{total_scenes} 个场景（使用 {model_used}）"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视觉分析失败: {str(e)}")


@router.post("/analyze-from-job")
async def analyze_visual_from_job(
    job_id: str = Form(...),
    max_scenes: Optional[int] = Form(None)
):
    """
    为已有任务的场景数据添加视觉分析
    
    Args:
        job_id: 任务 ID
        max_scenes: 限制分析数量（可选）
    
    Returns:
        {
            "success": true,
            "job_id": "job_xxx",
            "scenes_path": "jobs/job_xxx/scenes_with_visual.json",
            "stats": {...}
        }
    """
    try:
        # 1. 检查任务目录
        job_dir = settings.JOBS_DIR / job_id
        
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
        
        # 2. 查找 scenes.json 和视频文件
        scenes_path = job_dir / "scenes.json"
        if not scenes_path.exists():
            raise HTTPException(status_code=404, detail="scenes.json 不存在")
        
        # 查找视频文件
        video_path = None
        for ext in ['.mp4', '.mov', '.avi']:
            for path in job_dir.rglob(f"*{ext}"):
                video_path = path
                break
            if video_path:
                break
        
        if not video_path:
            raise HTTPException(status_code=404, detail="视频文件不存在")
        
        # 3. 加载 scenes.json
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        
        # 4. 分析视觉
        analyzer = VisualAnalyzer()
        updated_scenes = analyzer.analyze_scene_visuals(
            scenes_data,
            str(video_path),
            max_scenes=max_scenes
        )
        
        # 5. 保存结果
        output_path = job_dir / "scenes_with_visual.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_scenes.model_dump(), f, indent=2, ensure_ascii=False)
        
        # 6. 计算统计信息
        total_scenes = len(updated_scenes.scenes)
        analyzed_scenes = sum(1 for scene in updated_scenes.scenes if scene.visual)
        
        quality_scores = [
            scene.visual.quality_score
            for scene in updated_scenes.scenes
            if scene.visual
        ]
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        stats = {
            "total_scenes": total_scenes,
            "analyzed_scenes": analyzed_scenes,
            "avg_quality": round(avg_quality, 1)
        }
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            "scenes_path": str(output_path),
            "stats": stats,
            "message": f"成功分析 {analyzed_scenes}/{total_scenes} 个场景"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视觉分析失败: {str(e)}")


@router.get("/stats/{job_id}")
async def get_visual_stats(job_id: str):
    """
    获取任务的视觉分析统计信息
    
    Args:
        job_id: 任务 ID
    
    Returns:
        视觉分析统计信息
    """
    try:
        # 查找 scenes_with_visual.json
        job_dir = settings.JOBS_DIR / job_id
        scenes_path = job_dir / "scenes_with_visual.json"
        
        if not scenes_path.exists():
            raise HTTPException(status_code=404, detail="视觉分析结果不存在")
        
        # 加载数据
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        
        # 统计信息
        total_scenes = len(scenes_data.scenes)
        analyzed_scenes = sum(1 for scene in scenes_data.scenes if scene.visual)
        
        # 景别分布
        shot_types = {}
        moods = {}
        quality_scores = []
        subjects_count = {}
        
        for scene in scenes_data.scenes:
            if scene.visual:
                # 景别
                shot_type = scene.visual.shot_type
                shot_types[shot_type] = shot_types.get(shot_type, 0) + 1
                
                # 情绪
                mood = scene.visual.mood
                if mood:
                    moods[mood] = moods.get(mood, 0) + 1
                
                # 质量
                quality_scores.append(scene.visual.quality_score)
                
                # 主体
                for subject in scene.visual.subjects:
                    subjects_count[subject] = subjects_count.get(subject, 0) + 1
        
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        return JSONResponse(content={
            "job_id": job_id,
            "total_scenes": total_scenes,
            "analyzed_scenes": analyzed_scenes,
            "avg_quality": round(avg_quality, 1),
            "shot_types": shot_types,
            "moods": moods,
            "top_subjects": dict(sorted(subjects_count.items(), key=lambda x: x[1], reverse=True)[:10]),
            "quality_distribution": {
                "high (8-10)": sum(1 for q in quality_scores if q >= 8),
                "medium (5-7)": sum(1 for q in quality_scores if 5 <= q < 8),
                "low (1-4)": sum(1 for q in quality_scores if q < 5)
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")
