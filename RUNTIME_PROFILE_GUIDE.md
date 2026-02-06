# Runtime Profile 系统完整指南

**日期**: 2026-02-06  
**版本**: v2.0.0  
**状态**: ✅ 完整实现

---

## 🎯 核心理念

让系统"知道自己在干什么" - 自我感知、自我解释、自我适应

### 三大核心能力

1. **自我感知** - 自动检测硬件配置
2. **自我解释** - 告诉用户为什么这么运行
3. **自我适应** - 动态监控并自动降级

---

## 📊 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   RuntimeProfile                        │
│  (启动时检测，保存到磁盘)                                │
│  - CPU / Memory / GPU                                   │
│  - AI Runtime (Ollama)                                  │
│  - Editor (DaVinci Resolve)                             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                ExecutionPolicyResolver                  │
│  (根据 Profile 生成策略)                                 │
│  - Vision Policy                                        │
│  - Planning Policy                                      │
│  - Editing Policy                                       │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│                   RuntimeMonitor                        │
│  (动态监控，自动降级)                                     │
│  - GPU 显存使用率                                        │
│  - 内存压力                                              │
│  - 任务失败率                                            │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 启动服务器

```bash
cd autocut-director
python run_server.py
```

服务器启动时会自动：
1. 检测硬件配置
2. 生成执行策略
3. 启动运行时监控
4. 保存配置到 `runtime_profile.json`

### 2. 查看运行时状态

```bash
# 访问 API
curl http://localhost:8000/api/runtime/status
```

或访问 Web UI：
```
http://localhost:8000/
```

---

## 📋 Profile 分类

系统根据硬件自动分类为 5 个等级：

### 1. LOCAL_GPU_HIGH（高端工作站）

**硬件要求**:
- GPU: RTX 4090 / 3090 (16GB+ 显存)
- CPU: 16+ 线程
- 内存: 32GB+

**运行策略**:
```json
{
  "vision": {
    "provider": "local",
    "model": "llava-phi3",
    "device": "gpu",
    "max_scenes": 20
  },
  "planning": {
    "provider": "local",
    "model": "qwen2.5-14b"
  },
  "editing": {
    "executor": "davinci",
    "parallelism": 1,
    "preview_quality": "high"
  }
}
```

**特点**: 全本地运行，零成本，最佳性能

---

### 2. LOCAL_GPU_MID（中端配置）⭐ 推荐

**硬件要求**:
- GPU: RTX 4060 / 3060 (8GB 显存)
- CPU: 12+ 线程
- 内存: 16GB+

**运行策略**:
```json
{
  "vision": {
    "provider": "local",
    "model": "moondream",
    "device": "auto",
    "max_scenes": 10
  },
  "planning": {
    "provider": "cloud",
    "model": "deepseek-chat"
  },
  "editing": {
    "executor": "davinci",
    "parallelism": 1,
    "preview_quality": "medium"
  }
}
```

**特点**: 本地视觉分析 + 云端规划，平衡性能和成本

---

### 3. LOCAL_GPU_LOW（低端配置）

**硬件要求**:
- GPU: GTX 1660 / RTX 2060 (4-6GB 显存)
- CPU: 8+ 线程
- 内存: 8GB+

**运行策略**:
```json
{
  "vision": {
    "provider": "local",
    "model": "moondream",
    "device": "cpu",
    "max_scenes": 5
  },
  "planning": {
    "provider": "cloud",
    "model": "deepseek-chat"
  }
}
```

**特点**: CPU 模式视觉分析，限制场景数

---

### 4. LOCAL_CPU_ONLY（无独显）

**硬件要求**:
- GPU: 无或集成显卡
- CPU: 8+ 线程
- 内存: 8GB+

**运行策略**:
```json
{
  "vision": {
    "provider": "cloud",
    "model": "gpt-4o",
    "device": "cpu",
    "max_scenes": 10
  },
  "planning": {
    "provider": "cloud",
    "model": "deepseek-chat"
  }
}
```

**特点**: 全云端 AI 处理

---

### 5. CLOUD_HYBRID（混合模式）

**特点**: 灵活配置，根据需求选择本地/云端

---

## 🔍 运行时监控

### 监控指标

RuntimeMonitor 每 5 秒收集一次指标：

1. **GPU 显存使用率** - 防止 OOM
2. **内存可用量** - 防止系统卡死
3. **CPU 使用率** - 监控负载
4. **Resolve 状态** - 是否繁忙
5. **任务失败率** - 质量监控

### 自动降级规则

| 触发条件 | 降级动作 |
|---------|---------|
| GPU 显存 > 85% | 切换到 CPU 模式 |
| 可用内存 < 2GB | 切换到云端 Vision |
| 任务失败率 > 30% | 切换到云端 Vision |

### 降级示例

```
原始策略:
  Vision: local / moondream (GPU)
  Max Scenes: 10

触发降级: GPU 显存使用率过高 (87%)

降级后策略:
  Vision: cloud / gpt-4o (CPU)
  Max Scenes: 5
```

---

## 🛠️ API 接口

### 1. 获取 Profile

```bash
GET /api/runtime/profile
```

**响应**:
```json
{
  "profile": {
    "cpu": {"cores": 16, "threads": 24, "score": "high"},
    "memory": {"total_gb": 32, "available_gb": 18},
    "gpu": {
      "vendor": "NVIDIA",
      "model": "RTX 4060",
      "vram_gb": 8,
      "cuda": true
    },
    "ai_runtime": {
      "ollama": true,
      "ollama_models": ["moondream"],
      "cuda_available": true
    },
    "profile_class": "LOCAL_GPU_MID"
  },
  "explanation": "🧠 系统运行模式\n- 检测到 NVIDIA RTX 4060 (8GB 显存)\n..."
}
```

