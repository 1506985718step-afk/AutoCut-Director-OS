# AutoCut Director 协议文件规范

## 三个核心协议文件

所有功能都围绕这三个固定格式的 JSON 文件展开。

---

## 1. scenes.json (MVP v1)

**用途：** 定义视频的场景切分信息

**来源：** EDL/FCPXML 解析器生成

**Schema:**
```json
{
  "meta": {
    "schema": "scenes.v1",
    "fps": 30,
    "source": "davinci/edl"
  },
  "media": {
    "primary_clip_path": "D:/Footage/input.mp4"
  },
  "scenes": [
    {
      "scene_id": "S0001",
      "start_frame": 0,
      "end_frame": 120,
      "start_tc": "00:00:00:00",
      "end_tc": "00:00:04:00"
    }
  ]
}
```

**字段说明：**
- `meta.schema`: 协议版本标识
- `meta.fps`: 帧率
- `meta.source`: 来源（davinci/edl, fcpxml, auto）
- `media.primary_clip_path`: 主素材路径
- `scenes[].scene_id`: 场景唯一标识（格式：S0001, S0002...）
- `scenes[].start_frame/end_frame`: 场景帧范围
- `scenes[].start_tc/end_tc`: 时间码（HH:MM:SS:FF）

---

## 2. transcript.json (MVP v1)

**用途：** 音频转录结果

**来源：** Whisper ASR 或 SRT 导入

**Schema:**
```json
{
  "meta": {
    "schema": "transcript.v1",
    "language": "zh"
  },
  "segments": [
    {
      "start": 0.0,
      "end": 2.8,
      "text": "90%的人第一步就弹错了"
    }
  ]
}
```

**字段说明：**
- `meta.language`: 语言代码（zh, en, ja...）
- `segments[].start/end`: 时间戳（秒）
- `segments[].text`: 转录文本

---

## 3. editing_dsl.json (AI 输出，唯一指挥通道)

**用途：** AI 生成的剪辑指令

**来源：** LLM 根据 scenes.json 生成

**Schema:**
```json
{
  "meta": {
    "schema": "editing_dsl.v1",
    "target": "douyin",
    "aspect": "9:16"
  },
  "editing_plan": {
    "timeline": [
      {
        "order": 1,
        "scene_id": "S0001",
        "trim_frames": [10, 90],
        "purpose": "hook",
        "overlay_text": "第一步就错了"
      }
    ],
    "subtitles": {
      "mode": "from_transcript"
    },
    "music": {
      "track_path": "D:/Music/bgm.mp3",
      "volume_db": -18
    }
  },
  "export": {
    "resolution": "1080x1920",
    "format": "mp4"
  }
}
```

**字段说明：**
- `meta.target`: 目标平台（douyin, bilibili, youtube）
- `meta.aspect`: 画幅比例（9:16, 16:9, 1:1）
- `editing_plan.timeline[].order`: 片段顺序
- `editing_plan.timeline[].scene_id`: 引用 scenes.json 中的场景
- `editing_plan.timeline[].trim_frames`: 裁剪帧范围 [start, end]
- `editing_plan.timeline[].purpose`: 用途标签（hook, content, cta）
- `editing_plan.timeline[].overlay_text`: 叠加文字（可选）
- `editing_plan.subtitles.mode`: 字幕模式（from_transcript, none, custom）
- `editing_plan.music.volume_db`: 音量（dB）
- `export.resolution`: 输出分辨率（WxH）

---

## 硬规则（防 AI 幻觉）

Executor 在执行前必须验证：

### 1. scene_id 存在性检查
```python
if scene_id not in scenes.json:
    raise ValidationError("Scene ID not found")
```

### 2. trim_frames 范围检查
```python
if trim_start < scene.start_frame or trim_end > scene.end_frame:
    raise ValidationError("trim_frames out of scene range")
```

### 3. trim_frames 顺序检查
```python
if trim_start >= trim_end:
    raise ValidationError("Invalid trim_frames order")
```

**拒绝执行原则：** 任何验证失败都应立即拒绝执行，返回详细错误信息。

