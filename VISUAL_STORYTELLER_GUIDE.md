# Visual Storyteller 使用指南

## 概述

**Visual Storyteller（视觉叙事引擎）** 是 AutoCut Director 的无脚本模式，能够从零散的视觉素材中自动构思故事线。

### 核心能力

- 🧠 **智能聚类**：自动将素材按内容分组（人物、风景、物品）
- 💡 **创意构思**：提出多个可能的剪辑主题
- ✍️ **自动编剧**：生成配套的旁白或字幕文案
- 🎬 **完整输出**：生成虚拟的 transcript.json + editing_dsl.json

### 适用场景

- ✅ 有大量零散素材，不知道如何组织
- ✅ 想要快速生成多个版本的剪辑方案
- ✅ 需要 AI 辅助构思故事线
- ✅ 无脚本拍摄后的后期整理

## 工作流程

```
视觉素材（scenes_with_visual.json）
  ↓
1. 聚类分析
  - 按内容分组（人物、风景、物品）
  - 统计景别、情绪、主体
  ↓
2. 创意构思
  - 分析素材关联
  - 提出 3 个可能的主题
  - 选定最佳方案
  ↓
3. 自动编剧
  - 生成配套文案
  - 匹配画面时间点
  - 设计情绪曲线
  ↓
4. 输出
  - transcript_generated.json（虚拟脚本）
  - editing_dsl_from_story.json（剪辑指令）
```

## 使用方法

### 方法 1：Python API

```python
from app.core.visual_storyteller import VisualStoryteller
from app.models.schemas import ScenesJSON
import json

# 1. 加载场景数据（必须包含 visual 字段）
with open('scenes_with_visual.json', 'r') as f:
    scenes_dict = json.load(f)
scenes_data = ScenesJSON(**scenes_dict)

# 2. 初始化 Visual Storyteller
storyteller = VisualStoryteller()

# 3. 生成故事
story_result = storyteller.generate_story_from_visuals(
    scenes_data,
    duration_target=30,  # 目标时长（秒）
    style_preference="情感叙事"  # 可选：风格偏好
)

# 4. 查看结果
print(f"主题: {story_result['theme']}")
print(f"逻辑: {story_result['logic']}")
print(f"风格: {story_result['narrative_style']}")

# 5. 生成 DSL
dsl = storyteller.generate_dsl_from_story(
    scenes_data,
    story_result,
    platform="douyin"
)
```

### 方法 2：HTTP API

```bash
# 1. 从视觉素材创作故事
curl -X POST http://localhost:8000/api/storyteller/create-story-from-job \
  -F "job_id=job_xxx" \
  -F "duration_target=30" \
  -F "style_preference=情感叙事"

# 2. 从故事生成 DSL
curl -X POST http://localhost:8000/api/storyteller/generate-dsl-from-story \
  -F "job_id=job_xxx" \
  -F "platform=douyin"

# 3. 获取故事结果
curl http://localhost:8000/api/storyteller/story/job_xxx
```

### 方法 3：便捷函数

```python
from app.core.visual_storyteller import create_story_from_visuals

story_result = create_story_from_visuals(
    scenes_data,
    duration_target=30,
    style_preference="高燃踩点"
)
```

## 输出结果

### 1. 故事构思结果

```json
{
  "theme": "海边度假Vlog",
  "logic": "按时间顺序，从出发到日落，展现轻松愉快的氛围",
  "narrative_style": "舒缓治愈",
  "suggested_bgm_mood": "chill_hop",
  "clustering": {
    "groups": {
      "人物": ["S0001", "S0003"],
      "风景": ["S0002", "S0005"],
      "物品": ["S0004"]
    },
    "shot_types": {
      "特写": 3,
      "中景": 5,
      "全景": 2
    },
    "moods": {
      "开心": 4,
      "平静": 6
    }
  },
  "alternative_themes": [
    {
      "theme": "夏日探险记",
      "reason": "素材中有多个户外场景，适合冒险主题"
    },
    {
      "theme": "慢生活日记",
      "reason": "画面情绪平静，适合慢节奏叙事"
    }
  ]
}
```

### 2. 生成的文案（transcript_generated.json）

