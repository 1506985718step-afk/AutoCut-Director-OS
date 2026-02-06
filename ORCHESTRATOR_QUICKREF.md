# Orchestrator 快速参考

**版本**: v3.0.0 | **状态**: ✅ 生产就绪

---

## 🎯 核心原则

```
AI = 导演（决策）
Resolve = 工人（执行）
Orchestrator = 调度员（协调）
```

---

## 📊 状态机

```
CREATED → INGESTING → INGESTED → ANALYZING → ANALYZED
                                      ↓
                                  PLANNING → PLANNED
                                      ↓
                                  EXECUTING → EXPORTING → COMPLETED
```

---

## 🔒 资源锁

| 锁 | 用途 | 何时锁定 |
|---|------|---------|
| GPU_HEAVY | GPU 独占 | EXECUTING, EXPORTING |
| VISION_ALLOWED | Vision 许可 | 除 EXECUTING/EXPORTING 外 |
| RESOLVE_BUSY | Resolve 繁忙 | EXECUTING, EXPORTING |
| AI_ALLOWED | AI 许可 | PLANNING |

---

## 🛡️ 5 条铁律

1. ✅ 任何时间只允许一个 GPU-heavy 任务
2. ✅ Resolve Export > 一切 AI
3. ✅ Vision 失败 ≠ Job 失败
4. ✅ AI 输出不可执行 ≠ Executor 崩溃
5. ✅ 所有步骤必须可重跑

---

## 💻 快速使用

### Python

```python
from app.core.job_store import JobStore
from app.core.orchestrator import JobState

job_store = JobStore()

# 创建 Job
job_id = job_store.create_job()

# 转换状态
job_store.transition_state(job_id, JobState.ANALYZING)

# 查看状态
job = job_store.get_job(job_id)
print(job['state'])
```

### API

```bash
# 系统状态
curl http://localhost:8000/api/orchestrator/status

# 转换状态
curl -X POST http://localhost:8000/api/orchestrator/jobs/job_001/transition \
  -d '{"target_state": "analyzing"}'

# 健康检查
curl http://localhost:8000/api/orchestrator/health
```

---

## 🧪 测试

```powershell
python test_orchestrator.py
```

预期：6/6 通过 (100%)

---

## 📚 完整文档

- **ORCHESTRATOR_DESIGN.md** - 设计文档
- **ORCHESTRATOR_IMPLEMENTATION.md** - 实现文档
- **ORCHESTRATOR_FINAL.md** - 交付总结

---

**创建**: 2026-02-06 | **更新**: 2026-02-06
