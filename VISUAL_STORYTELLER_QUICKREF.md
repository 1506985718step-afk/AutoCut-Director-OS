# Visual Storyteller 快速参考

## 一句话总结

从零散视觉素材自动构思故事，无需脚本即可生成完整剪辑方案。

## 快速开始

### 1. Python API

```python
from app.core.visual_storyteller import create_story_from_visuals

story_result = create_story_from_visuals(
    scenes_with_visual,
    duration_target=30,
    style_preference="情感叙事"
)
```

### 2. HTTP API

```bash
curl -X POST http://localhost:8000/api/storyteller/create-story-from-job \
  -F "job_id=job_xxx" \
  -F "duration_target=30" \
  -F "style_preference=情感叙事"
```

## 工作流程

```
视觉素材 → 聚类分析 → 创意构思 → 自动编剧 → 输出
```

## 输出结果

- `story_result.json` - 故事构思
- `transcript_generated.json` - 虚拟脚本
- `editing_dsl_from_story.json` - 剪辑指令

## 风格选项

- **高燃踩点** - 快节奏，强节奏感
- **情感叙事** - 慢节奏，有故事线
- **无厘头鬼畜** - 快速切换，重复强调
- **氛围感** - 慢镜头，情绪渲染
- **教学讲解** - 逻辑清晰，分步骤

## 前置条件

```bash
# 必须先运行视觉分析
python -m app.tools.visual_analyzer video.mp4 scenes.json
```

## 配置

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
```

## 成本

- 每次故事生成：~$0.05-0.13
- 包含：聚类 + 构思 + 编剧 + DSL

## 测试

```bash
python test_visual_storyteller.py
```

## 适用场景

✅ 零散素材整理  
✅ 快速原型制作  
✅ 创意头脑风暴  
✅ 无脚本拍摄后期

## 文档

详细指南：[VISUAL_STORYTELLER_GUIDE.md](VISUAL_STORYTELLER_GUIDE.md)

---

**版本**: v1.9.0 | **日期**: 2026-02-05
