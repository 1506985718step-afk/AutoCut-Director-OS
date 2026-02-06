# LM Studio 集成指南

## 概述

LM Studio 是一个友好的本地 AI 模型管理工具，支持视觉模型（LLaVA 等）。AutoCut Director v2.0 已完整集成 LM Studio 作为本地视觉分析的替代方案。

### 为什么选择 LM Studio？

1. **友好的 UI 界面** - 图形化管理，无需命令行
2. **OpenAI 兼容 API** - 标准接口，易于集成
3. **自动 GPU 加速** - 自动检测并使用 GPU
4. **模型管理简单** - 一键下载、加载模型
5. **零配置启动** - 启动即用，无需复杂设置

### LM Studio vs Ollama

| 特性 | LM Studio | Ollama |
|------|-----------|--------|
| UI 界面 | ✓ 图形化 | ✗ 命令行 |
| 模型管理 | ✓ 一键下载 | 需手动 pull |
| GPU 加速 | ✓ 自动 | ✓ 自动 |
| API 兼容 | OpenAI 格式 | 自定义格式 |
| 适合人群 | 所有用户 | 技术用户 |

---

## 安装步骤

### 1. 下载 LM Studio

访问官网下载：https://lmstudio.ai/

- Windows: 下载 `.exe` 安装包
- macOS: 下载 `.dmg` 安装包
- Linux: 下载 `.AppImage` 文件

### 2. 安装并启动

1. 运行安装程序
2. 启动 LM Studio
3. 首次启动会自动配置环境

---

## 模型下载

### 推荐模型（按优先级）

#### 1. Moondream2 (1.5GB) - 🌟 首选
- **优点**: 极快、超轻量、专为边缘设备设计
- **速度**: CPU 模式下 2-3秒/场景
- **适合**: 所有用户，特别是无独显用户
- **搜索**: 在 LM Studio 中搜索 `moondream`
- **模型**: `vikhyatk/moondream2` (1.8B 参数，1.5GB)

#### 2. LLaVA-Phi-3 (2.5GB) - 推荐
- **优点**: 微软 Phi3 架构，逻辑性比 Moondream 好
- **速度**: CPU 模式下 4-6秒/场景
- **适合**: 需要更好逻辑推理的场景
- **搜索**: 在 LM Studio 中搜索 `llava-phi-3`
- **模型**: `xtuner/llava-phi-3-mini` (3.8B 参数，2.5GB)

#### 3. MiniCPM-V (5GB) - 不推荐
- **说明**: 性能虽好，但体积较大，不适合边缘设备
- **仅适合**: 有 8GB+ 显存且追求极致质量的用户

### 下载步骤

1. 打开 LM Studio
2. 点击左侧 "🔍 Search" 标签
3. 搜索 `moondream` （首选）或 `llava-phi-3`
4. 选择推荐的模型：
   - **首选**: `vikhyatk/moondream2` (1.5GB)
   - **次选**: `xtuner/llava-phi-3-mini` (2.5GB)
5. 点击 "Download" 下载
6. 等待下载完成（Moondream 只需 1-2 分钟）

---

## 启动本地服务器

### 1. 加载模型

1. 点击左侧 "💬 Chat" 标签
2. 点击顶部 "Select a model to load"
3. 选择已下载的模型（推荐 Moondream2）
4. 等待模型加载完成（Moondream2 加载很快，通常 5-10 秒）

### 2. 启动服务器

1. 点击左侧 "↔️ Local Server" 标签
2. 确保端口设置为 `1234`（默认）
3. 点击 "Start Server" 按钮
4. 看到 "Server running on http://localhost:1234" 表示成功

### 3. 验证服务

打开浏览器访问：http://localhost:1234/v1/models

应该看到类似以下的 JSON 响应：
```json
{
  "data": [
    {
      "id": "vikhyatk/moondream2",
      "object": "model",
      ...
    }
  ]
}
```

---

## 配置 AutoCut Director

### 1. 修改 `.env` 文件

```bash
# 本地视觉模型配置
USE_LOCAL_VISION=True
LOCAL_VISION_PROVIDER=lmstudio  # 改为 lmstudio
LOCAL_VISION_MODEL=auto         # auto 表示使用当前加载的模型

# LM Studio 配置
LMSTUDIO_HOST=http://localhost:1234/v1
LMSTUDIO_MODEL=auto
```

### 2. 重启服务器

如果服务器正在运行，需要重启：

```powershell
# 停止当前服务器（Ctrl+C）
# 然后重新启动
python run_server.py
```

---

## 测试集成

### 运行测试脚本

```powershell
python test_lmstudio.py
```

### 预期输出

```
🧪 LM Studio 集成测试

============================================================
测试 1: LM Studio 连接
============================================================
✓ LM Studio 可用
✓ 当前加载的模型: vikhyatk/moondream2

============================================================
测试 2: 运行时配置检测
============================================================

🧠 系统运行模式
- 未检测到独立显卡
- CPU: 24 线程 (ultra 性能)
- 内存: 31.8GB (可用 25.3GB)
- 本地 AI (LM Studio): vikhyatk/moondream2

📊 运行级别: LOCAL_CPU_ONLY

============================================================
测试 3: 执行策略
============================================================

策略说明: 纯 CPU 配置，本地 LM Studio 视觉分析 + 云端规划

视觉分析配置:
  Provider: local
  Backend: lmstudio
  Model: vikhyatk/moondream2
  Device: cpu
  Max Scenes: 10

✓ 所有测试完成
```

---

## 使用示例

### 1. 自动选择（推荐）

系统会根据 Runtime Profile 自动选择最佳配置：

