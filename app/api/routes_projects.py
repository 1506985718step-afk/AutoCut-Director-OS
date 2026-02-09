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
        # 🔥 新增：在创建项目前先检查达芬奇状态
        from ..tools.resolve_importer import get_importer
        
        print("🔍 检查达芬奇状态...")
        resolve_importer = get_importer()
        status = resolve_importer.check_resolve_status()
        
        if not status.get("connected", False):
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "DaVinci Resolve 连接失败",
                    "message": status.get("message", "无法连接到 DaVinci Resolve"),
                    "error_details": status.get("error", ""),
                    "instructions": [
                        "1. 启动 DaVinci Resolve",
                        "2. 创建或打开一个项目",
                        "3. 在 偏好设置 -> 系统 -> 常规 中开启 '外部脚本使用'",
                        "4. 重新提交任务"
                    ]
                }
            )
        
        print("✅ 达芬奇状态检查通过")
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
        
        # 7. 初始化项目状态 (配合 7-Stage Workflow)
        project_status[project_id] = {
            "status": "processing",
            "progress": 5,
            "current_step": "setup",
            "steps": [
                {"name": "setup", "status": "pending", "message": "项目初始化"},       # Stage 0
                {"name": "ingest", "status": "pending", "message": "素材处理"},      # Stage 1
                {"name": "recognition", "status": "pending", "message": "AI 识别"},  # Stage 2
                {"name": "director", "status": "pending", "message": "导演编排"},    # Stage 3
                {"name": "execution", "status": "pending", "message": "剪辑执行"},   # Stage 4
                {"name": "review", "status": "pending", "message": "成片审查"},      # Stage 5
                {"name": "export", "status": "pending", "message": "最终导出"}       # Stage 6
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
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


async def process_project(
    project_id: str,
    video_path: str,
    prompt: str,
    music_preference: str
):
    """
    后台处理项目 (基于 WorkflowOrchestrator 的 7 阶段流程)
    """
    from ..core.workflow_orchestrator import WorkflowOrchestrator, WorkflowStage
    
    project_path = Path("jobs") / project_id
    orchestrator = WorkflowOrchestrator(project_id, Path("jobs"))
    
    # 状态映射辅助函数
    def update_stage_status(stage_name, progress, message):
        update_project_status(project_id, stage_name, progress, message)

    # Debug Log Setup
    debug_log = Path("jobs") / "backend_debug.log"
    def log(msg):
        with open(debug_log, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().isoformat()}] {msg}\n")

    try:
        log(f"START process_project: {project_id}")
        
        # --- Stage 0: Setup ---
        log("Stage 0: Updating status to setup...")
        update_stage_status("setup", 10, "正在初始化 Resolve 项目...")
        
        log("Stage 0: Calling orchestrator.run_stage(SETUP)...")
        result = await orchestrator.run_stage(WorkflowStage.SETUP, video_path=video_path)
        log(f"Stage 0 Result: {result}")
        
        if not result["success"]:
            log("Stage 0 FAILED")
            raise RuntimeError(f"Stage 0 Failed: {result.get('message')}")
            
        log("Stage 0: Success. Updating status...")
        update_stage_status("setup", 15, "✓ 项目建立完成")

        # --- Stage 1: Ingest ---
        log("Stage 1: Updating status to ingest...")
        update_stage_status("ingest", 20, "正在处理素材...")
        
        log("Stage 1: Calling orchestrator.run_stage(INGEST)...")
        result = await orchestrator.run_stage(WorkflowStage.INGEST)
        log(f"Stage 1 Result: {result}")
        if not result["success"]:
            raise RuntimeError(f"Stage 1 Failed: {result.get('message')}")
        update_stage_status("ingest", 30, f"✓ 素材处理完成 ({len(orchestrator.context['assets'])} 个文件)")

        # --- Stage 2: Recognition ---
        update_stage_status("recognition", 35, "正在进行 AI 识别 (语音/视觉)...")
        result = await orchestrator.run_stage(WorkflowStage.RECOGNITION)
        if not result["success"]:
            raise RuntimeError(f"Stage 2 Failed: {result.get('message')}")
        update_stage_status("recognition", 50, f"✓ 识别完成 ({result.get('shotcards_count')} 个镜头)")

        # --- Stage 3: Director ---
        log("Stage 3: Updating status to director...")
        update_stage_status("director", 55, "AI 导演正在构思脚本...")
        
        log(f"Stage 3: Calling orchestrator.run_stage(DIRECTOR) with prompt: {prompt}")
        result = await orchestrator.run_stage(WorkflowStage.DIRECTOR, prompt=prompt)
        log(f"Stage 3 Result: {result}")
        
        if not result["success"]:
            log("Stage 3 FAILED")
            raise RuntimeError(f"Stage 3 Failed: {result.get('message')}")
            
        update_stage_status("director", 65, "✓ 脚本生成完成")

        # --- Stage 4: Execution ---
        log("Stage 4: Updating status to execution...")
        update_stage_status("execution", 70, "正在执行剪辑...")
        
        log("Stage 4: Calling orchestrator.run_stage(EXECUTION)...")
        result = await orchestrator.run_stage(WorkflowStage.EXECUTION)
        log(f"Stage 4 Result: {result}")
        
        if not result["success"]:
             raise RuntimeError(f"Stage 4 Failed: {result.get('message')}")
             
        update_stage_status("execution", 85, "✓ 粗剪完成")

        # --- Stage 5: Review ---
        update_stage_status("review", 90, "正在自动审查...")
        # result = await orchestrator.run_stage(WorkflowStage.REVIEW)
        # Placeholder
        update_stage_status("review", 95, "✓ 审查通过")

        # --- Stage 6: Export ---
        update_stage_status("export", 98, "正在导出最终成片...")
        # result = await orchestrator.run_stage(WorkflowStage.EXPORT)
        # Placeholder
        update_stage_status("export", 100, "✓ 处理完成")
        
        # 完成状态更新
        update_project_status(project_id, "completed", 100, "全流程处理完成")
        
        # 保存最终元数据
        meta_path = project_path / "project_meta.json"
        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as f:
                project_meta = json.load(f)
                project_meta["status"] = "completed"
                # project_meta["dsl_path"] = ... 
            
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(project_meta, f, indent=2, ensure_ascii=False)

    except Exception as e:
        import traceback
        traceback.print_exc()
        update_project_status(project_id, "error", 0, f"处理失败: {str(e)}")
        
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
    steps = status["steps"]
    try:
        current_idx = next(i for i, s in enumerate(steps) if s["name"] == step)
        
        for i, s in enumerate(steps):
            if i < current_idx:
                s["status"] = "completed"
            elif i == current_idx:
                s["status"] = "active"
                s["message"] = message
            else:
                s["status"] = "pending"
    except StopIteration:
        # Step name not found
        pass
    
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