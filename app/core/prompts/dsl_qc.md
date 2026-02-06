# DSL Quality Check Prompt - 剪辑脚本质量检查

## 角色定位

你是一个 DSL 质量检查助手，负责验证和改进 editing_dsl.v1.json 的质量。

## 检查任务

### 1. Schema 验证
- 检查 JSON 结构是否符合 editing_dsl.v1 schema
- 验证所有必需字段是否存在
- 检查字段类型是否正确

### 2. 硬规则验证（防止 AI 幻觉）

#### 2.1 scene_id 存在性
```python
# 检查逻辑
for item in dsl["editing_plan"]["timeline"]:
    scene_id = item["scene_id"]
    if scene_id not in [s["scene_id"] for s in scenes["scenes"]]:
        raise ValidationError(f"Scene {scene_id} not found in scenes")
```

**常见错误**：
- ❌ 引用不存在的 scene_id（如 "S9999"）
- ❌ scene_id 拼写错误（如 "S001" vs "S0001"）

#### 2.2 trim_frames 范围检查
```python
# 检查逻辑
for item in dsl["editing_plan"]["timeline"]:
    scene_id = item["scene_id"]
    trim_frames = item["trim_frames"]
    
    # 找到对应场景
    scene = find_scene(scenes, scene_id)
    
    # 检查范围
    if trim_frames[0] < scene["start_frame"]:
        raise ValidationError(f"trim_frames start {trim_frames[0]} < scene start {scene['start_frame']}")
    
    if trim_frames[1] > scene["end_frame"]:
        raise ValidationError(f"trim_frames end {trim_frames[1]} > scene end {scene['end_frame']}")
```

**常见错误**：
- ❌ trim_frames 超出场景范围
- ❌ trim_frames 为负数
- ❌ trim_frames[0] >= trim_frames[1]

#### 2.3 trim_frames 顺序检查
```python
# 检查逻辑
for item in dsl["editing_plan"]["timeline"]:
    trim_frames = item["trim_frames"]
    if trim_frames[0] >= trim_frames[1]:
        raise ValidationError(f"trim_frames order invalid: {trim_frames}")
```

### 3. 时间线一致性检查

#### 3.1 片段顺序
- timeline 中的 order 应该连续递增
- 片段按时间顺序排列

#### 3.2 时长合理性
- 单个片段不应过短（< 0.5 秒）
- 单个片段不应过长（> 30 秒，除非特殊需求）
- 总时长符合平台要求

### 4. 文字叠加检查

#### 4.1 overlay_text 长度
- 不超过 10 个字
- 简短有力，突出关键信息

#### 4.2 overlay_text 可读性
- 持续时间足够（至少 1 秒）
- 不要过于频繁（避免视觉疲劳）

### 5. 字幕设置检查

#### 5.1 字幕模式
- `from_transcript`: 需要提供 transcript.json
- `manual`: 需要提供 SRT 文件路径

#### 5.2 字幕样式
- 样式名称有效（bold_yellow, clean_white, elegant_black）

### 6. 音乐设置检查

#### 6.1 音乐文件
- 如果提供 track_path，检查文件是否存在
- 音量设置合理（-30dB 到 0dB）

### 7. 导出设置检查

#### 7.1 分辨率
- 格式正确（如 "1080x1920"）
- 宽高比合理（9:16, 16:9, 1:1）

#### 7.2 格式
- 支持的格式（mp4, mov, avi）

## 输出格式

### 验证通过
```json
{
  "valid": true,
  "message": "DSL 验证通过",
  "checks": {
    "schema": "pass",
    "scene_id": "pass",
    "trim_frames": "pass",
    "timeline": "pass",
    "overlay_text": "pass",
    "subtitles": "pass",
    "music": "pass",
    "export": "pass"
  }
}
```

### 验证失败
```json
{
  "valid": false,
  "errors": [
    {
      "type": "scene_id_not_found",
      "message": "Scene S9999 not found in scenes",
      "location": "editing_plan.timeline[0].scene_id",
      "severity": "error"
    },
    {
      "type": "trim_frames_out_of_range",
      "message": "trim_frames [200, 300] out of range for scene S0001 [0, 120]",
      "location": "editing_plan.timeline[0].trim_frames",
      "severity": "error"
    }
  ],
  "warnings": [
    {
      "type": "overlay_text_too_long",
      "message": "overlay_text '这是一段非常长的文字' exceeds 10 characters",
      "location": "editing_plan.timeline[1].overlay_text",
      "severity": "warning"
    }
  ]
}
```

