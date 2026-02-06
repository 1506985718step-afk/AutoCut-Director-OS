"""
Script Assembly API - 零散镜头组装工作流
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from ..core.ui_translator import get_translator
from ..core.llm_engine import LLMDirector
from ..tools.bgm_library import BGMLibrary

router = APIRouter(prefix="/api/assembly", tags=["assembly"])

# 初始化
translator = get_translator()
bgm_library = BGMLibrary()


@router.post("/create")
async def create_assembly_project(
    background_tasks: BackgroundTasks,
    assets_manifest: UploadFile = File(...),
    script_outline: Optional[UploadFile] = File(None),
    platform: str = Form(...),
    style: str = Form(...),
    pace: str = Form(default="medium"),
    subtitle_density: str = Form(default="standard"),
    music_preference: str = Form(default="emotional")
):
    """
    创建零散镜头组装项目
    
    Args:
        assets_manifest: 素材清单文件 (assets_manifest.json)
        script_outline: 脚本大纲文件 (script_outline.json, 可选)
        platform: 平台选择
        style: 风格选择
        pace: 节奏选择
        subtitle_density: 字幕密度
        music_preference: 音乐偏好
    
    Returns:
        {
            "project_id": "asm_20260205_143000",
            "status": "processing",
            "message": "项目创建成功，正在处理中..."
        }
    """
    try:
        # 1. 生成项目 ID
        project_id = f"asm_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 2. 创建项目目录
        project_path = Path("jobs") / project_id
        project_path.mkdir(parents=True, exist_ok=True)
        (project_path / "input").mkdir(exist_ok=True)
        (project_path / "temp").mkdir(exist_ok=True)
        (project_path / "output").mkdir(exist_ok=True)
        
        # 3. 保存素材清单
        manifest_content = await assets_manifest.read()
        manifest_data = json.loads(manifest_content.decode("utf-8"))
        
        manifest_path = project_path / "input" / "assets_manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2, ensure_ascii=False)
        
        # 4. 保存脚本大纲（如果有）
        script_data = None
        if script_outline:
            script_content = await script_outline.read()
            script_data = json.loads(script_content.decode("utf-8"))
            
            script_path = project_path / "input" / "script_outline.json"
            with script_path.open("w", encoding="utf-8") as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
        
        # 5. 翻译 UI 意图
        platform_meta = translator.translate_platform(platform)
        initial_prompt = translator.build_initial_prompt(
            platform=platform,
            style=style,
            pace=pace,
            subtitle_density=subtitle_density,
            music_preference=music_preference
        )
        
        # 6. 创建项目元数据
        project_meta = {
            "project_id": project_id,
            "workflow": "script_assembly",
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "assets_manifest": manifest_data,
            "script_outline": script_data,
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
            "current_step": "asset_validation"
        }
        
        # 7. 保存元数据
        meta_path = project_path / "project_meta.json"
        with meta_path.open("w", encoding="utf-8") as f:
            json.dump(project_meta, f, indent=2, ensure_ascii=False)
        
        # 8. 启动后台处理任务
        background_tasks.add_task(
            process_assembly_project,
            project_id,
            manifest_data,
            script_data,
            initial_prompt,
            music_preference
        )
        
        return JSONResponse(content={
            "project_id": project_id,
            "status": "processing",
            "workflow": "script_assembly",
            "message": "项目创建成功，正在处理中..."
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建项目失败: {str(e)}")


async def process_assembly_project(
    project_id: str,
    manifest_data: dict,
    script_data: Optional[dict],
    prompt: str,
    music_preference: str
):
    """
    后台处理零散镜头组装项目
    """
    project_path = Path("jobs") / project_id
    
    try:
        # 步骤 1: 验证素材
        update_assembly_status(project_id, "asset_validation", 10, "正在验证素材...")
        
        # 检查所有素材文件是否存在
        missing_assets = []
        for asset in manifest_data.get("assets", []):
            asset_path = Path(asset.get("path", ""))
            if not asset_path.exists():
                missing_assets.append(asset.get("asset_id"))
        
        if missing_assets:
            raise RuntimeError(f"缺少素材文件: {', '.join(missing_assets)}")
        
        # 步骤 2: 导入素材到 Resolve
        update_assembly_status(project_id, "resolve_import", 30, "正在导入素材到剪辑引擎...")
        
        # TODO: 调用 Resolve API 导入素材
        # await import_assets_to_resolve(manifest_data)
        
        # 步骤 3: 生成组装 DSL
        update_assembly_status(project_id, "dsl_generation", 50, "AI 正在生成组装方案...")
        
        # 构建 assets 结构（类似 scenes）
        assets_structure = {
            "assets": manifest_data.get("assets", [])
        }
        
        # 如果有脚本大纲，使用它；否则让 AI 自动组装
        if script_data:
            prompt += f"\n\n脚本大纲：\n{json.dumps(script_data, ensure_ascii=False, indent=2)}"
        else:
            prompt += "\n\n请根据素材内容自动组装成连贯的视频。"
        
        # 获取 BGM 库
        bgm_lib = None
        if music_preference != "none":
            music_config = translator.translate_music_preference(music_preference)
            bgm_lib = bgm_library.search(
                mood=music_config.get("mood"),
                energy=music_config.get("energy")
            )
        
        # 生成 DSL（使用 asset_id 代替 scene_id）
        director = LLMDirector()
        
        # 创建一个适配器，将 assets 转换为 scenes 格式
        adapted_scenes = {
            "scenes": [
                {
                    "scene_id": asset["asset_id"],
                    "start_frame": 0,
                    "end_frame": asset.get("duration_frames", 300),
                    "metadata": asset
                }
                for asset in manifest_data.get("assets", [])
            ]
        }
        
        from ..models.schemas import ScenesJSON, TranscriptJSON
        
        scenes = ScenesJSON(**adapted_scenes)
        
        # 创建空的 transcript（零散镜头可能没有语音）
        transcript = TranscriptJSON(segments=[])
        
        dsl = director.generate_editing_dsl(scenes, transcript, prompt, bgm_library=bgm_lib)
        
        # 保存 DSL
        dsl_path = project_path / "temp" / "assembly_dsl.json"
        with dsl_path.open("w", encoding="utf-8") as f:
            json.dump(dsl, f, indent=2, ensure_ascii=False)
        
        # 步骤 4: 执行组装
        update_assembly_status(project_id, "assembly", 80, "正在自动组装...")
        
        # TODO: 执行 Resolve 组装
        
        # 步骤 5: 生成预览
        update_assembly_status(project_id, "preview_generation", 95, "正在生成预览...")
        
        # TODO: 生成预览视频
        
        # 完成
        update_assembly_status(project_id, "completed", 100, "处理完成")
        
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
        update_assembly_status(project_id, "error", 0, f"处理失败: {str(e)}")
        
        # 更新元数据
        meta_path = project_path / "project_meta.json"
        if meta_path.exists():
            with meta_path.open("r", encoding="utf-8") as f:
                project_meta = json.load(f)
            project_meta["status"] = "error"
            project_meta["error"] = str(e)
            with meta_path.open("w", encoding="utf-8") as f:
                json.dump(project_meta, f, indent=2, ensure_ascii=False)


def update_assembly_status(
    project_id: str,
    step: str,
    progress: int,
    message: str
):
    """更新组装项目状态"""
    # 这里应该更新全局状态存储
    # 暂时只打印日志
    print(f"[{project_id}] {step}: {progress}% - {message}")


@router.get("/{project_id}/status")
async def get_assembly_status(project_id: str):
    """
    获取组装项目状态
    
    Args:
        project_id: 项目 ID
    
    Returns:
        项目状态信息
    """
    project_path = Path("jobs") / project_id
    meta_path = project_path / "project_meta.json"
    
    if not meta_path.exists():
        raise HTTPException(status_code=404, detail="项目不存在")
    
    with meta_path.open("r", encoding="utf-8") as f:
        project_meta = json.load(f)
    
    return JSONResponse(content={
        "project_id": project_id,
        "workflow": "script_assembly",
        "status": project_meta.get("status", "unknown"),
        "progress": 100 if project_meta.get("status") == "completed" else 0,
        "current_step": project_meta.get("current_step", "unknown")
    })
