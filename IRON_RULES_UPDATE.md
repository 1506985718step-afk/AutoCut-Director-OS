# 两条铁律更新总结

## 🎯 更新内容

为 AutoCut Director 添加了**两条铁律**，确保系统的严谨性和一致性。

---

## 🔴 铁律 1: 不允许"未提供素材库却要求素材调用"

### 问题
AI 可能会"幻想"不存在的 B-roll 素材，导致执行失败。

### 解决方案
- 如果没有提供 B-roll 素材库，`broll` 字段**必须为空数组** `[]`
- 通过 `assumptions` 字段记录建议
- 验证器强制检查

### 实现
```python
# app/models/schemas.py
if broll:
    if not broll_library:
        errors.append(
            f"铁律 1 违反 - 要求 B-roll 素材 {broll}，但未提供素材库。"
            f"必须降级为 broll: [] + assumptions"
        )
```

---

## 🔴 铁律 2: 坐标体系统一 - 内部只用 frame

### 问题
混用 timecode 和 frame 导致类型不一致、换算错误、代码复杂。

### 解决方案
- **内部执行只用 frame**（整数帧号）
- **对外展示可附带 TC**（timecode，仅用于可读性）
- **scenes.json 必须带 fps**，validator 用它统一换算

### 实现
```python
# app/models/schemas.py
if not isinstance(trim_start, int) or not isinstance(trim_end, int):
    errors.append(
        f"铁律 2 违反 - trim_frames 必须是整数帧号，不能是 timecode"
    )

# 换算工具
def frames_to_timecode(frame: int, fps: float) -> str
def timecode_to_frames(timecode: str, fps: float) -> int
```

---

## 📁 文件更新清单

### 新增文件
- ✅ `IRON_RULES.md` - 两条铁律详细说明
- ✅ `test_iron_rules.py` - 铁律测试脚本
- ✅ `IRON_RULES_UPDATE.md` - 本文件

### 更新文件
- ✅ `app/models/schemas.py` - 添加验证逻辑
  - 更新 `DSLValidator.validate_dsl_against_scenes()`
  - 添加 `validate_scenes_has_fps()`
  - 添加 `frames_to_timecode()`
  - 添加 `timecode_to_frames()`
  - 添加 `broll` 字段到 `TimelineItem`

- ✅ `app/core/llm_engine.py` - 更新提示词
  - 添加铁律 1 说明和示例
  - 添加铁律 2 说明和示例

- ✅ `app/core/prompts/dsl_generator.md` - 更新 DSL 生成指南
  - 添加铁律 1 详细说明
  - 添加铁律 2 详细说明
  - 添加验证检查清单

- ✅ `PROTOCOL.md` - 更新协议文件规范
  - 添加两条铁律章节
  - 添加验证规则总结

---

## 🧪 测试

### 运行测试
```bash
cd autocut-director
python test_iron_rules.py
```

### 测试内容
1. ✅ 铁律 1 - 违反情况（有 broll 但无素材库）
2. ✅ 铁律 1 - 正确情况（broll 为空）
3. ✅ 铁律 1 - 有素材库情况
4. ✅ 铁律 2 - 违反情况（使用 timecode）
5. ✅ 铁律 2 - 正确情况（使用 frame）
6. ✅ scenes.json 必须包含 fps
7. ✅ frame ↔ timecode 转换
8. ✅ 完整验证流程

### 测试结果
```
✅ 所有测试通过
两条铁律验证逻辑正确！
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
❌ Timeline item 1: 铁律 1 违反 - 要求 B-roll 素材 ['product.mp4']，
   但未提供素材库。必须降级为 broll: [] + assumptions
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
❌ Timeline item 1: 铁律 2 违反 - trim_frames 必须是整数帧号，
   不能是 timecode
```

---

### 示例 3: 全部通过 ✅

**scenes.json**:
```json
{
  "meta": {
    "schema": "scenes.v1",
    "fps": 30  // ✅ 包含 fps
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
        "trim_frames": [10, 90],  // ✅ 整数帧号
        "broll": []  // ✅ 没有素材库，为空
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

## 🎯 使用指南

### 1. 在 LLM 提示词中强调

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

### 2. 在验证流程中检查

```python
from app.models.schemas import DSLValidator

# 1. 验证 scenes.json
if not DSLValidator.validate_scenes_has_fps(scenes_data):
    raise ValueError("scenes.json 必须包含 fps")

# 2. 验证 DSL（包含两条铁律）
errors = DSLValidator.validate_dsl_against_scenes(
    dsl=dsl_data,
    scenes_data=scenes_data,
    broll_library=None  # 没有素材库
)

if errors:
    print("验证失败:")
    for err in errors:
        print(f"  - {err}")
    raise ValidationError(errors)

# 3. 执行
run_actions(actions)
```

### 3. 在 API 中返回详细错误

```python
@router.post("/api/llm/generate-dsl")
async def generate_dsl(...):
    # 生成 DSL
    dsl = director.generate_editing_dsl(...)
    
    # 验证
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl, scenes_data, broll_library=None
    )
    
    if errors:
        return {
            "status": "validation_failed",
            "errors": errors,
            "suggestions": [
                "检查 broll 字段是否为空",
                "检查 trim_frames 是否使用整数",
                "检查 scenes.json 是否包含 fps"
            ]
        }
    
    return {"status": "success", "dsl": dsl}
```

---

## 📚 相关文档

- **[IRON_RULES.md](IRON_RULES.md)** - 两条铁律详细说明 ⭐
- **[PROTOCOL.md](PROTOCOL.md)** - 协议文件规范
- **[app/models/schemas.py](app/models/schemas.py)** - 验证器实现
- **[app/core/llm_engine.py](app/core/llm_engine.py)** - LLM 提示词
- **[test_iron_rules.py](test_iron_rules.py)** - 铁律测试

---

## 🎉 总结

### 核心价值

**铁律 1: 不允许"未提供素材库却要求素材调用"**
- ✅ 防止 AI 幻觉
- ✅ 确保可执行性
- ✅ 降级策略清晰

**铁律 2: 坐标体系统一 - 内部只用 frame**
- ✅ 类型一致（整数）
- ✅ 计算简单
- ✅ fps 统一换算

### 系统改进

1. **稳定性提升** - 防止执行失败
2. **准确性提升** - 防止坐标混乱
3. **可维护性提升** - 代码简洁清晰
4. **可测试性提升** - 验证逻辑完善

### 向后兼容

- ✅ 现有 DSL 格式兼容
- ✅ 现有验证逻辑增强
- ✅ 新增字段可选（broll 默认为 []）

---

**遵守铁律，系统稳定！** 🎬✨

---

**版本**: v1.2.0  
**更新日期**: 2025-02-05  
**状态**: ✅ 强制执行