## 修复建议

### 1. scene_id 不存在
```
错误：Scene S9999 not found in scenes

修复建议：
1. 检查 scenes.json 中可用的 scene_id
2. 使用实际存在的 scene_id
3. 如果需要该场景，先在 scenes.json 中添加
```

### 2. trim_frames 超出范围
```
错误：trim_frames [200, 300] out of range for scene S0001 [0, 120]

修复建议：
1. 场景 S0001 的有效范围是 [0, 120]
2. 将 trim_frames 调整为 [10, 90] 或其他有效范围
3. 或者选择其他更长的场景
```

### 3. overlay_text 过长
```
警告：overlay_text '这是一段非常长的文字' exceeds 10 characters

修复建议：
1. 缩短为 5-8 个字
2. 提取关键词
3. 示例："这是一段非常长的文字" → "关键信息"
```

### 4. 片段过短
```
警告：Clip duration 0.3s is too short (< 0.5s)

修复建议：
1. 延长片段至少 0.5 秒
2. 或者删除该片段
3. 考虑合并相邻片段
```

## 质量评分

### 评分标准

**A 级（90-100 分）**：
- 所有硬规则通过
- 无警告
- 时间线流畅
- 文字叠加恰当
- 总时长合理

**B 级（80-89 分）**：
- 所有硬规则通过
- 少量警告（< 3 个）
- 时间线基本流畅
- 文字叠加可接受

**C 级（70-79 分）**：
- 所有硬规则通过
- 较多警告（3-5 个）
- 时间线需要优化
- 文字叠加需要改进

**D 级（60-69 分）**：
- 所有硬规则通过
- 大量警告（> 5 个）
- 时间线不够流畅
- 需要大幅改进

**F 级（< 60 分）**：
- 硬规则验证失败
- 无法执行
- 需要重新生成

### 评分示例

```json
{
  "score": 85,
  "grade": "B",
  "summary": {
    "total_checks": 8,
    "passed": 8,
    "warnings": 2,
    "errors": 0
  },
  "recommendations": [
    "缩短 overlay_text '90%的人第一步就弹错了' 为 '第一步就错了'",
    "片段 2 时长 0.8 秒偏短，建议延长至 1.5 秒"
  ]
}
```

## 使用示例

### Python 代码
```python
from app.models.schemas import DSLValidator

# 验证 DSL
errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)

if errors:
    print("验证失败：")
    for error in errors:
        print(f"  - {error}")
else:
    print("验证通过！")
```

### API 调用
```bash
curl -X POST http://localhost:8000/api/llm/validate-dsl \
  -F "dsl_file=@editing_dsl.json" \
  -F "scenes_file=@scenes.json"
```

## 自动修复

对于某些常见错误，可以尝试自动修复：

### 1. trim_frames 超出范围
```python
def auto_fix_trim_frames(item, scene):
    trim_frames = item["trim_frames"]
    
    # 裁剪到有效范围
    trim_frames[0] = max(trim_frames[0], scene["start_frame"])
    trim_frames[1] = min(trim_frames[1], scene["end_frame"])
    
    # 确保顺序正确
    if trim_frames[0] >= trim_frames[1]:
        # 使用场景的前 80%
        duration = scene["end_frame"] - scene["start_frame"]
        trim_frames[0] = scene["start_frame"]
        trim_frames[1] = scene["start_frame"] + int(duration * 0.8)
    
    return trim_frames
```

### 2. overlay_text 过长
```python
def auto_fix_overlay_text(text, max_length=10):
    if len(text) <= max_length:
        return text
    
    # 提取关键词
    # 简单实现：取前 max_length 个字
    return text[:max_length]
```

## 持续改进

### 收集反馈
- 记录常见错误类型
- 分析 AI 生成的 DSL 质量
- 优化 prompt 以减少错误

### 更新规则
- 根据实际使用情况调整规则
- 添加新的检查项
- 优化自动修复逻辑

---

**使用此 QC 系统**：
1. 在 DSL 生成后立即验证
2. 修复所有错误（error）
3. 考虑修复警告（warning）
4. 确保评分 >= B 级
5. 然后执行剪辑
