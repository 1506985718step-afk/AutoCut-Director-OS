# Modality Analyzer 快速参考

## 🎯 核心概念

**0 号步骤：在抽帧和 ASR 之前，先判断"用耳朵听"还是"用眼睛看"**

---

## 📋 决策矩阵

| 素材类型 | 推荐模式 | Vision 频率 |
|---------|---------|-----------|
| 出镜口播 | ASR_PRIMARY | 低 |
| 教程解说 | ASR_PRIMARY | 低 |
| Vlog | HYBRID | 中 |
| 产品展示 | VISION_PRIMARY | 高 |
| B-roll | VISION_PRIMARY | 高 |
| 无声素材 | VISION_PRIMARY | 必须 |

---

## 🚀 快速使用

### 1. 分析模态

```python
from app.tools.modality_analyzer import analyze_modality

analysis = analyze_modality("video.mp4")
print(f"推荐模式: {analysis.recommended_mode}")
```

### 2. 判断是否运行 Vision

```python
from app.tools.modality_analyzer import should_run_vision

if should_run_vision(analysis, has_transcript=True, confidence=0.9):
    # 运行 Vision
    pass
```

### 3. 匹配音频

```python
from app.tools.audio_matcher import match_audio_to_videos

matches = match_audio_to_videos(videos, audios)
```

### 4. 完整流水线

```python
from app.tools.smart_pipeline import run_smart_pipeline

result = run_smart_pipeline(job_dir, input_paths)
```

---

## 🔍 Vision 运行规则

```python
# VISION_PRIMARY → 必须跑
if mode == "VISION_PRIMARY":
    return True

# ASR_PRIMARY → 只在必要时跑
if mode == "ASR_PRIMARY":
    if no_transcript or low_confidence:
        return True
    return False

# HYBRID → 选择性跑
if mode == "HYBRID":
    return high_priority_segment
```

---

## 🎵 音频匹配策略

1. **显式匹配** - A001.mp4 ↔ A001.wav
2. **时间戳匹配** - 创建时间差 < 5 分钟
3. **波形匹配** - 互相关（可选）

---

## 📊 流水线步骤

```
1. Ingest & Index
2. Quick Quality Triage
3. Match Audio to Video
4. Modality Analysis
5. Segment Assets
6A. ASR Recognition
6B. Vision Analysis (selective)
6C. Structure Vision Data
7. Generate ShotCards
```

---

## 🧪 测试

```bash
python test_modality_analyzer.py
```

---

## 💡 性能优势

- **极轻量** - < 1 秒完成分析
- **省成本** - 避免不必要的 Vision 调用
- **高准确** - 基于规则，可预测

---

## 📚 完整文档

详见：[MODALITY_ANALYZER_GUIDE.md](MODALITY_ANALYZER_GUIDE.md)
