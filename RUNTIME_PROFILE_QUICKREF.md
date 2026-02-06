# Runtime Profile 快速参考

## 🚀 一分钟上手

### 启动服务器
```bash
python run_server.py
```

系统自动：
1. ✅ 检测硬件
2. ✅ 生成策略
3. ✅ 启动监控
4. ✅ 保存配置

---

## 📊 5 个 Profile 等级

| 等级 | GPU | 显存 | Vision | Planning |
|------|-----|------|--------|----------|
| **LOCAL_GPU_HIGH** | 4090/3090 | 16GB+ | 本地 llava-phi3 | 本地 qwen2.5 |
| **LOCAL_GPU_MID** ⭐ | 4060/3060 | 8GB | 本地 moondream | 云端 deepseek |
| **LOCAL_GPU_LOW** | 1660/2060 | 4-6GB | 本地 CPU 模式 | 云端 deepseek |
| **LOCAL_CPU_ONLY** | 无独显 | - | 云端 gpt-4o | 云端 deepseek |
| **CLOUD_HYBRID** | 混合 | - | 云端 | 云端 |

---

## 🔍 监控指标

每 5 秒检查：
- GPU 显存使用率
- 内存可用量
- CPU 使用率
- Resolve 状态
- 任务失败率

---

## ⚠️ 自动降级规则

| 触发条件 | 动作 |
|---------|------|
| GPU 显存 > 85% | → CPU 模式 |
| 可用内存 < 2GB | → 云端 Vision |
| 任务失败率 > 30% | → 云端 Vision |

---

## 🛠️ 常用 API

```bash
# 查看完整状态
GET /api/runtime/status

# 查看 Profile
GET /api/runtime/profile

# 查看策略
GET /api/runtime/policy

# 查看监控
GET /api/runtime/monitor

# 重新检测
GET /api/runtime/profile/reload

# 手动降级
POST /api/runtime/policy/degrade?reason=测试
```

---

## 🧪 测试

```bash
python test_runtime_profile.py
```

---

## 📝 配置文件

自动生成：`runtime_profile.json`

```json
{
  "profile_class": "LOCAL_GPU_MID",
  "gpu": {"model": "RTX 4060", "vram_gb": 8},
  "ai_runtime": {"ollama": true, "ollama_models": ["moondream"]},
  "degraded": false
}
```

---

## 💡 推荐配置

### 中端配置（最佳性价比）
- GPU: RTX 4060 (8GB)
- CPU: 16 线程
- 内存: 32GB
- Ollama: moondream

**成本**: 本地 Vision（零成本）+ 云端 Planning（低成本）

---

## 🎯 核心理念

**让系统"知道自己在干什么"**

1. 自我感知 - 自动检测硬件
2. 自我解释 - 告诉用户为什么
3. 自我适应 - 动态监控降级

---

## 📚 完整文档

详见：[RUNTIME_PROFILE_GUIDE.md](RUNTIME_PROFILE_GUIDE.md)
