# LM Studio 快速参考

## 一分钟启动

```bash
# 1. 下载并安装 LM Studio
https://lmstudio.ai/

# 2. 在 LM Studio 中下载模型（首选 Moondream2）
搜索: moondream
下载: vikhyatk/moondream2 (1.5GB) - 极快！

# 3. 启动服务器
LM Studio → Local Server → Start Server (端口 1234)

# 4. 配置 AutoCut Director
编辑 .env:
  LOCAL_VISION_PROVIDER=lmstudio

# 5. 测试
python test_lmstudio.py
```

---

## 配置速查

### .env 配置

```bash
# 使用 LM Studio
USE_LOCAL_VISION=True
LOCAL_VISION_PROVIDER=lmstudio
LMSTUDIO_HOST=http://localhost:1234/v1
LMSTUDIO_MODEL=auto

# 使用 Ollama
USE_LOCAL_VISION=True
LOCAL_VISION_PROVIDER=ollama
LOCAL_VISION_MODEL=moondream

# 使用云端
USE_LOCAL_VISION=False
```

---

## 推荐模型

| 模型 | 大小 | 速度 | 质量 | 适合 |
|------|------|------|------|------|
| Moondream2 🌟 | 1.5GB | 极快 | 中 | 所有用户（首选） |
| LLaVA-Phi-3 | 2.5GB | 快 | 高 | 需要更好逻辑推理 |
| MiniCPM-V | 5GB | 中 | 最高 | 8GB+ 显存（不推荐） |

**推荐策略**: 
- 无独显/低配置 → Moondream2（专为边缘设备设计）
- 需要逻辑推理 → LLaVA-Phi-3（微软 Phi3 架构）
- 追求极致质量 → 云端 GPT-4o

---

## 代码示例

### 自动选择（推荐）

```python
from app.tools.visual_analyzer_factory import analyze_scenes_auto

result = analyze_scenes_auto(
    scenes_data=scenes,
    video_path="video.mp4",
    use_policy=True  # 自动选择最佳配置
)
```

### 强制使用 LM Studio

```python
from app.tools.visual_analyzer_lmstudio import LMStudioVisualAnalyzer

analyzer = LMStudioVisualAnalyzer()
result = analyzer.analyze_scene_visuals(scenes, "video.mp4")
```

### 检查可用性

```python
analyzer = LMStudioVisualAnalyzer()
if analyzer.is_available():
    model = analyzer.get_loaded_model()
    print(f"使用模型: {model}")
```

---

## API 端点

### 检查服务状态

```bash
curl http://localhost:1234/v1/models
```

### 分析图片

```bash
curl -X POST http://localhost:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "auto",
    "messages": [{
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this image"},
        {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
      ]
    }]
  }'
```

---

## 性能参考

### CPU 模式（无独显）
- Moondream2: 2-3秒/场景 🌟 极快
- LLaVA-Phi-3: 4-6秒/场景

### GPU 模式（4GB+ 显存）
- Moondream2: 0.5-1秒/场景 🚀 极致性能
- LLaVA-Phi-3: 1-2秒/场景
- MiniCPM-V: 2-4秒/场景

---

## 故障排查

### LM Studio 不可用
```bash
# 检查服务
curl http://localhost:1234/v1/models

# 如果失败：
# 1. 确认 LM Studio 已启动
# 2. 确认已加载模型
# 3. 确认服务器已启动
```

### 端口冲突
```bash
# 更改 LM Studio 端口（如 1235）
# 然后更新 .env:
LMSTUDIO_HOST=http://localhost:1235/v1
```

### 内存不足
```bash
# 使用 Moondream2（只需 1.5GB，最轻量）
# 或减少场景数:
max_scenes=5
```

---

## 运行时策略

系统会根据硬件自动选择策略：

| 硬件配置 | 策略 | 说明 |
|----------|------|------|
| 无独显 + LM Studio | 本地 CPU | 使用 LM Studio (CPU) |
| 无独显 + 无本地 AI | 云端 | 使用 GPT-4o |
| 低端 GPU + LM Studio | 本地 CPU | 使用 LM Studio (CPU) |
| 中端 GPU + LM Studio | 本地 GPU | 使用 LM Studio (GPU) |
| 高端 GPU + LM Studio | 本地 GPU | 使用 LM Studio (GPU) |

---

## 成本对比

| 方案 | 10个场景 | 100个场景 | 1000个场景 |
|------|----------|-----------|------------|
| LM Studio | ¥0 | ¥0 | ¥0 |
| GPT-4o | ¥0.35 | ¥3.5 | ¥35 |

---

## 相关文档

- [LMSTUDIO_SETUP_GUIDE.md](LMSTUDIO_SETUP_GUIDE.md) - 完整安装指南
- [RUNTIME_PROFILE_GUIDE.md](RUNTIME_PROFILE_GUIDE.md) - 运行时配置
- [VISUAL_ANALYSIS_GUIDE.md](VISUAL_ANALYSIS_GUIDE.md) - 视觉分析
