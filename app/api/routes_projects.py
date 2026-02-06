"""
产品级 API - 项目管理
用户友好的 API，隐藏所有技术细节
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from typing import Optional, Dict, Any
import json
import shutil
from datetime import datetime
import asyncio

from ..core.ui_translator import get_translator
from ..core.llm_engine import LLMDirector
from ..core.job_store import JobStore
from ..tools.media_ingest import MediaIngest
from ..tools.bgm_library import BGMLibrary
from ..tools.resolve_importer import get_importer
from ..executor.runner import Runner
from ..models.schemas import ScenesJSON, TranscriptJSON

router = APIRouter(prefix="/api/projects", tags=["projects"])

# 初始化
translator = get_translator()
job_store = JobStore()
media_ingest = MediaIngest(job_dir="jobs")
bgm_library = BGMLibrary()
resolve_importer = get_importer()


# 全局项目状态存储（生产环境应使用 Redis）
project_status = {}


@router.post("/create")
async def create_project(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    platform: str = Form(...),
    style: str = Form(...),
    pace: str = Form(default="medium"),
    subtitle_density: str = Form(default="standard"),
    music_preference: str = Form(default="emotional")
):
    """
    创建新项目（产品级 API）
    
    用户只需上传视频和选择偏好，系统自动完成所有处理
    
    Args:
        video: 视频文件
        platform: 平台选择 (douyin/bilibili/youtube/kuaishou)
        style: 风格选择 (teaching/emotional/viral/vlog)
        pace: 节奏选择 (slow/medium/fast)
        subtitle_density: 字幕密度 (minimal/standard/dense)
        music_preference: 音乐偏好 (none/emotional/suspense/upbeat/calm)
    
    Returns:
        {
            "project_id": "proj_20260205_143000",
            "status": "processing",
            "message": "项目创建成功，正在处理中..."
        }
    """
    try:
        # 1. 生成项目 ID
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 2. 创建项目目录
        project_path = Path("jobs") / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "input").mkdir(exist_ok=True)
        (project_path / "temp").mkdir(exist_ok=True)
        (project_path / "output").mkdir(exist_ok=True)
        
        # 3. 保存视频
        video_path = project_path / "input" / video.filename
        with video_path.open("wb") as f:
            shutil.copyfileobj(video.file, f)
        
        # 4. 翻译 UI 意图
        platform_meta = translator.translate_platform(platform)
        initial_prompt = translator.build_initial_prompt(
            platform=platform,
            style=style,
            pace=pace,
            subtitle_density=subtitle_density,
            music_preference=music_preference
        )
        
        # 5. 创建项目元数据
        project_meta = {
            "project_id": project_id,
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "video_path": str(video_path),
            "user_preferences": {
                "platform": platform,
                "style": style,
                "pace": pace,
                "subtitle_density": subtitle_density,
                "music_preference": music_preference
            },
            "platform_meta": platform_meta,
            "initial_prompt": initial_prompt,
            "status": "processing",
            "progress": 0,
            "current_step": "video_import"
        }
        
        # 6. 保存元数据
        meta_path = project_path / "project_meta.json"
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(project_meta, f, indent=2, ensure_ascii=False)
        
        # 7. 初始化项目状态
        project_status[project_id] = {
            "status": "processing",
            "progress": 5,
            "current_step": "video_import",
            "steps": [
                {"name": "video_import", "status": "completed", "message": "视频已导入"},
                {"name": "audio_analysis", "status": "pending", "message": "等待中"},
                {"name": "scene_detection", "status": "pending", "message": "等待中"},
                {"name": "dsl_generation", "status": "pending", "message": "等待中"},
                {"name": "editing", "status": "pending", "message": "等待中"},
                {"name": "preview_generation", "status": "pending", "message": "等待中"}
            ],
            "estimated_remaining": 180
        }
        
        # 8. 启动后台处理任务
        background_tasks.add_task(
            process_project,
            project_id,
            str(video_path),
            initial_prompt,
            music_preference
        )
        
        return JSONResponse(content={
            "project_id": project_id,
            "status": "processing",
            "message": "项目创建成功，正在处理中..."
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


async def process_project(
    project_id: str,
    video_path: str,
    prompt: str,
    music_preference: str
):
    """
    后台处理项目（完整流程）
    
    这个函数对用户不可见，自动完成所有处理步骤
    """
    project_path = Path("jobs") / project_id
    
    try:
        # 步骤 1: 提取音频
        update_project_status(project_id, "audio_analysis", 20, "正在分析音频...")
        audio_path = project_path / "temp" / "audio.wav"
        media_ingest.extract_audio(video_path, str(audio_path))
        
        # 步骤 1.5: 导入素材到 Resolve
        update_project_status(project_id, "resolve_import", 25, "正在同步到剪辑引擎...")
        
        # 检查 Resolve 状态
        resolve_status = resolve_importer.check_resolve_status()
        
        if resolve_status["connected"]:
            # 导入视频到 Media Pool
            import_result = resolve_importer.import_media([video_path])
            
            if import_result["success"]:
                update_project_status(
                    project_id,
                    "resolve_import",
                    30,
                    f"✓ 已同步到剪辑引擎 ({resolve_status['project_name']})"
                )
            else:
                update_project_status(
                    project_id,
                    "resolve_import",
                    30,
                    f"⚠️ 同步失败: {import_result['message']}"
                )
        else:
            update_project_status(
                project_id,
                "resolve_import",
                30,
                "⚠️ DaVinci Resolve 未启动，跳过同步"
            )
        
        # 步骤 2: 语音识别（ASR）
        update_project_status(project_id, "audio_analysis", 35, "正在识别语音...")
        # TODO: 集成 Whisper ASR
        # transcript = await run_asr(audio_path)
        # 暂时使用模拟数据
        transcript_data = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "大家好，今天我们来讲解..."}
            ]
        }
        transcript_path = project_path / "temp" / "transcript.json"
        with transcript_path.open("w", encoding="utf-8") as f:
            json.dump(transcript_data, f, indent=2, ensure_ascii=False)
        
        # 步骤 3: 场景检测
        update_project_status(project_id, "scene_detection", 50, "正在检测场景...")
        # TODO: 集成场景检测
        # scenes = await detect_scenes(video_path)
        # 暂时使用模拟数据
        scenes_data = {
            "scenes": [
                {"scene_id": "scene_001", "start_frame": 0, "end_frame": 150}
            ]
        }
        scenes_path = project_path / "temp" / "scenes.json"
        with scenes_path.open("w", encoding="utf-8") as f:
            json.dump(scenes_data, f, indent=2, ensure_ascii=False)
        
        # 步骤 4: AI 生成 DSL
        update_project_status(project_id, "dsl_generation", 65, "AI 正在生成剪辑方案...")
        
        scenes = ScenesJSON(**scenes_data)
        transcript = TranscriptJSON(**transcript_data)
        
        # 获取 BGM 库
        bgm_lib = None
        if music_preference != "none":
            music_config = translator.translate_music_preference(music_preference)
            bgm_lib = bgm_library.search(
                mood=music_config.get("mood"),
                energy=music_config.get("energy")
            )
        
        director = LLMDirector()
        dsl = director.generate_editing_dsl(scenes, transcript, prompt, bgm_library=bgm_lib)
        
        dsl_path = project_path / "temp" / "editing_dsl.json"
        with dsl_path.open("w", encoding="utf-8") as f:
            json.dump(dsl, f, indent=2, ensure_ascii=False)
        
        # 步骤 5: 执行剪辑
        update_project_status(project_id, "editing", 80, "正在自动剪辑...")
        # TODO: 集成 Resolve 执行
        # runner = ExecutionRunner()
        # await runner.execute(dsl, video_path)
        
        # 步骤 6: 生成预览
        update_project_status(project_id, "preview_generation", 95, "正在生成预览...")
        # TODO: 生成预览视频
        
        # 完成
        update_project_status(project_id, "completed", 100, "处理完成")
        
        # 提取摘要
        summary = translator.extract_summary_from_dsl(dsl)
        
        # 更新项目元数据
        meta_path = project_path / "project_meta.json"
        with meta_path.open("r", encoding="utf-8") as f:
            project_meta = json.load(f)
        
        project_meta["status"] = "completed"
        project_meta["summary"] = summary
        project_meta["dsl_path"] = str(dsl_path)
        
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(project_meta, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        # 错误处理
        update_project_status(project_id, "error", 0, f"处理失败: {str(e)}")
        
        # 更新元数据
        meta_path = project_path / "project_meta.json"
        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as f:
                project_meta = json.load(f)
            project_meta["status"] = "error"
            project_meta["error"] = str(e)
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(project_meta, f, indent=2, ensure_ascii=False)


def update_project_status(
    project_id: str,
    step: str,
    progress: int,
    message: str
):
    """更新项目状态"""
    if project_id not in project_status:
        return
    
    status = project_status[project_id]
    status["progress"] = progress
    status["current_step"] = step
    
    # 更新步骤状态
    for s in status["steps"]:
        if s["name"] == step:
            s["status"] = "active"
            s["message"] = message
        elif s["name"] < step:  # 之前的步骤
            s["status"] = "completed"
    
    # 更新预计剩余时间
    remaining = int((100 - progress) / 100 * 180)
    status["estimated_remaining"] = remaining


@router.get("/{project_id}/status")
async def get_project_status(project_id: str):
    """
    获取项目状态（用于轮询）
    
    Args:
        project_id: 项目 ID
    
    Returns:
        项目状态信息
    """
    # 从内存获取实时状态
    if project_id in project_status:
        return JSONResponse(content={
            "project_id": project_id,
            **project_status[project_id]
        })
    
    # 从文件获取持久化状态
    project_path = Path("jobs") / project_id
    meta_path = project_path / "project_meta.json"
    
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    with meta_path.open("r", encoding="utf-8") as f:
        project_meta = json.load(f)
    
    return JSONResponse(content={
        "project_id": project_id,
        "status": project_meta.get("status", "unknown"),
        "progress": 100 if project_meta.get("status") == "completed" else 0,
        "current_step": project_meta.get("current_step", "unknown")
    })


@router.get("/{project_id}")
async def get_project(project_id: str, version: Optional[int] = None):
    """
    获取项目详情
    
    Args:
        project_id: 项目 ID
        version: 版本号（可选，默认最新版本）
    
    Returns:
        项目详细信息
    """
    project_path = Path("jobs") / project_id
    
    # 如果指定了版本，使用版本路径
    if version:
        project_path = Path("jobs") / f"{project_id}_v{version}"
    
    meta_path = project_path / "project_meta.json"
    
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    with meta_path.open("r", encoding="utf-8") as f:
        project_meta = json.load(f)
    
    # 添加预览 URL
    if project_meta.get("status") == "completed":
        project_meta["preview_url"] = f"/api/projects/{project_id}/preview"
        if version:
            project_meta["preview_url"] += f"?version={version}"
    
    return JSONResponse(content=project_meta)


@router.get("/{project_id}/preview")
async def get_project_preview(
    project_id: str,
    version: Optional[int] = None,
    quality: str = "480p"
):
    """
    获取项目预览视频
    
    Args:
        project_id: 项目 ID
        version: 版本号（可选）
        quality: 预览质量 (480p/720p)
    
    Returns:
        视频文件流
    """
    project_path = Path("jobs") / project_id
    
    if version:
        project_path = Path("jobs") / f"{project_id}_v{version}"
    
    preview_path = project_path / "temp" / f"preview_{quality}.mp4"
    
    if not preview_path.exists():
        # 如果预览不存在，尝试返回原始输出
        output_path = project_path / "output" / "final.mp4"
        if output_path.exists():
            return FileResponse(output_path, media_type="video/mp4")
        
        raise HTTPException(status_code=404, detail="预览视频不存在")
    
    return FileResponse(preview_path, media_type="video/mp4")


@router.post("/{project_id}/adjust")
async def adjust_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    adjustments: Dict[str, str]
):
    """
    调整项目（意图式调整）
    
    用户只需表达意图，系统自动重新生成 DSL 并执行
    
    Args:
        project_id: 项目 ID
        adjustments: 调整意图 {"pace": "faster", "hook": "stronger", ...}
    
    Returns:
        {
            "project_id": "proj_xxx",
            "new_version": 2,
            "status": "processing",
            "message": "正在重新生成..."
        }
    """
    try:
        # 1. 获取原项目信息
        project_path = Path("jobs") / project_id
        meta_path = project_path / "project_meta.json"
        
        if not meta_path.exists():
            raise HTTPException(status_code=404, detail="项目不存在")
        
        with meta_path.open("r", encoding="utf-8") as f:
            project_meta = json.load(f)
        
        # 2. 计算新版本号
        current_version = project_meta.get("version", 1)
        new_version = current_version + 1
        
        # 3. 创建新版本目录
        new_project_path = Path("jobs") / f"{project_id}_v{new_version}"
        new_project_path.mkdir(parents=True, exist_ok=True)
        (new_project_path / "temp").mkdir(exist_ok=True)
        (new_project_path / "output").mkdir(exist_ok=True)
        
        # 4. 复制必要文件
        shutil.copy(project_path / "temp" / "scenes.json", new_project_path / "temp")
        shutil.copy(project_path / "temp" / "transcript.json", new_project_path / "temp")
        
        # 5. 构建调整后的 prompt
        original_prompt = project_meta.get("initial_prompt", "")
        new_prompt = translator.build_adjustment_prompt(original_prompt, adjustments)
        
        # 6. 创建新版本元数据
        new_meta = project_meta.copy()
        new_meta["version"] = new_version
        new_meta["parent_version"] = current_version
        new_meta["created_at"] = datetime.now().isoformat()
        new_meta["user_adjustments"] = adjustments
        new_meta["adjusted_prompt"] = new_prompt
        new_meta["status"] = "processing"
        
        new_meta_path = new_project_path / "project_meta.json"
        with new_meta_path.open("w", encoding="utf-8") as f:
            json.dump(new_meta, f, indent=2, ensure_ascii=False)
        
        # 7. 初始化新版本状态
        new_project_id = f"{project_id}_v{new_version}"
        project_status[new_project_id] = {
            "status": "processing",
            "progress": 10,
            "current_step": "dsl_generation",
            "steps": [
                {"name": "dsl_generation", "status": "active", "message": "AI 正在重新生成剪辑方案..."},
                {"name": "editing", "status": "pending", "message": "等待中"},
                {"name": "preview_generation", "status": "pending", "message": "等待中"}
            ],
            "estimated_remaining": 60
        }
        
        # 8. 启动后台处理
        background_tasks.add_task(
            reprocess_project,
            new_project_id,
            new_prompt,
            project_meta.get("user_preferences", {}).get("music_preference", "emotional")
        )
        
        return JSONResponse(content={
            "project_id": project_id,
            "new_version": new_version,
            "status": "processing",
            "message": "正在重新生成..."
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调整失败: {str(e)}")


async def reprocess_project(
    project_id: str,
    prompt: str,
    music_preference: str
):
    """重新处理项目（仅重新生成 DSL 和执行）"""
    project_path = Path("jobs") / project_id
    
    try:
        # 读取 scenes 和 transcript
        with (project_path / "temp" / "scenes.json").open("r", encoding="utf-8") as f:
            scenes_data = json.load(f)
        with (project_path / "temp" / "transcript.json").open("r", encoding="utf-8") as f:
            transcript_data = json.load(f)
        
        scenes = ScenesJSON(**scenes_data)
        transcript = TranscriptJSON(**transcript_data)
        
        # 重新生成 DSL
        update_project_status(project_id, "dsl_generation", 40, "AI 正在重新生成剪辑方案...")
        
        bgm_lib = None
        if music_preference != "none":
            music_config = translator.translate_music_preference(music_preference)
            bgm_lib = bgm_library.search(
                mood=music_config.get("mood"),
                energy=music_config.get("energy")
            )
        
        director = LLMDirector()
        dsl = director.generate_editing_dsl(scenes, transcript, prompt, bgm_library=bgm_lib)
        
        dsl_path = project_path / "temp" / "editing_dsl.json"
        with dsl_path.open("w", encoding="utf-8") as f:
            json.dump(dsl, f, indent=2, ensure_ascii=False)
        
        # 执行剪辑
        update_project_status(project_id, "editing", 70, "正在重新剪辑...")
        # TODO: 执行 Resolve
        
        # 生成预览
        update_project_status(project_id, "preview_generation", 95, "正在生成预览...")
        # TODO: 生成预览
        
        # 完成
        update_project_status(project_id, "completed", 100, "处理完成")
        
        # 更新元数据
        summary = translator.extract_summary_from_dsl(dsl)
        meta_path = project_path / "project_meta.json"
        with meta_path.open("r", encoding="utf-8") as f:
            project_meta = json.load(f)
        project_meta["status"] = "completed"
        project_meta["summary"] = summary
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(project_meta, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        update_project_status(project_id, "error", 0, f"处理失败: {str(e)}")


@router.get("/{project_id}/versions")
async def get_project_versions(project_id: str):
    """
    获取项目所有版本
    
    Args:
        project_id: 项目 ID
    
    Returns:
        版本列表
    """
    versions = []
    jobs_dir = Path("jobs")
    
    # 查找所有版本
    for path in jobs_dir.glob(f"{project_id}*"):
        if path.is_dir():
            meta_path = path / "project_meta.json"
            if meta_path.exists():
                with meta_path.open("r", encoding="utf-8") as f:
                    meta = json.load(f)
                
                version_info = {
                    "version": meta.get("version", 1),
                    "created_at": meta.get("created_at"),
                    "status": meta.get("status"),
                    "summary": meta.get("summary", {}),
                    "user_adjustments": meta.get("user_adjustments", {}),
                    "preview_url": f"/api/projects/{project_id}/preview?version={meta.get('version', 1)}"
                }
                
                versions.append(version_info)
    
    # 按版本号排序
    versions.sort(key=lambda x: x["version"])
    
    return JSONResponse(content={
        "project_id": project_id,
        "total_versions": len(versions),
        "versions": versions
    })


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """
    删除项目及所有版本
    
    Args:
        project_id: 项目 ID
    
    Returns:
        删除结果
    """
    try:
        jobs_dir = Path("jobs")
        deleted_count = 0
        
        # 删除所有版本
        for path in jobs_dir.glob(f"{project_id}*"):
            if path.is_dir():
                shutil.rmtree(path)
                deleted_count += 1
        
        # 清理内存状态
        keys_to_remove = [k for k in project_status.keys() if k.startswith(project_id)]
        for key in keys_to_remove:
            del project_status[key]
        
        return JSONResponse(content={
            "project_id": project_id,
            "deleted_versions": deleted_count,
            "message": "项目已删除"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")
