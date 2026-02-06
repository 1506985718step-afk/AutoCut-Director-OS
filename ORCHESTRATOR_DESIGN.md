# Orchestrator 设计文档 - 状态机 + 调度算法

**日期**: 2026-02-05  
**版本**: v3.0.0  
**目标**: 让系统像 OpenClaw 一样聪明指挥，但绝不把电脑拖死

---

## 🎯 最终原则

### 一句话总原则

```
AI = 导演（决策）
Resolve = 工人（执行）
Orchestrator = 调度员（协调）
```

### 责任边界（铁律）

| 模块 | 职责 | 禁止做的事 |
|------|------|-----------|
| **AI（云端+本地）** | 理解内容、镜头语言、脚本、剪辑策略 | ❌ 不直接操作时间线 |
| **Executor（Resolve）** | 导入素材、剪辑、加字幕、加音乐、导出 | ❌ 不思考"怎么剪" |
| **Orchestrator（状态机）** | 资源调度、顺序控制、防崩溃 | ❌ 不做创意 |

**这条线一旦乱，系统必炸。**

---

## 📊 终版状态机（State Machine v1.0）

### 全局 Job 状态机

```
CREATED → INGESTING → INGESTED → ANALYZING → ANALYZED
    ↓                                ↓            ↓
  FAILED ←─────────────────────────┘            ↓
                                              PLANNING
                                                 ↓
                                              PLANNED
                                                 ↓
                                              EXECUTING
                                                 ↓
                                              EXPORTING
                                                 ↓
                                              COMPLETED
```

### 状态说明

#### 1. CREATED / INGESTING / INGESTED
**资源使用**:
- ✅ CPU：允许
- ✅ GPU：允许（轻量）
- ❌ Resolve：不允许操作时间线
- ❌ VLM：禁止（没意义）

**用途**: 素材预处理、音频提取、场景检测提示

---

#### 2. ANALYZING（最危险的阶段之一）

**功能**: 抽帧 + 本地 VLM（Eyes）

**资源使用**:
- ✅ CPU：允许
- ⚠️ GPU：可选（仅当 Resolve 空闲）
- ✅ Ollama VLM：允许（但受限）
- ❌ Resolve：禁止任何剪辑/导出

**硬限制**:
```python
VISION_MAX_SCENES = 10  # 最多分析 10 个场景
VISION_DEVICE = "cpu" | "auto"  # 设备选择
```

**关键规则**:
- ⚠️ 如果 Resolve 已启动但正在 Render → ANALYZING 必须等待
- ⚠️ 如果 GPU 使用率 > 70% → 强制使用 CPU 模式

---

#### 3. PLANNING（最安全、最"聪明"的阶段）

**功能**: 云端 DeepSeek 生成脚本 / 结构化 / DSL

**资源使用**:
- ✅ CPU：低
- ✅ GPU：0
- ✅ 网络：需要
- ❌ Resolve：禁止

**特点**:
- 👉 这是最便宜、最安全、最该多用 AI 的阶段
- 👉 AI 在这里"导演"，不在执行时"指手画脚"

---

#### 4. EXECUTING（剪辑执行）

**功能**: Resolve 执行 DSL（Hands）

**资源使用**:
- ✅ Resolve：全权
- ⚠️ CPU：优先给 Resolve
- ⚠️ GPU：优先给 Resolve

**禁止**:
- ❌ Ollama
- ❌ Vision
- ❌ 本地模型加载

**原则**: 这里 AI 完全"闭嘴"，只看 trace

---

#### 5. EXPORTING（最高风险）

**功能**: Resolve 导出视频

**资源使用**:
- 🔥 Resolve：高负载
- 🔥 GPU：全给 Resolve
- 🔥 CPU：全给 Resolve

**全局硬闸门**:
- 🚫 禁止一切 AI 模型调用
- 🚫 禁止 ffmpeg
- 🚫 禁止 Ollama

---

## 🔒 核心调度算法（Scheduler v1.0）

### 全局资源锁

```python
GLOBAL_LOCKS = {
    "GPU_HEAVY": False,      # Resolve Export / Render
    "VISION_ALLOWED": True,  # 是否允许跑 VLM
    "RESOLVE_BUSY": False,   # Resolve 是否繁忙
    "AI_ALLOWED": True       # 是否允许 AI 调用
}
```

### 状态切换时强制更新锁

