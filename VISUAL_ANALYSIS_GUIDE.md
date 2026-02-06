# 视觉分析功能指南

## 概述

AutoCut Director 现在拥有"眼睛"了！通过 GPT-4o Vision API，AI 导演可以：

- 🎬 理解画面内容（人物、物体、场景）
- 🎨 识别景别（特写、中景、全景）
- 😊 感知情绪（开心、紧张、平静）
- 💡 评估质量（清晰度、构图、美感）

这让 AI 导演能够**智能选择镜头**，而不仅仅依赖时间顺序。

## 功能特性

### 1. 视觉元数据结构

每个场景现在可以包含 `visual` 字段：

```json
{
  "scene_id": "S0001",
  "start_frame": 0,
  "end_frame": 150,
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

### 2. 智能镜头选择

AI 导演现在可以：

#### 画面匹配内容
- 语音说"打开手机" → 选择 subjects 包含 "手机" 的镜头
- 语音说"咖啡" → 选择 summary 包含 "咖啡" 的镜头

#### 情绪流控制
- 激昂的语音 → 配 mood 积极、action 强烈的画面
- 平静的讲解 → 配 mood 平静、lighting 柔和的画面

#### 景别组接（蒙太奇）
- 避免同景别跳接（Jump Cut）
- 尝试 "全景 → 中景 → 特写" 的递进
- 或 "特写 → 全景" 的对比

#### Hook 设计
- 开场使用 quality_score 最高的镜头
- 优先选择 shot_type 为 "特写" 或 "近景" 的冲击力画面

#### 质量优先
- 优先使用 quality_score >= 7 的镜头
- 避免使用 lighting 为 "过曝" 或 "暗调" 的低质量画面

## 使用方法

### 方法 1：独立工具

```bash
# 为现有的 scenes.json 添加视觉分析
python -m app.tools.visual_analyzer video.mp4 scenes.json

# 输出: scenes_with_visual.json
```

### 方法 2：Python API

```python
from app.tools.visual_analyzer import VisualAnalyzer
from app.models.schemas import ScenesJSON
import json

# 加载场景数据
with open('scenes.json', 'r') as f:
    scenes_dict = json.load(f)
scenes_data = ScenesJSON(**scenes_dict)

# 分析视觉
analyzer = VisualAnalyzer()
updated_scenes = analyzer.analyze_scene_visuals(
    scenes_data,
    video_path='video.mp4',
    max_scenes=None  # None = 分析所有场景
)

# 保存结果
with open('scenes_with_visual.json', 'w') as f:
    json.dump(updated_scenes.model_dump(), f, indent=2, ensure_ascii=False)
```

### 方法 3：集成到工作流

```python
from app.tools.visual_analyzer import analyze_scenes_with_vision
from app.core.llm_engine import LLMDirector

# 1. 分析视觉
scenes_with_visual = analyze_scenes_with_vision(scenes_data, video_path)

# 2. 生成 DSL（AI 导演会利用视觉信息）
director = LLMDirector()
dsl = director.generate_editing_dsl(
    scenes=scenes_with_visual,  # 包含视觉信息
    transcript=transcript_data,
    style_prompt="抖音爆款风格"
)
```

## 测试

### 运行测试套件

```bash
cd autocut-director
python test_visual_analyzer.py
```

测试内容：
1. ✅ 视觉分析功能
2. ✅ 视觉数据统计
3. ✅ DSL 增强验证

### 预期输出

```
👁️  开始视觉分析: 5 个场景
  > 分析 S0001 (T=2.5s)... ✅ [中景] 年轻人在咖啡厅使用笔记本电脑
  > 分析 S0002 (T=7.3s)... ✅ [特写] 手指在键盘上打字
  > 分析 S0003 (T=12.1s)... ✅ [全景] 咖啡厅内部环境

✅ 视觉分析完成: 3/5 个场景
```

## 配置

### 环境变量

在 `.env` 文件中：

```bash
# OpenAI API Key（必需）
OPENAI_API_KEY=sk-your-api-key-here

# 可选：自定义 API 端点
OPENAI_BASE_URL=https://api.openai.com/v1
```

### 模型选择

视觉分析器强制使用 `gpt-4o`（支持视觉的模型）。

### 成本控制

- 使用 `detail="low"` 降低成本（每张图约 $0.001）
- 使用 `max_scenes` 参数限制分析数量
- 只分析关键场景（如 Hook、CTA）

## 性能优化

### 1. 批量处理

```python
# 限制分析数量（调试用）
analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes=10)
```

### 2. 缓存结果

视觉分析结果会保存在 `scenes.json` 中，避免重复分析：

```python
# 如果场景已有 visual 字段，会自动跳过
if scene.visual:
    continue
