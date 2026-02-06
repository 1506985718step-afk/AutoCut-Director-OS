# 两条铁律 - AutoCut Director 核心约束

## 🎯 为什么需要铁律？

在 AI 驱动的视频剪辑系统中，必须有**硬性约束**来防止：
1. AI 幻觉（生成不存在的素材）
2. 坐标混乱（timecode 和 frame 混用）
3. 执行失败（无法在 Resolve 中实现）

这两条铁律是系统稳定运行的**基石**。

---

## 🔴 铁律 1: 不允许"未提供素材库却要求素材调用"

### 问题场景

AI 可能会"幻想"不存在的 B-roll 素材：

```json
{
  "timeline": [
    {
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": [10, 90],
      "broll": ["product_closeup.mp4", "user_testimonial.mp4"]  // ❌ 这些素材不存在
    }
  ]
}
```

**后果**:
- Resolve 执行时找不到文件
- 流水线中断
- 用户体验差

---

### 铁律内容

**规则**: 如果没有提供 B-roll 素材库，`broll` 字段**必须为空数组** `[]`

**验证逻辑**:
```python
# app/models/schemas.py
if broll:
    if not broll_library:
        # 违反铁律 1
        errors.append(
            f"铁律 1 违反 - 要求 B-roll 素材 {broll}，但未提供素材库。"
            f"必须降级为 broll: [] + assumptions"
        )
```

---

### 正确做法 ✅

**场景**: 没有 B-roll 素材库

```json
{
  "editing_plan": {
    "timeline": [
      {
        "order": 1,
        "scene_id": "S0001",
        "trim_frames": [10, 90],
        "purpose": "hook",
        "overlay_text": "第一步就错了",
        "broll": []  // ✅ 没有素材库，必须为空
      }
    ]
  },
  "assumptions": [
    "建议添加产品特写 B-roll 增强视觉效果",
    "建议添加用户使用场景 B-roll 提升代入感"
  ]
}
```

**说明**:
- `broll: []` - 明确表示不使用 B-roll
- `assumptions` - 记录建议，供后续优化

---

### 降级策略

当需要 B-roll 但没有素材库时：

1. **设置 `broll: []`**
2. **在 `assumptions` 中说明建议**
3. **通过其他方式增强表现力**:
   - 增加 `overlay_text` 文字叠加
   - 优化字幕样式
   - 调整剪辑节奏

---

### 有素材库的情况

**场景**: 提供了 B-roll 素材库

```python
# 素材库
broll_library = [
    "product_closeup.mp4",
    "user_testimonial.mp4",
    "factory_tour.mp4"
]

# DSL 验证
DSLValidator.validate_dsl_against_scenes(
    dsl, 
    scenes_data, 
    broll_library=broll_library  # 提供素材库
)
```

**DSL**:
```json
{
  "timeline": [
    {
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": [10, 90],
      "broll": ["product_closeup.mp4"]  // ✅ 素材库中存在
    }
  ]
}
```

---

## 🔴 铁律 2: 坐标体系统一 - 内部只用 frame

### 问题场景

混用 timecode 和 frame 会导致：

```json
{
  "timeline": [
    {
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": ["00:00:01:00", "00:00:04:00"]  // ❌ 使用了 timecode
    }
  ]
}
```

**后果**:
- 类型不一致（字符串 vs 整数）
- 换算错误（不同 fps 下 timecode 含义不同）
- 代码复杂度增加

---

### 铁律内容

**规则**: 
1. **内部执行只用 frame**（整数帧号）
2. **对外展示可附带 TC**（timecode，仅用于可读性）
3. **scenes.json 必须带 fps**，validator 用它统一换算

**验证逻辑**:
```python
# app/models/schemas.py
if not isinstance(trim_start, int) or not isinstance(trim_end, int):
    errors.append(
        f"铁律 2 违反 - trim_frames 必须是整数帧号，不能是 timecode"
    )
```

---

### 正确做法 ✅

**scenes.json** - 必须包含 fps:
```json
{
  "meta": {
    "schema": "scenes.v1",
    "fps": 30,  // ✅ 必须提供 fps
    "source": "davinci/edl"
  },
  "scenes": [
    {
      "scene_id": "S0001",
      "start_frame": 0,      // ✅ 使用 frame
      "end_frame": 120,      // ✅ 使用 frame
      "start_tc": "00:00:00:00",  // 可选，仅用于展示
      "end_tc": "00:00:04:00"     // 可选，仅用于展示
    }
  ]
}
```

**editing_dsl.json** - 只用 frame:
```json
{
  "editing_plan": {
    "timeline": [
      {
        "order": 1,
        "scene_id": "S0001",
        "trim_frames": [30, 120]  // ✅ 整数帧号
      }
    ]
  }
}
```

---

### 换算工具

**Frame → Timecode** (用于展示):
```python
# app/models/schemas.py
def frames_to_timecode(frame: int, fps: float) -> str:
    """将帧号转换为 timecode（用于对外展示）"""
    total_seconds = frame / fps
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    frames = int(frame % fps)
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

# 示例
frames_to_timecode(120, 30)  # → "00:00:04:00"
```

**Timecode → Frame** (用于输入):
```python
def timecode_to_frames(timecode: str, fps: float) -> int:
    """将 timecode 转换为帧号（用于输入处理）"""
    hours, minutes, seconds, frames = map(int, timecode.split(":"))
    
    total_frames = (
        hours * 3600 * fps +
        minutes * 60 * fps +
        seconds * fps +
        frames
    )
    
    return int(total_frames)

# 示例
timecode_to_frames("00:00:04:00", 30)  # → 120
```

---

### 为什么只用 frame？

