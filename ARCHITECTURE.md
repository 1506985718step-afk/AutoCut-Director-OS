# AutoCut Director 架构设计

## 设计理念

### 1. 协议驱动（Protocol-Driven）

所有功能围绕三个固定格式的 JSON 协议文件展开：

```
scenes.json → transcript.json → editing_dsl.json → Resolve
```

**优势：**
- 清晰的数据流
- 易于验证和调试
- 版本化设计
- 跨语言兼容

### 2. 数据驱动（Data-Driven）

动作是纯数据对象（dataclass），Executor 只负责执行：

```python
@dataclass
class Action:
    name: str
    params: dict

# 工厂函数
create_timeline(name, fps) -> Action
append_scene(scene_id, in_frame, out_frame) -> Action
```

**优势：**
- 易于序列化和传输
- 业务逻辑与执行分离
- 可测试性强
- 易于扩展

### 3. 硬规则验证（Hard Rules Validation）

防止 AI 幻觉，确保数据一致性：

```python
DSLValidator.validate_dsl_against_scenes(dsl, scenes)

# 检查项：
# 1. scene_id 存在性
# 2. trim_frames 范围
# 3. trim_frames 顺序
```

**优势：**
- 拒绝无效的 AI 输出
- 保证执行安全性
- 详细的错误信息

---

## 核心组件

### 1. 协议层（Protocol Layer）

**文件：** `app/models/schemas.py`

```python
class ScenesJSON(BaseModel):
    meta: ScenesMeta
    media: ScenesMedia
    scenes: List[Scene]

class EditingDSL(BaseModel):
    meta: EditingDSLMeta
    editing_plan: EditingPlan
    export: Export

class DSLValidator:
    @staticmethod
    def validate_dsl_against_scenes(dsl, scenes) -> tuple[bool, list]
```

**职责：**
- 定义协议数据结构
- 提供数据验证
- 硬规则检查

### 2. 工具层（Tools Layer）

**文件：** `app/tools/`

```python
# EDL 解析器
def parse_edl_to_scenes(edl_path, fps, primary_clip_path) -> dict

# Whisper ASR
def transcribe_audio(audio_path, model_size) -> dict

# SRT 解析器
def parse_srt_to_transcript(srt_path) -> dict
```

**职责：**
- 解析外部格式
- 生成协议文件
- 数据转换

### 3. 动作层（Action Layer）

**文件：** `app/executor/actions.py`

```python
@dataclass
class Action:
    name: str
    params: dict

# 工厂函数
def create_timeline(name, fps) -> Action
def append_scene(scene_id, in_frame, out_frame) -> Action
def import_srt(path) -> Action
def add_music(path, volume_db) -> Action
def export_mp4(path, resolution) -> Action

# 执行器
def execute_action(action, adapter) -> Any
```

**职责：**
- 定义动作数据结构
- 提供工厂函数
- 映射到 Resolve 操作

### 4. 执行层（Execution Layer）

**文件：** `app/executor/`

```python
# Resolve 连接
def connect_resolve() -> tuple[resolve, project]

# Resolve 适配器
class ResolveAdapter:
    def connect()
    def create_timeline(name, framerate, resolution)
    def append_clip(source, start, end, track)
    def import_srt(srt_path, track)
    def add_audio(audio_path, start, volume)
    def export(output_path, preset, quality)

# 动作队列执行器
class Runner:
    def run(actions: List[Action])
    def get_trace() -> list
```

**职责：**
- 连接 DaVinci Resolve
- 执行动作队列
- 记录执行 trace

### 5. API 层（API Layer）

**文件：** `app/api/`

```python
# 分析路由
@router.post("/analyze")
async def analyze(edl_file, audio_file)

# 执行路由
@router.post("/execute")
async def execute(dsl_file, scenes_file)

# 验证路由
@router.post("/execute/validate")
async def validate_dsl_endpoint(dsl_data, scenes_data)
```

**职责：**
- 处理 HTTP 请求
- 文件上传管理
- Job 状态管理

---

## 数据流