```

### 3. 并行处理（未来）

可以使用 `asyncio` 并行调用 Vision API，提高速度。

## 示例场景

### 输入：scenes.json

```json
{
  "meta": {
    "schema": "scenes.v1",
    "fps": 30,
    "source": "davinci/edl"
  },
  "media": {
    "primary_clip_path": "D:/Videos/tutorial.mp4"
  },
  "scenes": [
    {
      "scene_id": "S0001",
      "start_frame": 0,
      "end_frame": 150,
      "start_tc": "00:00:00:00",
      "end_tc": "00:00:05:00"
    }
  ]
}
```

### 输出：scenes_with_visual.json

```json
{
  "meta": {
    "schema": "scenes.v1",
    "fps": 30,
    "source": "davinci/edl"
  },
  "media": {
    "primary_clip_path": "D:/Videos/tutorial.mp4"
  },
  "scenes": [
    {
      "scene_id": "S0001",
      "start_frame": 0,
      "end_frame": 150,
      "start_tc": "00:00:00:00",
      "end_tc": "00:00:05:00",
      "visual": {
        "summary": "讲师在白板前讲解",
        "shot_type": "中景",
        "subjects": ["人物", "白板", "马克笔"],
        "action": "讲解",
        "mood": "专业",
        "lighting": "室内",
        "quality_score": 8
      }
    }
  ]
}
```

## AI 导演的视觉理解

### Prompt 增强

LLM Director 的 system prompt 现在包含：

```
🎯 核心能力升级：你现在拥有"视觉理解"能力！

Scenes 数据中包含了 `visual` 字段（景别、内容描述、情绪、主体）。
请充分利用这些信息来匹配剪辑逻辑，而不仅仅依赖时间顺序或随机选择。

剪辑逻辑指南：
1. 画面匹配内容
2. 情绪流控制
3. 景别组接（蒙太奇原则）
4. Hook 设计（前 3 秒）
5. 质量优先
```

### 实际效果

**之前**（无视觉信息）：
- AI 按时间顺序选择镜头
- 可能选到低质量画面
- 画面与语音内容不匹配

**之后**（有视觉信息）：
- AI 根据语音内容选择匹配的画面
- 优先使用高质量镜头
- 遵循蒙太奇原则组接
- Hook 使用最具冲击力的画面

## 故障排除

### Q1: 提示 "OPENAI_API_KEY not configured"

**解决**：在 `.env` 文件中配置 API Key

```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### Q2: 提示 "Frame extraction failed"

**原因**：FFmpeg 未安装或视频文件损坏

**解决**：
1. 安装 FFmpeg：`winget install FFmpeg`
2. 检查视频文件是否完整

### Q3: 提示 "Vision API error"

**原因**：API 调用失败（网络、配额、模型不支持）

**解决**：
1. 检查网络连接
2. 检查 API 配额
3. 确保使用 `gpt-4o` 模型

### Q4: 分析速度慢

**原因**：每个场景需要截帧 + API 调用

**优化**：
1. 使用 `max_scenes` 限制数量
2. 只分析关键场景
3. 使用 `detail="low"` 降低成本

## 最佳实践

### 1. 选择性分析

不是所有场景都需要视觉分析：

```python
# 只分析前 10 个场景（Hook 区域）
analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes=10)
```

### 2. 增量分析

如果场景已有视觉数据，会自动跳过：

```python
# 第一次：分析所有场景
scenes_v1 = analyzer.analyze_scene_visuals(scenes_data, video_path)

# 第二次：只分析新增场景
scenes_v2 = analyzer.analyze_scene_visuals(scenes_v1, video_path)
```

### 3. 质量过滤

在 DSL 生成时，可以过滤低质量场景：

```python
# 只使用高质量场景
high_quality_scenes = [
    scene for scene in scenes_data.scenes
    if scene.visual and scene.visual.quality_score >= 7
]
```

## 未来计划

- [ ] 支持批量并行分析（提高速度）
- [ ] 支持自定义视觉标签（如"产品特写"、"人物表情"）
- [ ] 支持视频摘要（自动生成封面图）
- [ ] 支持场景相似度匹配（找相似镜头）
- [ ] 支持动作识别（如"挥手"、"点头"）

## 总结

视觉分析功能让 AutoCut Director 从"盲剪"升级为"智能剪辑"：

- ✅ AI 导演能"看懂"画面
- ✅ 根据内容智能选择镜头
- ✅ 遵循专业剪辑原则
- ✅ 提高成片质量

**关键优势**：
- 画面与语音内容匹配
- 情绪流控制
- 景别组接优化
- 质量优先选择

---

**版本**: v1.8.0  
**日期**: 2026-02-05  
**状态**: ✅ 视觉分析功能已实现
