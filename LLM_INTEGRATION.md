# LLM 集成指南 - AI 生成剪辑脚本

## 概述

AutoCut Director 现已集成 LLM（大语言模型），让 AI 真正成为剪辑导演。系统可以根据视觉素材（scenes.json）和听觉素材（transcript.json），自动生成符合平台风格的剪辑脚本（editing_dsl.json）。

## 核心功能

### 1. LLM Director 引擎

位置：`app/core/llm_engine.py`

```python
from app.core.llm_engine import LLMDirector

director = LLMDirector()
dsl = director.generate_editing_dsl(
    scenes=scenes,           # ScenesJSON 对象
    transcript=transcript,   # TranscriptJSON 对象
    style_prompt="抖音爆款风格"
)
```

### 2. 字幕渲染系统

位置：`app/executor/resolve_adapter.py`

支持三种字幕样式：
- `bold_yellow` - 抖音风格（粗体黄字黑边）
- `clean_white` - 简洁白字
- `elegant_black` - 优雅黑字

```python
adapter.render_subtitles_from_transcript(
    transcript_segments=transcript.segments,
    fps=30,
    style="bold_yellow"
)
```

### 3. 文字叠加功能

支持自定义文字叠加（overlay_text）：

```python
adapter.add_text_overlay(
    text="第一步就错了",
    start_frame=30,
    duration_frames=60,
    style={
        "font_size": 72,
        "font_color": [1.0, 1.0, 0.0],  # 黄色
        "position": [0.5, 0.3],
        "stroke_width": 3,
        "stroke_color": [0.0, 0.0, 0.0]
    }
)
```

## 配置

### 1. 环境变量

在 `.env` 文件中配置：

```bash
# LLM 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=  # 可选：自定义端点（如 Azure）
```

### 2. 支持的模型

推荐使用：
- **gpt-4o** - 长窗口，JSON 模式支持好
- **gpt-4-turbo** - 性能好，成本适中
- **gpt-3.5-turbo** - 成本低，但可能不够稳定

也支持兼容 OpenAI API 的其他服务：
- Azure OpenAI
- 国内大模型（通义千问、文心一言等，需要适配层）

### 3. 安装依赖

```bash
pip install openai==1.54.0
```

## API 使用

### 1. 生成 DSL

```bash
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@examples/scenes.v1.json" \
  -F "transcript_file=@examples/transcript.v1.json" \
  -F "style_prompt=抖音爆款风格：节奏快、文字多、强调关键词"
```

响应：
```json
{
  "success": true,
  "dsl": {
    "meta": {...},
    "editing_plan": {...},
    "export": {...}
  },
  "meta": {
    "scenes_count": 3,
    "transcript_segments": 5,
    "timeline_items": 4,
    "style": "抖音爆款风格"
  }
}
```

### 2. 验证 DSL

```bash
curl -X POST http://localhost:8000/api/llm/validate-dsl \
  -F "dsl_file=@examples/editing_dsl.v1.json" \
  -F "scenes_file=@examples/scenes.v1.json"
```

### 3. 获取风格预设

```bash
curl http://localhost:8000/api/llm/style-presets
```

返回预设风格：
- `douyin` - 抖音爆款
- `bilibili` - B站知识区
- `youtube` - YouTube Vlog
- `kuaishou` - 快手热门

### 4. 批量生成

一次性生成多个平台的剪辑脚本：

```bash
curl -X POST http://localhost:8000/api/llm/batch-generate \
  -F "scenes_file=@examples/scenes.v1.json" \
  -F "transcript_file=@examples/transcript.v1.json" \
  -F "styles=douyin,bilibili,youtube"
```

## 完整工作流

### 方式 1: Python 脚本