### 完整工作流

```
1. 用户上传 EDL
   ↓
2. parse_edl_to_scenes()
   ↓
3. scenes.json (存储)
   ↓
4. LLM 读取 scenes.json
   ↓
5. 生成 editing_dsl.json
   ↓
6. DSLValidator.validate_dsl_against_scenes()
   ↓ (验证通过)
7. _dsl_to_actions(dsl, scenes)
   ↓
8. Action 队列
   ↓
9. Runner.run(actions)
   ↓
10. execute_action() → ResolveAdapter
   ↓
11. DaVinci Resolve 操作
   ↓
12. 导出成品
```

### DSL → Actions 转换

```python
def _dsl_to_actions(dsl: EditingDSL, scenes: ScenesJSON) -> List[Action]:
    actions = []
    
    # 1. 创建时间线
    actions.append(create_timeline(name, fps, resolution))
    
    # 2. 添加场景片段
    for item in dsl.editing_plan.timeline:
        actions.append(append_scene(
            scene_id=item.scene_id,
            in_frame=item.trim_frames[0],
            out_frame=item.trim_frames[1],
            source=scenes.media.primary_clip_path
        ))
    
    # 3. 添加字幕
    if dsl.editing_plan.subtitles.mode == "from_transcript":
        actions.append(import_srt(path))
    
    # 4. 添加音乐
    actions.append(add_music(path, volume_db))
    
    # 5. 导出
    actions.append(export_mp4(path, resolution))
    
    return actions
```

### Actions → Resolve 执行

```python
def execute_action(action: Action, adapter: ResolveAdapter):
    if action.name == "CreateTimeline":
        return adapter.create_timeline(**action.params)
    
    elif action.name == "AppendScene":
        # 帧数 → 秒
        fps = adapter.current_timeline.GetSetting("timelineFrameRate")
        start_sec = action.params["in_frame"] / fps
        end_sec = action.params["out_frame"] / fps
        
        return adapter.append_clip(
            source=action.params["source"],
            start=start_sec,
            end=end_sec
        )
    
    # ... 其他动作
```

---

## 设计模式

### 1. 工厂模式（Factory Pattern）

```python
# 动作工厂函数
def create_timeline(name, fps) -> Action
def append_scene(scene_id, in_frame, out_frame) -> Action

# 使用
action = create_timeline("My Timeline", 30.0)
```

### 2. 适配器模式（Adapter Pattern）

```python
class ResolveAdapter:
    """适配 DaVinci Resolve API"""
    
    def create_timeline(self, name, framerate, resolution):
        # 适配 Resolve API
        self.current_timeline = self.media_pool.CreateEmptyTimeline(name)
        self.current_timeline.SetSetting("timelineFrameRate", str(framerate))
```

### 3. 策略模式（Strategy Pattern）

```python
def execute_action(action: Action, adapter):
    """根据 action.name 选择执行策略"""
    if action.name == "CreateTimeline":
        return adapter.create_timeline(...)
    elif action.name == "AppendScene":
        return adapter.append_clip(...)
```

### 4. 数据传输对象（DTO Pattern）

```python
@dataclass
class Action:
    """纯数据对象，易于序列化"""
    name: str
    params: dict
```

---

## 关键决策

### 1. 为什么使用 dataclass 而不是类继承？

**传统方式（类继承）：**
```python
class Action:
    def execute(self, adapter):
        raise NotImplementedError

class CreateTimeline(Action):
    def __init__(self, name, fps):
        self.name = name
        self.fps = fps
    
    def execute(self, adapter):
        return adapter.create_timeline(self.name, self.fps)
```

**数据驱动方式（dataclass）：**
```python
@dataclass
class Action:
    name: str
    params: dict

def create_timeline(name, fps) -> Action:
    return Action("CreateTimeline", {"name": name, "fps": fps})

def execute_action(action, adapter):
    if action.name == "CreateTimeline":
        return adapter.create_timeline(**action.params)
```

