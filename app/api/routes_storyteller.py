"""
视觉叙事 API - 无脚本模式
从视觉素材自动构思故事
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import shutil
from typing import Optional

from ..config import settings
from ..core.visual_storyteller import VisualStoryteller
from ..models.schemas import ScenesJSON

router = APIRouter(prefix="/api/storyteller", tags=["storyteller"])


@router.post("/create-story")
async def create_story(
    scenes_file: UploadFile = File(...),
    duration_target: int = Form(30),
    style_preference: Optional[str] = Form(None)
):
    """
    从视觉素材创作故事（无脚本模式）
    
    Args:
        scenes_file: scenes.json 文件（必须包含 visual 字段）
        duration_target: 目标时长（秒）
        style_preference: 风格偏好（可选，如 "高燃踩点"、"情感叙事"）
    
    Returns:
        {
            "success": true,
            "theme": "海边度假Vlog",
            "logic": "按时间顺序，从出发到日落",
            "narrative_style": "舒缓治愈",
            "generated_transcript": {...},
            "suggested_bgm_mood": "chill_hop",
            "clustering": {...},
            "alternative_themes": [...]
        }
    """
    try:
        # 1. 保存上传的文件
        temp_dir = settings.UPLOADS_DIR / "temp_storyteller"
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        scenes_path = temp_dir / scenes_file.filename
        
        with open(scenes_path, "wb") as f:
            shutil.copyfileobj(scenes_file.file, f)
        
        # 2. 加载 scenes.json
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        
        # 3. 检查视觉数据
        visual_count = sum(1 for scene in scenes_data.scenes if scene.visual)
        
        if visual_count == 0:
            raise HTTPException(
                status_code=400,
                detail="场景数据中没有视觉信息，请先运行视觉分析"
            )
        
        # 4. 初始化 Visual Storyteller
        storyteller = VisualStoryteller()
        
        # 5. 生成故事
        story_result = storyteller.generate_story_from_visuals(
            scenes_data,
            duration_target=duration_target,
            style_preference=style_preference
        )
        
        # 6. 清理临时文件
        try:
            scenes_path.unlink()
        except:
            pass
        
        # 7. 转换 TranscriptJSON 为字典
        response_data = {
            "success": True,
            "theme": story_result['theme'],
            "logic": story_result['logic'],
            "narrative_style": story_result['narrative_style'],
            "generated_transcript": story_result['generated_transcript'].model_dump(),
            "suggested_bgm_mood": story_result['suggested_bgm_mood'],
            "clustering": story_result['clustering'],
            "alternative_themes": story_result.get('alternative_themes', []),
            "message": f"成功生成故事：{story_result['theme']}"
        }
        
        return JSONResponse(content=response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"故事生成失败: {str(e)}")


@router.post("/create-story-from-job")
async def create_story_from_job(
    job_id: str = Form(...),
    duration_target: int = Form(30),
    style_preference: Optional[str] = Form(None)
):
    """
    为已有任务创作故事（无脚本模式）
    
    Args:
        job_id: 任务 ID
        duration_target: 目标时长（秒）
        style_preference: 风格偏好（可选）
    
    Returns:
        {
            "success": true,
            "job_id": "job_xxx",
            "story_path": "jobs/job_xxx/story_result.json",
            "transcript_path": "jobs/job_xxx/transcript_generated.json",
            ...
        }
    """
    try:
        # 1. 检查任务目录
        job_dir = settings.JOBS_DIR / job_id
        
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
        
        # 2. 查找 scenes_with_visual.json
        scenes_path = job_dir / "scenes_with_visual.json"
        
        if not scenes_path.exists():
            # 尝试使用普通 scenes.json
            scenes_path = job_dir / "scenes.json"
            if not scenes_path.exists():
                raise HTTPException(status_code=404, detail="scenes.json 不存在")
        
        # 3. 加载场景数据
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        
        # 4. 检查视觉数据
        visual_count = sum(1 for scene in scenes_data.scenes if scene.visual)
        
        if visual_count == 0:
            raise HTTPException(
                status_code=400,
                detail="场景数据中没有视觉信息，请先运行视觉分析"
            )
        
        # 5. 生成故事
        storyteller = VisualStoryteller()
        story_result = storyteller.generate_story_from_visuals(
            scenes_data,
            duration_target=duration_target,
            style_preference=style_preference
        )
        
        # 6. 保存结果
        story_path = job_dir / "story_result.json"
        story_output = {
            "theme": story_result['theme'],
            "logic": story_result['logic'],
            "narrative_style": story_result['narrative_style'],
            "suggested_bgm_mood": story_result['suggested_bgm_mood'],
            "clustering": story_result['clustering'],
            "alternative_themes": story_result.get('alternative_themes', []),
            "generated_transcript": story_result['generated_transcript'].model_dump()
        }
        
        with open(story_path, 'w', encoding='utf-8') as f:
            json.dump(story_output, f, indent=2, ensure_ascii=False)
        
        # 7. 保存 transcript.json
        transcript_path = job_dir / "transcript_generated.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(
                story_result['generated_transcript'].model_dump(),
                f,
                indent=2,
                ensure_ascii=False
            )
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            "story_path": str(story_path),
            "transcript_path": str(transcript_path),
            "theme": story_result['theme'],
            "narrative_style": story_result['narrative_style'],
            "message": f"成功生成故事：{story_result['theme']}"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"故事生成失败: {str(e)}")


@router.post("/generate-dsl-from-story")
async def generate_dsl_from_story(
    job_id: str = Form(...),
    platform: str = Form("douyin")
):
    """
    从故事生成 editing_dsl.json
    
    Args:
        job_id: 任务 ID
        platform: 目标平台（douyin/bilibili/youtube）
    
    Returns:
        {
            "success": true,
            "job_id": "job_xxx",
            "dsl_path": "jobs/job_xxx/editing_dsl_from_story.json",
            ...
        }
    """
    try:
        # 1. 检查任务目录
        job_dir = settings.JOBS_DIR / job_id
        
        if not job_dir.exists():
            raise HTTPException(status_code=404, detail=f"任务不存在: {job_id}")
        
        # 2. 加载故事结果
        story_path = job_dir / "story_result.json"
        
        if not story_path.exists():
            raise HTTPException(status_code=404, detail="story_result.json 不存在，请先生成故事")
        
        with open(story_path, 'r', encoding='utf-8') as f:
            story_result = json.load(f)
        
        # 3. 加载场景数据
        scenes_path = job_dir / "scenes_with_visual.json"
        if not scenes_path.exists():
            scenes_path = job_dir / "scenes.json"
        
        with open(scenes_path, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        
        # 4. 重建 TranscriptJSON
        from ..models.schemas import TranscriptJSON
        story_result['generated_transcript'] = TranscriptJSON(
            **story_result['generated_transcript']
        )
        
        # 5. 生成 DSL
        storyteller = VisualStoryteller()
        dsl = storyteller.generate_dsl_from_story(
            scenes_data,
            story_result,
            platform=platform
        )
        
        # 6. 保存 DSL
        dsl_path = job_dir / "editing_dsl_from_story.json"
        with open(dsl_path, 'w', encoding='utf-8') as f:
            json.dump(dsl, f, indent=2, ensure_ascii=False)
        
        # 7. DSL 摘要
        timeline = dsl.get('editing_plan', {}).get('timeline', [])
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            "dsl_path": str(dsl_path),
            "timeline_items": len(timeline),
            "platform": platform,
            "message": f"成功生成 DSL（{len(timeline)} 个片段）"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DSL 生成失败: {str(e)}")


@router.get("/story/{job_id}")
async def get_story(job_id: str):
    """
    获取任务的故事结果
    
    Args:
        job_id: 任务 ID
    
    Returns:
        故事结果
    """
    try:
        job_dir = settings.JOBS_DIR / job_id
        story_path = job_dir / "story_result.json"
        
        if not story_path.exists():
            raise HTTPException(status_code=404, detail="故事结果不存在")
        
        with open(story_path, 'r', encoding='utf-8') as f:
            story_result = json.load(f)
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            **story_result
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取故事失败: {str(e)}")