| 方面 | Frame | Timecode |
|------|-------|----------|
| **类型** | 整数 | 字符串 |
| **精度** | 精确到帧 | 精确到帧 |
| **计算** | 简单（加减乘除） | 复杂（需要解析） |
| **fps 依赖** | 无（绝对值） | 有（相对值） |
| **存储** | 4 字节 | 11 字节 |
| **比较** | 直接比较 | 需要转换 |

**结论**: Frame 更适合内部计算，Timecode 仅用于展示

---

### 不同 fps 下的换算

| fps | 1 秒 | 4 秒 | 1 分钟 |
|-----|------|------|--------|
| 24 | 24 帧 | 96 帧 | 1440 帧 |
| 25 | 25 帧 | 100 帧 | 1500 帧 |
| 30 | 30 帧 | 120 帧 | 1800 帧 |
| 60 | 60 帧 | 240 帧 | 3600 帧 |

**示例**:
- 30fps: trim_frames [30, 120] = 1-4 秒
- 60fps: trim_frames [60, 240] = 1-4 秒

**注意**: 相同的 timecode "00:00:01:00" 在不同 fps 下对应不同的帧号！

---

## 🔧 验证流程

### 1. scenes.json 验证

```python
from app.models.schemas import DSLValidator

# 检查 fps
if not DSLValidator.validate_scenes_has_fps(scenes_data):
    raise ValueError("铁律 2 违反: scenes.json 必须包含 fps")
```

### 2. DSL 验证

```python
# 完整验证（包含两条铁律）
errors = DSLValidator.validate_dsl_against_scenes(
    dsl=dsl_data,
    scenes_data=scenes_data,
    broll_library=None  # 没有素材库
)

if errors:
    print("验证失败:")
    for err in errors:
        print(f"  - {err}")
```

---

## 📊 验证示例

### 示例 1: 违反铁律 1

**DSL**:
```json
{
  "timeline": [
    {
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": [10, 90],
      "broll": ["product.mp4"]  // ❌ 没有素材库
    }
  ]
}
```

**验证结果**:
```
❌ Timeline item 1: 铁律 1 违反 - 要求 B-roll 素材 ['product.mp4']，但未提供素材库。必须降级为 broll: [] + assumptions
```

---

### 示例 2: 违反铁律 2

**DSL**:
```json
{
  "timeline": [
    {
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": ["00:00:01:00", "00:00:04:00"]  // ❌ 使用了 timecode
    }
  ]
}
```

**验证结果**:
```
❌ Timeline item 1: 铁律 2 违反 - trim_frames 必须是整数帧号，不能是 timecode
```

---

### 示例 3: 全部通过 ✅

**scenes.json**:
```json
{
  "meta": {
    "schema": "scenes.v1",
    "fps": 30
  },
  "scenes": [
    {
      "scene_id": "S0001",
      "start_frame": 0,
      "end_frame": 120
    }
  ]
}
```

**DSL**:
```json
{
  "editing_plan": {
    "timeline": [
      {
        "order": 1,
        "scene_id": "S0001",
        "trim_frames": [10, 90],
        "broll": []
      }
    ]
  }
}
```

**验证结果**:
```
✅ 验证通过！
```

---

## 🎯 最佳实践

### 1. LLM 提示词

在 LLM 提示词中明确强调两条铁律：

```python
system_prompt = """
你是专业的短视频剪辑导演。

🔴 铁律 1: 如果没有素材库，broll 必须为 []
🔴 铁律 2: trim_frames 必须使用整数帧号

硬规则：
- scene_id 必须存在于 scenes 中
- trim_frames 必须在场景范围内
- trim_frames[0] < trim_frames[1]
"""
```

### 2. 验证流程

```python
# 1. 验证 scenes.json
if not DSLValidator.validate_scenes_has_fps(scenes_data):
    raise ValueError("scenes.json 必须包含 fps")

# 2. 验证 DSL
errors = DSLValidator.validate_dsl_against_scenes(
    dsl, scenes_data, broll_library=None
)

if errors:
    # 记录错误，拒绝执行
    log_errors(errors)
    raise ValidationError(errors)

# 3. 执行
run_actions(actions)
```

### 3. 错误处理

```python
try:
    errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
    if errors:
        # 返回详细错误信息
        return {
            "status": "validation_failed",
            "errors": errors,
            "suggestions": [
                "检查 broll 字段是否为空",
                "检查 trim_frames 是否使用整数",
                "检查 scenes.json 是否包含 fps"
            ]
        }
except Exception as e:
    # 捕获异常
    return {"status": "error", "message": str(e)}
```

---

## 📚 相关文档

- **[app/models/schemas.py](app/models/schemas.py)** - 验证器实现
- **[app/core/llm_engine.py](app/core/llm_engine.py)** - LLM 提示词
- **[app/core/prompts/dsl_generator.md](app/core/prompts/dsl_generator.md)** - DSL 生成指南
- **[PROTOCOL.md](PROTOCOL.md)** - 协议文件规范

---

## 🎉 总结

### 铁律 1: 不允许"未提供素材库却要求素材调用"
- ✅ 防止 AI 幻觉
- ✅ 确保可执行性
- ✅ 降级策略清晰

### 铁律 2: 坐标体系统一 - 内部只用 frame
- ✅ 类型一致（整数）
- ✅ 计算简单
- ✅ fps 统一换算

### 核心价值
- 🔒 **稳定性** - 防止执行失败
- 🎯 **准确性** - 防止坐标混乱
- 🚀 **可维护性** - 代码简洁清晰

**遵守铁律，系统稳定！** 🎬✨

---

**版本**: v1.2.0  
**更新日期**: 2025-02-05  
**状态**: ✅ 强制执行