---

## 工作流程

```
1. 用户上传 EDL/视频
   ↓
2. 生成 scenes.json + transcript.json
   ↓
3. LLM 读取 scenes.json，生成 editing_dsl.json
   ↓
4. Executor 验证 DSL（硬规则检查）
   ↓
5. 执行 Resolve 操作
   ↓
6. 导出成品
```

---

## 版本演进

- **v1 (MVP)**: 基础场景切分 + 单素材
- **v2 (计划)**: 多素材支持 + 转场效果
- **v3 (计划)**: 动态字幕样式 + 特效

---

## API 端点

### 分析素材
```bash
POST /api/analyze
- edl_file: EDL 文件
- audio_file: 音频文件（可选）

返回: scenes.json + transcript.json
```

### 执行剪辑
```bash
POST /api/execute
- dsl_file: editing_dsl.json
- scenes_file: scenes.json

返回: 执行 trace + 输出路径
```

### 验证 DSL
```bash
POST /api/execute/validate
Body: {
  "dsl_data": {...},
  "scenes_data": {...}
}

返回: { "valid": true/false, "errors": [...] }
```


---

## 🔴 两条铁律

### 铁律 1: 不允许"未提供素材库却要求素材调用"

**规则**: 如果没有提供 B-roll 素材库，`broll` 字段**必须为空数组** `[]`

**原因**:
- 防止 AI 幻觉（生成不存在的素材）
- 确保可执行性（Resolve 能找到所有文件）
- 降级策略清晰（通过 assumptions 说明建议）

**示例**:
```json
{
  "timeline": [
    {
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": [10, 90],
      "broll": []  // ✅ 没有素材库，必须为空
    }
  ],
  "assumptions": [
    "建议添加产品特写 B-roll 增强视觉效果"
  ]
}
```

**验证**:
```python
from app.models.schemas import DSLValidator

errors = DSLValidator.validate_dsl_against_scenes(
    dsl, scenes_data, broll_library=None
)
# 如果 broll 不为空，会返回错误
```

---

### 铁律 2: 坐标体系统一 - 内部只用 frame

**规则**: 
1. **内部执行只用 frame**（整数帧号）
2. **对外展示可附带 TC**（timecode，仅用于可读性）
3. **scenes.json 必须带 fps**，validator 用它统一换算

**原因**:
- 类型一致（整数 vs 字符串）
- 计算简单（加减乘除 vs 解析）
- fps 无关（绝对值 vs 相对值）

**示例**:
```json
{
  "meta": {
    "fps": 30  // ✅ 必须提供 fps
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

**换算工具**:
```python
from app.models.schemas import DSLValidator

# Frame → Timecode (展示)
tc = DSLValidator.frames_to_timecode(120, fps=30)
# → "00:00:04:00"

# Timecode → Frame (输入)
frame = DSLValidator.timecode_to_frames("00:00:04:00", fps=30)
# → 120
```

**验证**:
```python
# 检查 fps
if not DSLValidator.validate_scenes_has_fps(scenes_data):
    raise ValueError("scenes.json 必须包含 fps")

# 检查 trim_frames 类型
errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
# 如果 trim_frames 不是整数，会返回错误
```

---

## 验证规则总结

### 基础验证
1. ✅ scene_id 必须存在于 scenes.json 中
2. ✅ trim_frames 必须在场景的 [start_frame, end_frame] 范围内
3. ✅ trim_frames[0] < trim_frames[1]
4. ✅ overlay_text 不超过 10 个字

### 铁律验证
5. 🔴 **铁律 1**: 如果没有素材库，broll 必须为 []
6. 🔴 **铁律 2**: trim_frames 必须是整数帧号，不能是 timecode
7. 🔴 **铁律 2**: scenes.json 必须包含 fps

---

## 相关文档

- **[IRON_RULES.md](IRON_RULES.md)** - 两条铁律详细说明 ⭐
- **[app/models/schemas.py](app/models/schemas.py)** - 验证器实现
- **[test_iron_rules.py](test_iron_rules.py)** - 铁律测试

---