```python
from app.tools.visual_analyzer_factory import analyze_scenes_auto

# 自动选择分析器（会使用 LM Studio）
result = analyze_scenes_auto(
    scenes_data=scenes,
    video_path="video.mp4",
    use_policy=True  # 使用执行策略
)
```

### 2. 强制使用 LM Studio

```python
from app.tools.visual_analyzer_lmstudio import LMStudioVisualAnalyzer

analyzer = LMStudioVisualAnalyzer()

# 分析单张图片
description = analyzer.analyze_image(
    "frame.jpg",
    prompt="Describe this video frame for editing purposes."
)

# 分析场景
result = analyzer.analyze_scene_visuals(
    scenes_data=scenes,
    video_path="video.mp4",
    max_scenes=10
)
```

### 3. 通过 API

```bash
# 使用默认配置（会自动使用 LM Studio）
curl -X POST http://localhost:8787/api/visual/analyze \
  -F "video=@video.mp4" \
  -F "scenes=@scenes.json"
```

---

## 性能优化

### CPU 模式优化

如果没有独立显卡，LM Studio 会自动使用 CPU：

1. **首选 Moondream2**: 专为边缘设备设计，CPU 模式下极快（2-3秒/场景）
2. **限制场景数**: 设置 `max_scenes=10-15`（Moondream2 可以处理更多）
3. **次选 LLaVA-Phi-3**: 如需更好逻辑推理（4-6秒/场景）

### GPU 加速

如果有独立显卡，LM Studio 会自动使用：

1. **Moondream2 + GPU**: 速度可达 0.5-1秒/场景，极致性能
2. **调整批处理**: 可以增加 `max_scenes=20-30`
3. **LLaVA-Phi-3 + GPU**: 如需更好逻辑推理（1-2秒/场景）

---

## 故障排查

### 问题 1: LM Studio 不可用

**症状**: 测试显示 "LM Studio 不可用"

**解决方案**:
1. 确认 LM Studio 已启动
2. 确认已加载视觉模型
3. 确认本地服务器已启动（端口 1234）
4. 检查防火墙设置

### 问题 2: 模型加载失败

**症状**: 无法加载模型或加载很慢

**解决方案**:
1. 检查内存是否充足（Moondream2 只需 3-4GB 总内存）
2. 尝试重启 LM Studio
3. 优先使用 Moondream2（最轻量，1.5GB）

### 问题 3: 分析速度慢

**症状**: 每个场景分析需要很长时间

**解决方案**:
1. **首选 Moondream2**（专为速度优化，CPU 模式下 2-3秒/场景）
2. 减少 `max_scenes` 数量
3. 如果有 GPU，确保 LM Studio 正在使用 GPU
4. 考虑使用云端模式（设置 `USE_LOCAL_VISION=False`）

### 问题 4: 端口冲突

**症状**: 服务器启动失败，提示端口被占用

**解决方案**:
1. 在 LM Studio 中更改端口（如 1235）
2. 更新 `.env` 中的 `LMSTUDIO_HOST`
3. 或者关闭占用 1234 端口的其他程序

---

## 切换回 Ollama

如果想切换回 Ollama：

1. 修改 `.env`:
```bash
LOCAL_VISION_PROVIDER=ollama
```

2. 重启服务器

系统会自动切换到 Ollama。

---

## 成本对比

### LM Studio（本地）
- **成本**: 零
- **速度**: 取决于硬件（CPU: 5-10秒/场景，GPU: 1-3秒/场景）
- **质量**: 中等到高（取决于模型）
- **适合**: 所有用户

### GPT-4o（云端）
- **成本**: $0.005/图片（约 ¥0.035/图片）
- **速度**: 2-3秒/场景
- **质量**: 最高
- **适合**: 对质量要求极高的用户

### 推荐策略

- **日常使用**: LM Studio（零成本）
- **重要项目**: GPT-4o（最高质量）
- **混合模式**: 先用 LM Studio 快速预览，重要场景用 GPT-4o

---

## 常见问题

### Q: LM Studio 和 Ollama 可以同时使用吗？

A: 可以。系统会根据配置自动选择。如果两者都可用，优先使用配置文件中指定的 `LOCAL_VISION_PROVIDER`。

### Q: 需要什么样的硬件？

A: 
- **最低**: 4GB 内存 + CPU（可以运行 Moondream2，1.5GB）
- **推荐**: 8GB 内存 + CPU（可以运行 LLaVA-Phi-3，2.5GB）
- **最佳**: 16GB 内存 + 4GB+ 显存（GPU 加速，速度提升 5-10 倍）

### Q: 分析质量如何？

A: 
- **Moondream2**: 速度极快，质量中等，适合快速预览和大批量处理
- **LLaVA-Phi-3**: 逻辑性更好，质量接近 GPT-4o，适合需要精准理解的场景
- **对于剪辑**: 两者都足够使用，Moondream2 性价比最高

### Q: 可以离线使用吗？

A: 可以。模型下载后，LM Studio 完全离线运行。只有 Planning（规划）功能需要联网（使用 DeepSeek API）。

---

## 下一步

- 阅读 [RUNTIME_PROFILE_GUIDE.md](RUNTIME_PROFILE_GUIDE.md) 了解自适应策略
- 阅读 [VISUAL_ANALYSIS_GUIDE.md](VISUAL_ANALYSIS_GUIDE.md) 了解视觉分析
- 阅读 [MODALITY_ANALYZER_GUIDE.md](MODALITY_ANALYZER_GUIDE.md) 了解模态分析

---

## 技术支持

如有问题，请查看：
1. LM Studio 官方文档: https://lmstudio.ai/docs
2. 项目 GitHub Issues
3. 运行 `python test_lmstudio.py` 进行诊断