### 2. 获取执行策略

```bash
GET /api/runtime/policy
```

**响应**:
```json
{
  "policy": {
    "vision": {
      "provider": "local",
      "model": "moondream",
      "device": "auto",
      "max_scenes": 10
    },
    "planning": {
      "provider": "cloud",
      "model": "deepseek-chat"
    },
    "editing": {
      "executor": "davinci",
      "parallelism": 1,
      "preview_quality": "medium"
    }
  }
}
```

### 3. 获取监控状态

```bash
GET /api/runtime/monitor
```

**响应**:
```json
{
  "running": true,
  "degraded": false,
  "metrics": {
    "gpu": {
      "vram_used_percent": 45.2,
      "vram_used_gb": 3.6,
      "vram_total_gb": 8.0
    },
    "memory": {
      "used_percent": 62.5,
      "available_gb": 12.0
    },
    "cpu": {
      "percent": 35.8
    },
    "resolve_busy": false,
    "task_failure_rate": 0.0
  },
  "task_stats": {
    "total": 10,
    "failed": 0,
    "success_rate": 100.0
  }
}
```

### 4. 获取完整状态

```bash
GET /api/runtime/status
```

**响应**: 包含 Profile + Policy + Monitor + Recommendations

### 5. 手动降级

```bash
POST /api/runtime/policy/degrade?reason=测试降级
```

### 6. 重新检测

```bash
GET /api/runtime/profile/reload
GET /api/runtime/policy/reload
```

---

## 🧪 测试

### 运行测试脚本

```bash
cd autocut-director
python test_runtime_profile.py
```

**测试内容**:
1. RuntimeProfile 自动检测
2. ExecutionPolicy 生成
3. 策略降级
4. RuntimeMonitor 监控
5. 用户友好解释
6. 完整集成测试

---

## 📝 配置文件

### runtime_profile.json

启动时自动生成，保存在项目根目录：

```json
{
  "cpu": {
    "cores": 16,
    "threads": 24,
    "score": "high"
  },
  "memory": {
    "total_gb": 32.0,
    "available_gb": 18.5
  },
  "gpu": {
    "vendor": "NVIDIA",
    "model": "RTX 4060",
    "vram_gb": 8.0,
    "cuda": true
  },
  "ai_runtime": {
    "ollama": true,
    "ollama_models": ["moondream"],
    "cuda_available": true
  },
  "editor": {
    "davinci": {
      "installed": true,
      "version": "20",
      "scriptable": true
    }
  },
  "os": "Windows",
  "profile_class": "LOCAL_GPU_MID",
  "degraded": false,
  "degradation_reason": null
}
```

---

## 🎨 用户界面显示

### 启动时显示

```
============================================================
🚀 AutoCut Director 启动中...
============================================================

📊 检测运行时配置...
✓ 配置文件已保存: runtime_profile.json

🧠 系统运行模式
- 检测到 NVIDIA RTX 4060 (8.0GB 显存)
- CPU: 24 线程 (high 性能)
- 内存: 32.0GB (可用 18.5GB)
- 本地 AI: Ollama (1 个模型)

📊 运行级别: LOCAL_GPU_MID

📋 生成执行策略...
✓ Vision: local / moondream
✓ Planning: cloud / deepseek-chat
✓ Editing: davinci

🔍 启动运行时监控...

============================================================
✅ AutoCut Director 启动完成
============================================================
```

### 降级时显示

```
⚠️  触发自动降级: GPU 显存使用率过高 (87%)

⚠️  自动降级触发: GPU 显存使用率过高 (87%)
  → 降级后 Vision: cloud
```

---

## 🔧 高级用法

### 1. 自定义降级回调

```python
from app.core.runtime_monitor import get_runtime_monitor

monitor = get_runtime_monitor()

def my_callback(reason: str):
    print(f"降级触发: {reason}")
    # 自定义处理逻辑

monitor.register_degradation_callback(my_callback)
```

### 2. 手动检查是否应该使用 CPU

```python
from app.core.runtime_monitor import get_runtime_monitor

monitor = get_runtime_monitor()

if monitor.should_use_cpu_for_vision():
    # 使用 CPU 模式
    pass
```

### 3. 记录任务结果

```python
from app.core.runtime_monitor import get_runtime_monitor

monitor = get_runtime_monitor()

try:
    # 执行任务
    result = do_something()
    monitor.record_task_result(success=True)
except:
    monitor.record_task_result(success=False)
```

---

## 📚 相关文档

- [ORCHESTRATOR_DESIGN.md](ORCHESTRATOR_DESIGN.md) - 状态机和调度算法
- [OLLAMA_INTEGRATION_SUMMARY.md](OLLAMA_INTEGRATION_SUMMARY.md) - 本地视觉模型集成
- [SYSTEM_ARCHITECTURE_V2.md](SYSTEM_ARCHITECTURE_V2.md) - 系统架构总览

---

## ✅ 实现清单

- [x] RuntimeProfile 自动检测
- [x] ExecutionPolicyResolver 策略生成
- [x] RuntimeMonitor 动态监控
- [x] 自动降级机制
- [x] API 接口
- [x] 启动时初始化
- [x] 配置文件保存
- [x] 用户友好解释
- [x] 完整测试脚本
- [x] 文档

---

## 🎯 核心价值

1. **零配置** - 自动检测，开箱即用
2. **自我感知** - 知道自己的硬件能力
3. **自我解释** - 告诉用户为什么这么运行
4. **自我适应** - 动态监控，自动降级
5. **防崩溃** - 永远不会因为资源不足而崩溃

---

**让系统"知道自己在干什么"** ✅