```python
from app.tools.scene_from_edl import parse_edl_to_scenes
from app.tools.asr_whisper import transcribe_audio
from app.core.llm_engine import LLMDirector
from app.executor.runner import run_actions

# 1. 场景切分
scenes_data = parse_edl_to_scenes("input.edl", fps=30, primary_clip="input.mp4")

# 2. 语音转录
transcript_data = transcribe_audio("input.mp4", model="base", language="zh")

# 3. AI 生成 DSL
director = LLMDirector()
dsl = director.generate_editing_dsl(scenes, transcript, "抖音爆款风格")

# 4. 转换为动作
actions = dsl_to_actions(dsl, scenes_data)

# 5. 执行剪辑
trace = run_actions(actions)
```

### 方式 2: API 调用

```bash
# 1. 分析素材
curl -X POST http://localhost:8000/api/analyze \
  -F "edl_file=@input.edl" \
  -F "audio_file=@input.mp4"

# 2. AI 生成 DSL
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@scenes.json" \
  -F "transcript_file=@transcript.json" \
  -F "style_prompt=抖音爆款风格"

# 3. 执行剪辑
curl -X POST http://localhost:8000/api/execute \
  -F "dsl_file=@editing_dsl.json" \
  -F "scenes_file=@scenes.json"
```

## 风格提示词模板

### 抖音爆款

```
抖音爆款风格：
1. 开头 3 秒必须有强烈的 Hook（钩子），吸引观众停留
2. 节奏快，每 3-5 秒切换画面或文字
3. 删除所有废话、停顿、重复内容
4. 文字叠加要简短有力（5-8 字），突出关键信息
5. 强调数字和对比（如"90%的人"、"第一步"）
6. 总时长控制在 30-60 秒
```

### B站知识区

```
B站知识区风格：
1. 开头简短介绍主题
2. 节奏适中，每 5-10 秒切换画面
3. 保留完整的讲解内容
4. 字幕完整，突出关键知识点
5. 适当添加图表和示例
6. 总时长 3-10 分钟
```

### YouTube Vlog

```
YouTube Vlog 风格：
1. 保持自然的节奏和情感
2. 删除明显的废话和停顿
3. 保留有趣的瞬间和反应
4. 字幕简洁，不遮挡画面
5. 适当添加转场和音乐
6. 总时长 5-15 分钟
```

## 测试脚本

### 1. 测试 LLM 生成

```bash
python test_llm_director.py
```

### 2. 测试字幕渲染

```bash
python test_subtitle_rendering.py
```

### 3. 完整工作流

```bash
python example_ai_workflow.py
```

## 硬规则验证

LLM 生成的 DSL 会经过硬规则验证，防止 AI 幻觉：

1. **scene_id 存在性** - 确保引用的场景存在
2. **trim_frames 范围** - 确保裁剪范围在场景内
3. **trim_frames 顺序** - 确保 in < out

如果验证失败，API 会返回详细的错误信息：

```json
{
  "error": "AI 生成的 DSL 验证失败（AI 幻觉检测）",
  "validation_errors": [
    "Scene S9999 not found in scenes",
    "trim_frames [200, 300] out of range for scene S0001 [0, 120]"
  ]
}
```

## 字幕样式自定义

### 预设样式

```python
# 抖音风格
style = {
    "font_size": 72,
    "font_color": [1.0, 1.0, 0.0],  # 黄色
    "stroke_width": 3,
    "stroke_color": [0.0, 0.0, 0.0],  # 黑色描边
    "position": [0.5, 0.8],  # 底部
    "bold": True
}

# 简洁白字
style = {
    "font_size": 60,
    "font_color": [1.0, 1.0, 1.0],  # 白色
    "stroke_width": 2,
    "stroke_color": [0.0, 0.0, 0.0],
    "position": [0.5, 0.85],
    "bold": False
}

# 优雅黑字
style = {
    "font_size": 56,
    "font_color": [0.0, 0.0, 0.0],  # 黑色
    "stroke_width": 0,
    "stroke_color": [1.0, 1.0, 1.0],
    "position": [0.5, 0.15],  # 顶部
    "bold": False
}
```

### 自定义样式

