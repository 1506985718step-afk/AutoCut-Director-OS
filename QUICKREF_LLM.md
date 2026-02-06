# LLM 功能快速参考

## 🚀 5 分钟上手

### 1. 配置（1 分钟）

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
```

### 2. 安装（1 分钟）

```bash
pip install openai==1.54.0
```

### 3. 测试（3 分钟）

```bash
python test_llm_director.py
```

---

## 📝 代码示例

### Python 调用

```python
from app.core.llm_engine import LLMDirector
from app.models.schemas import ScenesJSON, TranscriptJSON

# 加载素材
scenes = ScenesJSON(**scenes_data)
transcript = TranscriptJSON(**transcript_data)

# AI 生成剪辑脚本
director = LLMDirector()
dsl = director.generate_editing_dsl(
    scenes=scenes,
    transcript=transcript,
    style_prompt="抖音爆款风格：节奏快、文字多、强调关键词"
)
```

### API 调用

```bash
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@scenes.json" \
  -F "transcript_file=@transcript.json" \
  -F "style_prompt=抖音爆款风格"
```

---

## 🎨 风格预设

| 平台 | 关键词 | 时长 | 特点 |
|------|--------|------|------|
| 抖音 | `douyin` | 30-60s | 节奏快、文字多、强调关键词 |
| B站 | `bilibili` | 3-10min | 节奏适中、字幕完整、强调知识点 |
| YouTube | `youtube` | 5-15min | 自然流畅、保留情感、适度剪辑 |
| 快手 | `kuaishou` | 15-60s | 接地气、情感强、节奏紧凑 |

### 获取预设

```bash
curl http://localhost:8000/api/llm/style-presets
```

---

## 🎬 字幕样式

### 预设样式

```python
# 抖音风格（粗体黄字黑边）
style="bold_yellow"

# 简洁白字
style="clean_white"

# 优雅黑字
style="elegant_black"
```

### 自定义样式

```python
custom_style = {
    "font_size": 72,
    "font_color": [1.0, 1.0, 0.0],  # RGB (黄色)
    "position": [0.5, 0.3],  # 归一化坐标
    "stroke_width": 3,
    "stroke_color": [0.0, 0.0, 0.0]
}
```

---

## 🔧 常用 API

### 1. 生成 DSL

```bash
POST /api/llm/generate-dsl
```

### 2. 验证 DSL

```bash
POST /api/llm/validate-dsl
```

### 3. 风格预设

```bash
GET /api/llm/style-presets
```

### 4. 批量生成

```bash
POST /api/llm/batch-generate
```

---

## ⚠️ 常见问题

### Q: API Key 错误？

```bash
# 检查 .env 配置
cat .env | grep OPENAI_API_KEY
```

### Q: JSON 解析失败？

使用支持 JSON 模式的模型：
- ✅ gpt-4o
- ✅ gpt-4-turbo
- ❌ gpt-3.5-turbo（不稳定）

### Q: 验证失败（AI 幻觉）？

系统会自动拦截，可以：
1. 重新生成
2. 手动修正 DSL
3. 调整风格提示词

---

## 📚 完整文档

- [LLM_INTEGRATION.md](LLM_INTEGRATION.md) - 完整指南
- [API_USAGE.md](API_USAGE.md) - API 文档
- [BRAIN_AND_RENDER.md](BRAIN_AND_RENDER.md) - 功能概览

---

## 🎯 完整工作流

```bash
# 1. 分析素材
curl -X POST http://localhost:8000/api/analyze \
  -F "edl_file=@input.edl" \
  -F "audio_file=@input.mp4"

# 2. AI 生成
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@scenes.json" \
  -F "transcript_file=@transcript.json" \
  -F "style_prompt=抖音爆款风格"

# 3. 执行剪辑
curl -X POST http://localhost:8000/api/execute \
  -F "dsl_file=@editing_dsl.json" \
  -F "scenes_file=@scenes.json"
```

---

**快速开始**: `python example_ai_workflow.py`
