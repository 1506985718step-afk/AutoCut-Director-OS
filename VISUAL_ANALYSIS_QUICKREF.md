# 视觉分析快速参考

## 一句话总结

让 AI 导演能"看懂"画面，根据内容智能选择镜头。

## 快速开始

### 1. 独立使用

```bash
python -m app.tools.visual_analyzer video.mp4 scenes.json
```

### 2. Python API

```python
from app.tools.visual_analyzer import analyze_scenes_with_vision

scenes_with_visual = analyze_scenes_with_vision(scenes_data, video_path)
```

### 3. HTTP API

```bash
curl -X POST http://localhost:8000/api/visual/analyze-from-job \
  -F "job_id=job_xxx"
```

## 视觉元数据结构

```json
{
  "visual": {
    "summary": "年轻人在咖啡厅使用笔记本电脑",
    "shot_type": "中景",
    "subjects": ["人物", "笔记本电脑", "咖啡杯"],
    "action": "工作",
    "mood": "专注",
    "lighting": "自然光",
    "quality_score": 8
  }
}
```

## AI 导演如何使用

### 画面匹配内容
语音说"手机" → 选择 subjects 包含 "手机" 的镜头

### 情绪流控制
激昂语音 → 配 mood 积极、action 强烈的画面

### 景别组接
避免 Jump Cut，尝试 "全景 → 中景 → 特写"

### Hook 设计
开场使用 quality_score 最高的镜头

### 质量优先
优先使用 quality_score >= 7 的镜头

## 配置

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
```

## 成本

- 每张图片：~$0.001
- 10 个场景：~$0.01

## 测试

```bash
python test_visual_analyzer.py
```

## 文档

详细指南：[VISUAL_ANALYSIS_GUIDE.md](VISUAL_ANALYSIS_GUIDE.md)

---

**版本**: v1.8.0 | **日期**: 2026-02-05