```json
{
  "meta": {
    "schema": "transcript.v1",
    "language": "zh"
  },
  "segments": [
    {
      "start": 0.0,
      "end": 3.0,
      "text": "阳光洒在海面上"
    },
    {
      "start": 3.0,
      "end": 8.0,
      "text": "这是我期待已久的假期"
    },
    {
      "start": 8.0,
      "end": 12.0,
      "text": "远离城市的喧嚣"
    },
    {
      "start": 12.0,
      "end": 15.0,
      "text": "在这里，时间变慢了"
    }
  ]
}
```

### 3. 剪辑指令（editing_dsl_from_story.json）

标准的 editing_dsl.v1.json 格式，可直接用于执行剪辑。

## 风格选项

### 预设风格

1. **高燃踩点**
   - 快节奏，强节奏感
   - 短句、强调、重复
   - 适合：运动、旅行、产品展示

2. **情感叙事**
   - 慢节奏，有故事线
   - 舒缓、细腻、有画面感
   - 适合：Vlog、纪录片

3. **无厘头鬼畜**
   - 快速切换，重复强调
   - 夸张、反转、吐槽
   - 适合：搞笑、吐槽

4. **氛围感**
   - 慢镜头，情绪渲染
   - 诗意、留白、意境
   - 适合：风景、美食

5. **教学讲解**
   - 逻辑清晰，分步骤
   - 清晰、分步骤
   - 适合：教程、测评

### 自定义风格

```python
story_result = storyteller.generate_story_from_visuals(
    scenes_data,
    duration_target=30,
    style_preference="科技感未来风，配合电子音乐"
)
```

## 聚类分析

### 自动分组

Visual Storyteller 会自动将素材分为三大类：

1. **人物**：包含人物的镜头
2. **风景**：自然景观（天空、海、山、树等）
3. **物品**：其他物体（产品、道具等）

### 统计信息

- **景别分布**：特写、中景、全景的数量
- **情绪分布**：开心、平静、紧张等情绪的占比
- **高频主体**：出现最多的物体或人物

## 创意构思

### AI 思考维度

1. **内容连贯性**
   - 素材之间的逻辑关系
   - 时间顺序、空间关系、因果关系

2. **情绪曲线**
   - 如何安排情绪起伏
   - 平静 → 高潮 → 收尾

3. **视觉节奏**
   - 景别如何组接
   - 全景 → 中景 → 特写

4. **故事性**
   - 能否构建简单的叙事弧
   - 开始 → 发展 → 结局

### 备选主题

AI 会提供 2-3 个备选主题，每个主题都有理由说明：

```json
{
  "alternatives": [
    {
      "theme": "夏日探险记",
      "reason": "素材中有多个户外场景，适合冒险主题"
    },
    {
      "theme": "慢生活日记",
      "reason": "画面情绪平静，适合慢节奏叙事"
    }
  ]
}
```

## 自动编剧

### 文案生成原则

1. **分段合理**：3-5 个句子，每句 3-8 秒
2. **时间标注**：每句话标注预估时间范围
3. **内容匹配**：文案与画面内容呼应
4. **情绪递进**：开场吸引 → 内容展开 → 结尾升华
5. **简洁有力**：每句话不超过 20 字

### 文案风格示例

**高燃踩点**：
```
"这就是！"
"看到了吗！"
"没错，就是这样！"
```

**情感叙事**：
```
"阳光洒在海面上..."
"这是我期待已久的假期..."
"在这里，时间变慢了..."
```

**氛围感**：
```
"时间在这里变慢了..."
"每一刻都值得珍藏..."
"这就是生活的意义..."
```

## 完整工作流示例

### 场景 1：零散旅行素材

```python
# 1. 视觉分析（前置步骤）
from app.tools.visual_analyzer import analyze_scenes_with_vision
scenes_with_visual = analyze_scenes_with_vision(scenes_data, video_path)

# 2. 创作故事
from app.core.visual_storyteller import VisualStoryteller
storyteller = VisualStoryteller()

story_result = storyteller.generate_story_from_visuals(
    scenes_with_visual,
    duration_target=60,
    style_preference="情感叙事"
)

# 3. 生成 DSL
dsl = storyteller.generate_dsl_from_story(
    scenes_with_visual,
    story_result,
    platform="bilibili"
)

# 4. 执行剪辑
from app.executor.runner import Runner
runner = Runner()
runner.execute(dsl, scenes_with_visual)
```

### 场景 2：产品拍摄素材

```python
story_result = storyteller.generate_story_from_visuals(
    scenes_with_visual,
    duration_target=30,
    style_preference="高燃踩点，产品展示"
)

# AI 会自动识别产品特写镜头
# 生成配套的产品介绍文案
# 设计快节奏的剪辑方案
```

