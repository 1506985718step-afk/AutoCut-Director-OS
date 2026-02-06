"""LLM 相关 API 路由 - AI 生成剪辑脚本"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import json
from pathlib import Path
from ..core.llm_engine import LLMDirector
from ..models.schemas import ScenesJSON, TranscriptJSON, DSLValidator


router = APIRouter()


@router.post("/generate-dsl")
async def generate_dsl(
    scenes_file: UploadFile = File(..., description="scenes.v1.json 文件"),
    transcript_file: UploadFile = File(..., description="transcript.v1.json 文件"),
    style_prompt: str = Form(
        default="抖音爆款风格：节奏快、文字多、强调关键词",
        description="剪辑风格描述"
    )
):
    """
    AI 生成剪辑脚本
    
    输入：
    - scenes.v1.json（场景切分）
    - transcript.v1.json（语音转录）
    - style_prompt（风格描述）
    
    输出：
    - editing_dsl.v1.json（剪辑指令）
    
    示例：
    ```bash
    curl -X POST http://localhost:8000/api/llm/generate-dsl \
      -F "scenes_file=@examples/scenes.v1.json" \
      -F "transcript_file=@examples/transcript.v1.json" \
      -F "style_prompt=抖音爆款风格"
    ```
    """
    try:
        # 1. 读取上传的文件
        scenes_content = await scenes_file.read()
        transcript_content = await transcript_file.read()
        
        scenes_data = json.loads(scenes_content.decode("utf-8"))
        transcript_data = json.loads(transcript_content.decode("utf-8"))
        
        # 2. 验证数据格式
        scenes = ScenesJSON(**scenes_data)
        transcript = TranscriptJSON(**transcript_data)
        
        # 3. 调用 LLM 生成 DSL
        director = LLMDirector()
        dsl = director.generate_editing_dsl(scenes, transcript, style_prompt)
        
        # 4. 验证生成的 DSL
        errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
        
        if errors:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "AI 生成的 DSL 验证失败（AI 幻觉检测）",
                    "validation_errors": errors,
                    "dsl": dsl  # 仍然返回 DSL，供调试
                }
            )
        
        # 5. 返回生成的 DSL
        return JSONResponse(
            content={
                "success": True,
                "dsl": dsl,
                "meta": {
                    "scenes_count": len(scenes.scenes),
                    "transcript_segments": len(transcript.segments),
                    "timeline_items": len(dsl["editing_plan"]["timeline"]),
                    "style": style_prompt
                }
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM 调用失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"处理失败: {str(e)}"
        )


@router.post("/validate-dsl")
async def validate_dsl(
    dsl_file: UploadFile = File(..., description="editing_dsl.v1.json 文件"),
    scenes_file: UploadFile = File(..., description="scenes.v1.json 文件")
):
    """
    验证 DSL 硬规则
    
    检查：
    - scene_id 存在性
    - trim_frames 范围
    - trim_frames 顺序
    
    示例：
    ```bash
    curl -X POST http://localhost:8000/api/llm/validate-dsl \
      -F "dsl_file=@examples/editing_dsl.v1.json" \
      -F "scenes_file=@examples/scenes.v1.json"
    ```
    """
    try:
        # 读取文件
        dsl_content = await dsl_file.read()
        scenes_content = await scenes_file.read()
        
        dsl_data = json.loads(dsl_content.decode("utf-8"))
        scenes_data = json.loads(scenes_content.decode("utf-8"))
        
        # 验证
        errors = DSLValidator.validate_dsl_against_scenes(dsl_data, scenes_data)
        
        if errors:
            return JSONResponse(
                content={
                    "valid": False,
                    "errors": errors
                }
            )
        
        return JSONResponse(
            content={
                "valid": True,
                "message": "DSL 验证通过"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"验证失败: {str(e)}"
        )


@router.get("/style-presets")
async def get_style_presets():
    """
    获取预设的剪辑风格
    
    返回常用的风格描述模板
    """
    presets = {
        "douyin": {
            "name": "抖音爆款",
            "description": "节奏快、文字多、强调关键词",
            "prompt": """
抖音爆款风格：
1. 开头 3 秒必须有强烈的 Hook（钩子）
2. 节奏快，每 3-5 秒切换画面或文字
3. 删除所有废话、停顿、重复内容
4. 文字叠加要简短有力（5-8 字）
5. 强调数字和对比
6. 总时长 30-60 秒
"""
        },
        "bilibili": {
            "name": "B站知识区",
            "description": "节奏适中、字幕完整、强调知识点",
            "prompt": """
B站知识区风格：
1. 开头简短介绍主题
2. 节奏适中，每 5-10 秒切换画面
3. 保留完整的讲解内容
4. 字幕完整，突出关键知识点
5. 适当添加图表和示例
6. 总时长 3-10 分钟
"""
        },
        "youtube": {
            "name": "YouTube Vlog",
            "description": "自然流畅、保留情感、适度剪辑",
            "prompt": """
YouTube Vlog 风格：
1. 保持自然的节奏和情感
2. 删除明显的废话和停顿
3. 保留有趣的瞬间和反应
4. 字幕简洁，不遮挡画面
5. 适当添加转场和音乐
6. 总时长 5-15 分钟
"""
        },
        "kuaishou": {
            "name": "快手热门",
            "description": "接地气、情感强、节奏紧凑",
            "prompt": """
快手热门风格：
1. 开头直接切入主题
2. 节奏紧凑，保持高能
3. 强调情感和共鸣
4. 文字大而醒目
5. 多用对比和反转
6. 总时长 15-60 秒
"""
        }
    }
    
    return JSONResponse(content={"presets": presets})


@router.post("/batch-generate")
async def batch_generate_dsl(
    scenes_file: UploadFile = File(...),
    transcript_file: UploadFile = File(...),
    styles: str = Form(..., description="风格列表，逗号分隔，如: douyin,bilibili,youtube")
):
    """
    批量生成多个风格的 DSL
    
    一次性生成多个平台的剪辑脚本
    
    示例：
    ```bash
    curl -X POST http://localhost:8000/api/llm/batch-generate \
      -F "scenes_file=@examples/scenes.v1.json" \
      -F "transcript_file=@examples/transcript.v1.json" \
      -F "styles=douyin,bilibili,youtube"
    ```
    """
    try:
        # 读取文件
        scenes_content = await scenes_file.read()
        transcript_content = await transcript_file.read()
        
        scenes_data = json.loads(scenes_content.decode("utf-8"))
        transcript_data = json.loads(transcript_content.decode("utf-8"))
        
        scenes = ScenesJSON(**scenes_data)
        transcript = TranscriptJSON(**transcript_data)
        
        # 获取风格预设
        presets_response = await get_style_presets()
        presets = json.loads(presets_response.body)["presets"]
        
        # 批量生成
        director = LLMDirector()
        results = {}
        
        for style_key in styles.split(","):
            style_key = style_key.strip()
            
            if style_key not in presets:
                results[style_key] = {"error": f"未知风格: {style_key}"}
                continue
            
            try:
                style_prompt = presets[style_key]["prompt"]
                dsl = director.generate_editing_dsl(scenes, transcript, style_prompt)
                
                # 验证
                errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
                
                results[style_key] = {
                    "success": len(errors) == 0,
                    "dsl": dsl,
                    "validation_errors": errors if errors else None
                }
                
            except Exception as e:
                results[style_key] = {"error": str(e)}
        
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"批量生成失败: {str(e)}"
        )
