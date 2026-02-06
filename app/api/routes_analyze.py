"""分析路由 - 处理素材分析请求"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import shutil
from typing import Optional

from ..config import settings
from ..core.job_store import JobStore
from ..tools.asr_whisper import transcribe_audio
from ..tools.scene_from_edl import parse_edl_to_scenes
from ..tools.scene_from_xml import parse_xml_to_scenes

router = APIRouter()
job_store = JobStore()


@router.post("/story")
async def analyze_story(
    video_file: UploadFile = File(...),
    duration_target: int = Form(30),
    style_preference: Optional[str] = Form(None),
    platform: str = Form("douyin")
):
    """
    全自动导演模式（B模式）：扔进视频，吐出故事
    
    完整流程：
    1. 视频上传 → 场景检测
    2. VisualAnalyzer → 打标签
    3. VisualStoryteller → 构思故事
    4. LLMDirector → 生成 DSL
    5. 返回完整剪辑方案
    
    Args:
        video_file: 视频文件
        duration_target: 目标时长（秒）
        style_preference: 风格偏好（可选）
        platform: 目标平台
    
    Returns:
        {
            "success": true,
            "job_id": "job_xxx",
            "story": {...},
            "dsl": {...},
            "message": "全自动分析完成"
        }
    """
    try:
        from ..tools.visual_analyzer_factory import analyze_scenes_auto
        from ..core.visual_storyteller import VisualStoryteller
        from ..core.llm_engine import LLMDirector
        from ..tools.scene_from_edl import detect_scenes_from_video
        
        print("\n🎬 全自动导演模式启动...")
        
        # 1. 创建任务
        job_id = job_store.create_job()
        job_dir = settings.JOBS_DIR / job_id
        
        # 2. 保存视频
        video_path = job_dir / video_file.filename
        with open(video_path, "wb") as f:
            shutil.copyfileobj(video_file.file, f)
        
        print(f"  ✓ 视频已保存: {video_path}")
        
        # 3. 场景检测（简化版：使用固定 FPS）
        print("\n[1/5] 场景检测...")
        # TODO: 实现真正的场景检测
        # 暂时使用模拟数据
        from ..models.schemas import ScenesJSON, ScenesMeta, ScenesMedia, Scene
        
        # 获取视频信息
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=duration,r_frame_rate",
             "-of", "json", str(video_path)],
            capture_output=True,
            text=True
        )
        
        video_info = json.loads(result.stdout)
        duration = float(video_info["streams"][0]["duration"])
        fps_str = video_info["streams"][0]["r_frame_rate"]
        fps = eval(fps_str)  # "30/1" -> 30.0
        
        # 简单分段：每 5 秒一个场景
        scenes = []
        segment_duration = 5.0
        num_segments = int(duration / segment_duration)
        
        for i in range(num_segments):
            start_sec = i * segment_duration
            end_sec = min((i + 1) * segment_duration, duration)
            start_frame = int(start_sec * fps)
            end_frame = int(end_sec * fps)
            
            scenes.append(Scene(
                scene_id=f"S{i+1:04d}",
                start_frame=start_frame,
                end_frame=end_frame,
                start_tc=f"00:00:{int(start_sec):02d}:00",
                end_tc=f"00:00:{int(end_sec):02d}:00"
            ))
        
        scenes_data = ScenesJSON(
            meta=ScenesMeta(fps=fps, source="auto_detect"),
            media=ScenesMedia(primary_clip_path=str(video_path)),
            scenes=scenes
        )
        
        print(f"  ✓ 检测到 {len(scenes)} 个场景")
        
        # 4. 视觉分析
        print("\n[2/5] 视觉分析（AI 眼睛）...")
        scenes_with_visual = analyze_scenes_auto(
            scenes_data,
            str(video_path),
            max_scenes=min(10, len(scenes))  # 限制数量以控制成本
        )
        
        # 保存 scenes_with_visual.json
        scenes_path = job_dir / "scenes_with_visual.json"
        with open(scenes_path, 'w', encoding='utf-8') as f:
            json.dump(scenes_with_visual.model_dump(), f, indent=2, ensure_ascii=False)
        
        # 5. 故事构思
        print("\n[3/5] 故事构思（AI 大脑）...")
        storyteller = VisualStoryteller()
        story_result = storyteller.generate_story_from_visuals(
            scenes_with_visual,
            duration_target=duration_target,
            style_preference=style_preference
        )
        
        # 保存故事结果
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
        
        # 6. 生成 DSL
        print("\n[4/5] 生成剪辑方案（AI 导演）...")
        dsl = storyteller.generate_dsl_from_story(
            scenes_with_visual,
            story_result,
            platform=platform
        )
        
        # 保存 DSL
        dsl_path = job_dir / "editing_dsl.json"
        with open(dsl_path, 'w', encoding='utf-8') as f:
            json.dump(dsl, f, indent=2, ensure_ascii=False)
        
        print("\n[5/5] 完成！")
        print(f"  ✓ 主题: {story_result['theme']}")
        print(f"  ✓ 风格: {story_result['narrative_style']}")
        print(f"  ✓ 时间线片段: {len(dsl.get('editing_plan', {}).get('timeline', []))}")
        
        return JSONResponse(content={
            "success": True,
            "job_id": job_id,
            "story": {
                "theme": story_result['theme'],
                "logic": story_result['logic'],
                "narrative_style": story_result['narrative_style'],
                "suggested_bgm_mood": story_result['suggested_bgm_mood']
            },
            "dsl_summary": {
                "timeline_items": len(dsl.get('editing_plan', {}).get('timeline', [])),
                "platform": platform,
                "resolution": dsl.get('export', {}).get('resolution')
            },
            "paths": {
                "scenes": str(scenes_path),
                "story": str(story_path),
                "dsl": str(dsl_path)
            },
            "message": f"全自动分析完成：{story_result['theme']}"
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"全自动分析失败: {str(e)}")


@router.post("/analyze")
async def analyze(
    edl_file: Optional[UploadFile] = File(None),
    xml_file: Optional[UploadFile] = File(None),
    audio_file: Optional[UploadFile] = File(None),
    srt_file: Optional[UploadFile] = File(None)
):
    """
    分析上传的素材，生成 scenes.json 和 transcript.json
    
    Stage A (MVP): EDL -> scenes.json
    Stage A': FCPXML -> scenes.json (增强)
    Stage B: Audio -> transcript.json (Whisper ASR)
    Stage C: SRT -> transcript.json (直接导入)
    """
    # 创建新任务
    job_id = job_store.create_job()
    job_dir = settings.JOBS_DIR / job_id
    
    result = {
        "job_id": job_id,
        "artifacts": {}
    }
    
    try:
        # Stage A: EDL -> scenes.json (MVP 推荐)
        if edl_file:
            edl_path = job_dir / edl_file.filename
            with open(edl_path, "wb") as f:
                shutil.copyfileobj(edl_file.file, f)
            
            # TODO: 从请求参数获取 fps 和 primary_clip_path
            fps = 30  # 默认 30fps
            primary_clip_path = "D:/Footage/input.mp4"  # 需要用户提供
            
            scenes = parse_edl_to_scenes(str(edl_path), fps, primary_clip_path)
            scenes_path = job_dir / "scenes.json"
            with open(scenes_path, "w", encoding="utf-8") as f:
                json.dump(scenes, f, indent=2, ensure_ascii=False)
            
            result["artifacts"]["scenes"] = "scenes.json"
            job_store.update_job(job_id, status="analyzing", progress=30)
        
        # Stage A': FCPXML -> scenes.json
        if xml_file:
            xml_path = job_dir / xml_file.filename
            with open(xml_path, "wb") as f:
                shutil.copyfileobj(xml_file.file, f)
            
            scenes = parse_xml_to_scenes(str(xml_path))
            scenes_path = job_dir / "scenes.json"
            with open(scenes_path, "w", encoding="utf-8") as f:
                json.dump(scenes, f, indent=2, ensure_ascii=False)
            
            result["artifacts"]["scenes"] = "scenes.json"
            job_store.update_job(job_id, status="analyzing", progress=30)
        
        # Stage B: Whisper ASR -> transcript.json
        if audio_file:
            audio_path = job_dir / audio_file.filename
            with open(audio_path, "wb") as f:
                shutil.copyfileobj(audio_file.file, f)
            
            job_store.update_job(job_id, status="transcribing", progress=50)
            transcript = transcribe_audio(str(audio_path))
            
            transcript_path = job_dir / "transcript.json"
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
            
            result["artifacts"]["transcript"] = "transcript.json"
            job_store.update_job(job_id, status="analyzing", progress=80)
        
        # Stage C: SRT -> transcript.json (直接导入)
        if srt_file:
            srt_path = job_dir / srt_file.filename
            with open(srt_path, "wb") as f:
                shutil.copyfileobj(srt_file.file, f)
            
            # 解析 SRT 为 transcript.json
            from ..tools.srt_parser import parse_srt_to_transcript
            transcript = parse_srt_to_transcript(str(srt_path))
            
            transcript_path = job_dir / "transcript.json"
            with open(transcript_path, "w", encoding="utf-8") as f:
                json.dump(transcript, f, indent=2, ensure_ascii=False)
            
            result["artifacts"]["transcript"] = "transcript.json"
        
        if not result["artifacts"]:
            raise HTTPException(status_code=400, detail="至少需要提供一个文件")
        
        job_store.update_job(job_id, status="completed", progress=100, result=result)
        return JSONResponse(content=result)
        
    except Exception as e:
        job_store.update_job(job_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/job/{job_id}")
async def get_job_status(job_id: str):
    """获取任务状态"""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="任务不存在")
    return job


@router.get("/job/{job_id}/artifact/{artifact_name}")
async def get_artifact(job_id: str, artifact_name: str):
    """下载任务产物"""
    job_dir = settings.JOBS_DIR / job_id
    artifact_path = job_dir / artifact_name
    
    if not artifact_path.exists():
        raise HTTPException(status_code=404, detail="产物不存在")
    
    from fastapi.responses import FileResponse
    return FileResponse(artifact_path)