**优势：**
- ✅ 易于序列化（JSON/MessagePack）
- ✅ 易于传输（HTTP/RPC）
- ✅ 易于存储（数据库/文件）
- ✅ 业务逻辑与执行分离
- ✅ 更容易测试和调试

### 2. 为什么需要硬规则验证？

**问题：** AI 可能生成无效的 DSL

```json
{
  "timeline": [
    {"scene_id": "S9999", "trim_frames": [10, 90]}  // 场景不存在
  ]
}
```

**解决：** 硬规则验证

```python
is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)

if not is_valid:
    raise HTTPException(400, detail={"errors": errors})
```

**结果：** 拒绝执行，返回详细错误

### 3. 为什么使用帧数而不是秒？

**原因：**
- ✅ 精确性：帧是视频的最小单位
- ✅ 一致性：EDL 使用帧数
- ✅ 可验证：易于检查范围
- ✅ 转换简单：`seconds = frames / fps`

---

## 扩展性

### 添加新动作

1. 在 `actions.py` 添加工厂函数：
```python
def add_transition(type: str, duration: float) -> Action:
    return Action("AddTransition", {"type": type, "duration": duration})
```

2. 在 `execute_action()` 添加执行逻辑：
```python
elif action.name == "AddTransition":
    return adapter.add_transition(**action.params)
```

3. 在 `ResolveAdapter` 添加方法：
```python
def add_transition(self, type: str, duration: float):
    # Resolve API 调用
    pass
```

### 添加新协议版本

1. 定义新版本模型：
```python
class ScenesV2(BaseModel):
    meta: ScenesMetaV2  # schema: "scenes.v2"
    media: ScenesMediaV2
    scenes: List[SceneV2]
    transitions: List[Transition]  # 新增
```

2. 添加版本检测：
```python
def parse_scenes(data: dict):
    if data["meta"]["schema"] == "scenes.v1":
        return ScenesJSON(**data)
    elif data["meta"]["schema"] == "scenes.v2":
        return ScenesV2(**data)
```

---

## 性能考虑

### 1. 批量操作

```python
# 不好：逐个添加片段
for clip in clips:
    adapter.append_clip(clip)

# 好：批量添加
adapter.append_clips_batch(clips)
```

### 2. 异步执行

```python
# 未来：异步执行动作队列
async def run_async(self, actions: List[Action]):
    await asyncio.gather(*[
        execute_action_async(action, self.adapter)
        for action in actions
    ])
```

### 3. 缓存

```python
# 缓存媒体池导入
class ResolveAdapter:
    def __init__(self):
        self._media_cache = {}
    
    def append_clip(self, source, ...):
        if source not in self._media_cache:
            self._media_cache[source] = self._import_media(source)
        clip = self._media_cache[source]
```

---

## 测试策略

### 1. 单元测试

```python
# 测试动作创建
def test_create_timeline_action():
    action = create_timeline("Test", 30.0)
    assert action.name == "CreateTimeline"
    assert action.params["fps"] == 30.0

# 测试 DSL 验证
def test_dsl_validator():
    is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)
    assert is_valid == True
```

### 2. 集成测试

```python
# 测试 Resolve 连接
def test_resolve_connection():
    resolve, project = connect_resolve()
    assert resolve is not None
    assert project is not None

# 测试完整流程
def test_e2e():
    scenes = parse_edl_to_scenes("test.edl", 30, "input.mp4")
    dsl = create_test_dsl()
    actions = _dsl_to_actions(dsl, scenes)
    runner = Runner()
    runner.run(actions)
    assert len(runner.get_trace()) > 0
```

---

## 总结

**核心优势：**
1. ✅ 协议驱动 - 清晰的数据流
2. ✅ 数据驱动 - 易于序列化和传输
3. ✅ 硬规则验证 - 防止 AI 幻觉
4. ✅ 最小骨架 - 简洁高效
5. ✅ 易于扩展 - 模块化设计

**设计原则：**
- 数据与逻辑分离
- 协议优先
- 验证优先
- 简单优于复杂

---

**版本**: 1.0.0  
**最后更新**: 2025-02-05