```python
custom_style = {
    "font_size": 80,              # 字体大小
    "font_color": [1.0, 0.0, 0.0],  # RGB 颜色（红色）
    "position": [0.5, 0.5],       # 归一化坐标 (x, y)
    "alignment": "center",        # 对齐方式
    "bold": True,                 # 粗体
    "stroke_width": 4,            # 描边宽度
    "stroke_color": [1.0, 1.0, 1.0]  # 描边颜色（白色）
}
```

## 性能优化

### 1. 批量处理

使用批量生成 API 一次性生成多个平台的脚本，节省 API 调用次数。

### 2. 缓存策略

对于相同的素材和风格，可以缓存生成的 DSL：

```python
import hashlib
import json

def cache_key(scenes, transcript, style):
    content = json.dumps({
        "scenes": scenes.model_dump(),
        "transcript": transcript.model_dump(),
        "style": style
    }, sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()
```

### 3. 异步处理

对于长视频，建议使用异步任务队列（如 Celery）处理。

## 故障排查

### 1. LLM 调用失败

```
ValueError: OPENAI_API_KEY not configured in .env
```

解决：在 `.env` 中配置 API Key

### 2. JSON 解析失败

```
ValueError: AI 生成了无效的 JSON
```

解决：
- 检查模型是否支持 JSON 模式
- 尝试使用 gpt-4o 或 gpt-4-turbo
- 调整 temperature 参数（降低创造性）

### 3. 验证失败

```
AI 生成的 DSL 验证失败（AI 幻觉检测）
```

解决：
- 检查 system prompt 是否清晰
- 在 style_prompt 中强调硬规则
- 使用更强大的模型

### 4. 字幕渲染失败

```
RuntimeError: Cannot access Fusion
```

解决：
- 确保 DaVinci Resolve 正在运行
- 检查 Resolve 版本（需要 Studio 版本）
- 尝试使用 Title 生成器（备选方案）

## 最佳实践

### 1. 风格提示词

- 明确具体，避免模糊描述
- 包含时长要求
- 强调硬规则（scene_id、trim_frames）
- 提供示例

### 2. 素材准备

- 场景切分要合理（3-10 秒一个场景）
- 转录要准确（使用合适的 Whisper 模型）
- 素材质量要好（清晰、稳定）

### 3. 验证流程

```python
# 1. 生成 DSL
dsl = director.generate_editing_dsl(scenes, transcript, style)

# 2. 验证硬规则
errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
if errors:
    # 重新生成或手动修正
    pass

# 3. 预览（可选）
# 在 Resolve 中快速预览效果

# 4. 正式执行
trace = run_actions(actions)
```

## 扩展开发

### 1. 自定义风格

在 `routes_llm.py` 中添加新的风格预设：

```python
presets["custom"] = {
    "name": "自定义风格",
    "description": "描述",
    "prompt": "详细的风格要求..."
}
```

### 2. 多模型支持

修改 `llm_engine.py` 支持其他模型：

```python
# 使用 Anthropic Claude
from anthropic import Anthropic
client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

# 使用 Google Gemini
import google.generativeai as genai
genai.configure(api_key=settings.GOOGLE_API_KEY)
```

### 3. 自定义动作

在 `actions.py` 中添加新的动作类型：

```python
def add_transition(type: str, duration: int) -> Action:
    return Action("AddTransition", {
        "type": type,
        "duration": duration
    })
```

## 总结

LLM 集成让 AutoCut Director 真正实现了"AI 驱动的自动化剪辑"：

1. **输入** - EDL + 音频
2. **分析** - 场景切分 + 语音转录
3. **生成** - AI 生成剪辑脚本
4. **验证** - 硬规则防止幻觉
5. **执行** - 自动化剪辑
6. **输出** - 成片

整个流程完全自动化，只需提供素材和风格要求！

---

**相关文档**：
- [PROTOCOL.md](PROTOCOL.md) - 协议文件规范
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计
- [API_USAGE.md](API_USAGE.md) - API 使用指南
