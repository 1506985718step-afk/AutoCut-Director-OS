"""执行路由 - 处理 DSL 执行请求"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Body
from fastapi.responses import JSONResponse
from pathlib import Path
import json
import shutil
from typing import Dict

from ..config import settings
from ..core.job_store import JobStore
from ..models.schemas import EditingDSL, ScenesJSON, DSLValidator
from ..executor.runner import Runner
from ..executor import actions

router = APIRouter()
job_store = JobStore()


@router.post("/execute")
async def execute(
    dsl_file: UploadFile = File(...),
    scenes_file: UploadFile = File(...)
):
    """
    执行 editing DSL，调用 Resolve 完成剪辑
    
    硬规则：必须同时上传 editing_dsl.json 和 scenes.json
    Executor 会验证 scene_id 存在 + trim_frames 在范围内（防 AI 幻觉）
    
    流程:
    1. 加载并验证 DSL 和 scenes
    2. 硬规则检查（scene_id + trim_frames）
    3. 转换为 Action 队列
    4. 执行 Resolve 操作
    5. 返回 trace 日志
    """
    # 创建执行任务
    job_id = job_store.create_job()
    job_dir = settings.JOBS_DIR / job_id
    
    try:
        # 保存 DSL
        dsl_path = job_dir / "editing_dsl.json"
        with open(dsl_path, "wb") as f:
            shutil.copyfileobj(dsl_file.file, f)
        
        # 保存 scenes
        scenes_path = job_dir / "scenes.json"
        with open(scenes_path, "wb") as f:
            shutil.copyfileobj(scenes_file.file, f)
        
        # 读取并解析 DSL
        with open(dsl_path, "r", encoding="utf-8") as f:
            dsl_data = json.load(f)
        dsl = EditingDSL(**dsl_data)
        
        # 读取并解析 scenes
        with open(scenes_path, "r", encoding="utf-8") as f:
            scenes_data = json.load(f)
        scenes = ScenesJSON(**scenes_data)
        
        # 硬规则验证：防止 AI 幻觉
        is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)
        if not is_valid:
            job_store.update_job(job_id, status="failed", error={"validation_errors": errors})
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "DSL validation failed (AI hallucination detected)",
                    "errors": errors
                }
            )
        
        job_store.update_job(job_id, status="executing", progress=10)
        
        # 转换 DSL 为 Action 队列
        actions = _dsl_to_actions(dsl, scenes)
        
        # 执行动作队列
        runner = Runner(job_id=job_id)
        job_store.update_job(job_id, status="executing", progress=30)
        
        runner.run(actions)
        trace = runner.get_trace()
        
        # 保存 trace
        trace_path = job_dir / "trace.json"
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(trace, f, indent=2, ensure_ascii=False)
        
        result = {
            "job_id": job_id,
            "status": "success",
            "trace": trace,
            "output": f"output/{job_id}.{dsl.export.format}"
        }
        
        job_store.update_job(job_id, status="completed", progress=100, result=result)
        return JSONResponse(content=result)
        
    except Exception as e:
        job_store.update_job(job_id, status="failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute/validate")
async def validate_dsl_endpoint(
    dsl_data: Dict = Body(...),
    scenes_data: Dict = Body(...)
):
    """仅验证 DSL，不执行"""
    try:
        dsl = EditingDSL(**dsl_data)
        scenes = ScenesJSON(**scenes_data)
        
        is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)
        
        return {
            "valid": is_valid,
            "errors": errors
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [str(e)]
        }


def _dsl_to_actions(dsl: EditingDSL, scenes: ScenesJSON) -> list:
    """
    将 DSL 转换为 Action 队列（数据驱动设计）
    
    Args:
        dsl: EditingDSL 对象
        scenes: ScenesJSON 对象
        
    Returns:
        Action 对象列表
    """
    action_list = []
    
    # 构建 scene_id -> Scene 映射
    scene_map = {scene.scene_id: scene for scene in scenes.scenes}
    
    # 1. 创建时间线
    width, height = map(int, dsl.export.resolution.split('x'))
    
    action_list.append(actions.create_timeline(
        name=f"AutoCut_{dsl.meta.target}",
        fps=scenes.meta.fps,
        resolution={"width": width, "height": height}
    ))
    
    # 2. 按 order 排序添加片段
    sorted_timeline = sorted(dsl.editing_plan.timeline, key=lambda x: x.order)
    
    for item in sorted_timeline:
        scene = scene_map[item.scene_id]
        trim_start, trim_end = item.trim_frames
        
        action_list.append(actions.append_scene(
            scene_id=item.scene_id,
            in_frame=trim_start,
            out_frame=trim_end,
            source=scenes.media.primary_clip_path
        ))
        
        # TODO: 添加 overlay_text 支持
    
    # 3. 添加字幕（如果模式是 from_transcript）
    if dsl.editing_plan.subtitles.mode == "from_transcript":
        # TODO: 需要 transcript.json 支持
        # action_list.append(actions.import_srt("path/to/subtitle.srt"))
        pass
    
    # 4. 添加背景音乐
    action_list.append(actions.add_music(
        path=dsl.editing_plan.music.track_path,
        volume_db=dsl.editing_plan.music.volume_db
    ))
    
    # 5. 导出
    action_list.append(actions.export_mp4(
        path=f"output/autocut_{dsl.meta.target}.{dsl.export.format}",
        resolution=dsl.export.resolution
    ))
    
    return action_list