```python
def on_state_enter(state):
    if state == "ANALYZING":
        assert not GLOBAL_LOCKS["RESOLVE_BUSY"]
        GLOBAL_LOCKS["VISION_ALLOWED"] = True
    
    if state in ["EXECUTING", "EXPORTING"]:
        GLOBAL_LOCKS["VISION_ALLOWED"] = False
        GLOBAL_LOCKS["AI_ALLOWED"] = False
        GLOBAL_LOCKS["GPU_HEAVY"] = True
        GLOBAL_LOCKS["RESOLVE_BUSY"] = True

def on_state_exit(state):
    if state == "EXPORTING":
        GLOBAL_LOCKS["GPU_HEAVY"] = False
        GLOBAL_LOCKS["RESOLVE_BUSY"] = False
        GLOBAL_LOCKS["VISION_ALLOWED"] = True
        GLOBAL_LOCKS["AI_ALLOWED"] = True
```

### Vision 调度算法（防崩溃关键）

```python
def run_vision_task(task):
    # 1. 检查是否允许
    if not GLOBAL_LOCKS["VISION_ALLOWED"]:
        queue(task)
        return "DEFERRED"
    
    # 2. 检查 GPU 状态
    if GLOBAL_LOCKS["GPU_HEAVY"]:
        force_cpu_mode(task)
    
    # 3. 执行
    run(task)
```

**结论**: 宁可慢，不可炸。

---

## 🧠 核心算法优化（"AI 更像导演"）

### 镜头理解：不是"识别画面"，而是"剪辑语义"

我们明确一个事实：
- ❌ 不需要"完美 CV"
- ✅ 只需要剪辑级理解

**VisualMetadata 只保留导演关心的字段**:

```json
{
  "summary": "Man playing classical guitar",
  "shot_type": "Close-up",
  "mood": "Calm",
  "quality_score": 8,
  "usable": true
}
```

👉 不做检测算法竞赛，只做"能不能剪"判断

---

### 没脚本时，AI 的导演流程

**新增模式**: `SCRIPT_MODE = AUTO_DIRECT`

**流程**:

1. **AI 先看素材**
   - 抽关键帧
   - Vision → caption
   - DeepSeek 聚类 → "这些素材讲什么"

2. **生成"剪辑脚本草案"**
   ```json
   {
     "segments": [
       { "purpose": "hook", "intent": "吸引注意", "target_sec": 3 },
       { "purpose": "showcase", "intent": "展示演奏", "target_sec": 10 }
     ]
   }
   ```

3. **再反向选素材**
   - 质量差的直接丢弃
   - 重复角度合并
   - 自动标记"备用镜头"

**这一步是导演行为，不是剪辑行为。**

---

### DSL 执行算法（Hands 专用）

Executor 只看 DSL，不思考：

```json
{
  "timeline": [
    { "asset_id": "A003", "trim": [20, 110] },
    { "asset_id": "A001", "trim": [0, 80] }
  ],
  "music": { "id": "bgm_02", "ducking": true },
  "subtitle": { "style": "bold_center" }
}
```

**Executor 禁止**:
- ❌ 调整顺序
- ❌ 判断好不好
- ❌ 再剪一次

---

## 🛡️ 防电脑崩溃的 5 条铁律

### 铁律 1: 任何时间只允许一个 GPU-heavy 任务

```python
def acquire_gpu_heavy():
    if GLOBAL_LOCKS["GPU_HEAVY"]:
        raise ResourceBusyError("GPU 已被占用")
    GLOBAL_LOCKS["GPU_HEAVY"] = True
```

**实现**: 全局锁 + 状态机强制检查

---

### 铁律 2: Resolve Export > 一切 AI

```python
def on_export_start():
    # 强制停止所有 AI 任务
    stop_all_vision_tasks()
    stop_all_ai_tasks()
    
    # 独占资源
    GLOBAL_LOCKS["GPU_HEAVY"] = True
    GLOBAL_LOCKS["VISION_ALLOWED"] = False
    GLOBAL_LOCKS["AI_ALLOWED"] = False
```

**实现**: EXPORTING 状态自动触发

---

### 铁律 3: Vision 失败 ≠ Job 失败（可降级）

```python
def analyze_scene_with_fallback(scene):
    try:
        return vision_analyze(scene)
    except VisionError:
        # 降级：使用默认值
        return VisualMetadata(
            summary="未分析",
            shot_type="中景",
            quality_score=5,
            usable=True
        )
```

**实现**: 异常捕获 + 默认值

---

### 铁律 4: AI 输出不可执行 ≠ Executor 崩溃

```python
def execute_dsl(dsl):
    # 1. 验证 DSL
    errors = validate_dsl(dsl)
    if errors:
        log_errors(errors)
        return {"status": "validation_failed", "errors": errors}
    
    # 2. 执行
    try:
        result = resolve_adapter.execute(dsl)
        return {"status": "success", "result": result}
    except Exception as e:
        log_exception(e)
        return {"status": "execution_failed", "error": str(e)}
```