### 场景 3：美食拍摄素材

```python
story_result = storyteller.generate_story_from_visuals(
    scenes_with_visual,
    duration_target=45,
    style_preference="氛围感，美食探店"
)

# AI 会识别食物特写、环境镜头
# 生成诱人的美食文案
# 设计慢节奏的氛围感剪辑
```

## 测试

### 运行测试套件

```bash
cd autocut-director
python test_visual_storyteller.py
```

测试内容：
1. ✅ 故事生成功能
2. ✅ DSL 生成功能
3. ✅ 多风格测试

### 预期输出

```
🎬 Visual Storyteller 启动...
  ✓ 发现 10/10 个场景有视觉数据

[1/4] 聚类分析...
  ✓ 识别到 3 个素材组

[2/4] 提取视觉摘要...

[3/4] AI 构思故事线...
  ✓ 主题: 海边度假Vlog
  ✓ 风格: 舒缓治愈

[4/4] 生成虚拟脚本...
  ✓ 生成了 4 段文案

✅ Visual Storyteller 完成！
```

## 配置

### 环境变量

```bash
# .env
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o  # 需要强推理能力
```

### 模型选择

Visual Storyteller 强制使用 `gpt-4o`，因为需要：
- 强推理能力（分析素材关联）
- 创造性（构思故事主题）
- 长上下文（处理大量场景）

## 成本估算

### API 调用

每次故事生成包含：
1. 聚类分析（本地计算，免费）
2. 故事构思（1 次 API 调用）
3. 文案生成（1 次 API 调用）
4. DSL 生成（1 次 API 调用，可选）

### 成本

- 故事生成：~$0.02-0.05
- DSL 生成：~$0.03-0.08
- 总计：~$0.05-0.13 per story

## 故障排除

### Q1: 提示 "场景数据中没有视觉信息"

**原因**：scenes.json 中没有 `visual` 字段

**解决**：先运行视觉分析
```bash
python -m app.tools.visual_analyzer video.mp4 scenes.json
```

### Q2: 生成的故事不符合预期

**原因**：素材聚类结果不理想

**解决**：
1. 检查视觉分析质量
2. 尝试不同的 `style_preference`
3. 调整 `duration_target`

### Q3: 文案时间点不准确

**原因**：AI 估算的时间可能不精确

**解决**：
1. 在 DSL 生成阶段会自动调整
2. 可以手动编辑 transcript_generated.json

### Q4: 备选主题都不满意

**原因**：素材内容单一或混乱

**解决**：
1. 增加更多视觉素材
2. 提供更明确的 `style_preference`
3. 手动编辑故事构思

## 最佳实践

### 1. 素材准备

- ✅ 确保所有场景都有视觉分析
- ✅ 素材质量评分 >= 7
- ✅ 素材内容有一定关联性

### 2. 风格选择

- ✅ 根据素材类型选择风格
- ✅ 旅行素材 → 情感叙事
- ✅ 产品素材 → 高燃踩点
- ✅ 美食素材 → 氛围感

### 3. 时长设置

- ✅ 短视频：15-30 秒
- ✅ 中视频：30-60 秒
- ✅ 长视频：60-120 秒

### 4. 结果优化

- ✅ 查看备选主题，选择最佳方案
- ✅ 根据聚类结果调整素材
- ✅ 手动微调生成的文案

## 未来计划

- [ ] 支持多语言文案生成
- [ ] 支持自定义文案模板
- [ ] 支持情绪曲线可视化
- [ ] 支持素材推荐（缺少哪些镜头）
- [ ] 支持批量生成多个版本
- [ ] 支持用户反馈学习

## 总结

Visual Storyteller 是 AutoCut Director 的创新功能：

- ✅ 无需脚本，从零散素材构思故事
- ✅ 智能聚类，自动分析素材关联
- ✅ 创意构思，提供多个主题方案
- ✅ 自动编剧，生成配套文案
- ✅ 完整输出，可直接用于剪辑

**核心价值**：
- 降低创作门槛
- 提高创作效率
- 激发创意灵感
- 快速生成多版本

**适用场景**：
- 零散素材整理
- 快速原型制作
- 创意头脑风暴
- 无脚本拍摄后期

---

**版本**: v1.9.0  
**日期**: 2026-02-05  
**状态**: ✅ Visual Storyteller 已实现