**实现**: 多层验证 + 异常隔离

---

### 铁律 5: 所有步骤必须可重跑（幂等）

```python
def analyze_scenes(job_id):
    # 检查是否已完成
    if is_analysis_complete(job_id):
        return load_cached_result(job_id)
    
    # 执行分析
    result = do_analysis(job_id)
    
    # 保存结果
    save_result(job_id, result)
    
    return result
```

**实现**: 
- 检查缓存
- 保存中间结果
- 支持断点续传

---

## 📈 性能指标

### 资源使用上限

| 阶段 | CPU | GPU | 内存 | 网络 |
|------|-----|-----|------|------|
| ANALYZING | 50% | 30% | 4GB | 低 |
| PLANNING | 10% | 0% | 1GB | 中 |
| EXECUTING | 70% | 70% | 8GB | 低 |
| EXPORTING | 90% | 90% | 12GB | 低 |

### 超时设置

| 操作 | 超时 | 重试 |
|------|------|------|
| Vision 单帧 | 30秒 | 3次 |
| AI 规划 | 60秒 | 2次 |
| Resolve 操作 | 5秒 | 1次 |
| 导出 | 无限 | 0次 |

---

## 🔧 配置选项

### 环境变量

```bash
# 资源控制
VISION_MAX_SCENES=10
VISION_DEVICE=auto  # auto, cpu, cuda
VISION_TIMEOUT=30

# 调度策略
ALLOW_CONCURRENT_VISION=False
FORCE_CPU_ON_RESOLVE_BUSY=True

# 安全阈值
GPU_USAGE_THRESHOLD=0.7
MEMORY_USAGE_THRESHOLD=0.8
```

---

## 🧪 测试用例

### 测试 1: 资源冲突

```python
def test_resource_conflict():
    # 1. 启动 Resolve Export
    job1 = start_export()
    assert GLOBAL_LOCKS["GPU_HEAVY"] == True
    
    # 2. 尝试启动 Vision
    job2 = start_vision()
    assert job2.status == "DEFERRED"
    
    # 3. Export 完成
    finish_export(job1)
    assert GLOBAL_LOCKS["GPU_HEAVY"] == False
    
    # 4. Vision 自动恢复
    assert job2.status == "RUNNING"
```

### 测试 2: 状态转换

```python
def test_state_transition():
    job = create_job()
    
    # 合法转换
    assert transition(job, INGESTING) == True
    assert transition(job, INGESTED) == True
    assert transition(job, ANALYZING) == True
    
    # 非法转换
    assert transition(job, EXPORTING) == False
```

### 测试 3: 降级处理

```python
def test_vision_fallback():
    # 模拟 Vision 失败
    mock_vision_error()
    
    result = analyze_scene(scene)
    
    # 应该返回默认值，而不是崩溃
    assert result.summary == "未分析"
    assert result.usable == True
```

---

## 📚 API 接口

### 获取系统状态

```bash
GET /api/orchestrator/status
```

**返回**:
```json
{
  "resource_locks": {
    "GPU_HEAVY": false,
    "VISION_ALLOWED": true,
    "RESOLVE_BUSY": false,
    "AI_ALLOWED": true
  },
  "active_jobs": {
    "job_001": "analyzing",
    "job_002": "planning"
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 67.8,
    "memory_available_gb": 8.5
  }
}
```

### 强制状态转换

```bash
POST /api/jobs/{job_id}/transition
{
  "target_state": "analyzing",
  "force": false
}
```

---

## 🎓 最佳实践

### 1. 开发时

```python
# 使用 CPU 模式，避免 GPU 冲突
USE_LOCAL_VISION=True
VISION_DEVICE=cpu
VISION_MAX_SCENES=3
```

### 2. 生产时

```python
# 自动调度，最大性能
USE_LOCAL_VISION=True
VISION_DEVICE=auto
VISION_MAX_SCENES=10
ALLOW_CONCURRENT_VISION=False
```

### 3. 调试时

```python
# 查看状态
curl http://localhost:8000/api/orchestrator/status

# 查看 Job 状态历史
curl http://localhost:8000/api/jobs/{job_id}
```

---

## ✅ 实现检查清单

- [x] 全局资源锁（ResourceLock）
- [x] 状态机（JobState + StateTransition）
- [x] 调度器（Orchestrator）
- [x] Job 管理器集成
- [x] 5 条铁律实现
- [ ] API 接口
- [ ] 测试用例
- [ ] 性能监控
- [ ] 文档完善

---

**文档版本**: v1.0  
**创建日期**: 2026-02-05  
**最后更新**: 2026-02-05
