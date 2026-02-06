# 快速参考卡片

## 🚀 一键启动

```bash
cd autocut-director
python quick_start.py
```

---

## 📋 核心流程

```
素材 → (本地) 分析 → (远程) AI → (本地) Resolve → 成片
```

### 本地处理
- ✅ EDL 解析 → scenes.json
- ✅ Whisper 转录 → transcript.json
- ✅ Resolve 执行 → 成片

### 远程处理
- ✅ GPT-4o 生成 → editing_dsl.json

---

## 🎨 风格预设

| 风格 | 特点 | 时长 |
|------|------|------|
| 抖音爆款 | 节奏快、文字多 | 30-60s |
| B站知识区 | 节奏适中、完整 | 3-10min |
| YouTube Vlog | 自然流畅 | 5-15min |
| 快手热门 | 情感强、紧凑 | 15-60s |

---

## 📁 三个协议文件

### scenes.v1.json
```json
{
  "scenes": [
    {
      "scene_id": "S0001",
      "start_frame": 0,
      "end_frame": 120
    }
  ]
}
```

### transcript.v1.json
```json
{
  "segments": [
    {
      "start": 0.0,
      "end": 2.8,
      "text": "90%的人第一步就弹错了"
    }
  ]
}
```

### editing_dsl.v1.json
```json
{
  "editing_plan": {
    "timeline": [
      {
        "scene_id": "S0001",
        "trim_frames": [10, 90],
        "overlay_text": "第一步就错了"
      }
    ]
  }
}
```

---

## 🔧 配置

### .env 文件
```bash
# LLM
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o

# Whisper
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
```

---

## 🧪 测试

```bash
# 基础测试
python test_edl_parser.py
python test_dsl_validator.py
python test_actions.py

# LLM 测试
python test_llm_director.py

# SRT 测试
python test_srt_generation.py
```

---

## 📚 文档

| 文档 | 说明 |
|------|------|
| [CORE_LOGIC.md](CORE_LOGIC.md) | 核心逻辑 ⭐ |
| [PIPELINE_GUIDE.md](PIPELINE_GUIDE.md) | 流水线指南 ⭐ |
| [QUICKSTART.md](QUICKSTART.md) | 快速开始 |
| [LLM_INTEGRATION.md](LLM_INTEGRATION.md) | LLM 集成 |
| [SUBTITLE_WORKFLOW.md](SUBTITLE_WORKFLOW.md) | 字幕工作流 |

---

## 🐛 故障排查

### LLM 失败
```
❌ OPENAI_API_KEY not configured
```
→ 配置 `.env` 中的 API Key

### Resolve 失败
```
❌ Cannot connect to DaVinci Resolve
```
→ 启动 Resolve + 运行 `.\scripts\set_resolve_env.ps1`

### 文件不存在
```
⚠️  文件不存在
```
→ 检查文件路径，使用绝对路径

---

## 💡 最佳实践

1. **首次使用** - 用 `quick_start.py` 测试
2. **批量处理** - 用 `run_pipeline.py` + 命令行参数
3. **自动化** - 用 Python API 集成
4. **离线模式** - 跳过 LLM，使用预设 DSL

---

## 📊 性能

| 阶段 | 时间 | 位置 |
|------|------|------|
| EDL 解析 | < 1s | 本地 |
| Whisper (base) | 1-2min | 本地 |
| GPT-4o | 10-30s | 远程 |
| Resolve 执行 | 2-5min | 本地 |
| **总计** | **3-8min** | |

---

## 🎯 命令速查

```bash
# 快速启动
python quick_start.py

# 完整流水线
python run_pipeline.py --edl input.edl --audio input.mp4 --output output.mp4

# 启动 API 服务
python run_server.py

# 运行测试
python test_edl_parser.py
```

---

**开始使用**: `python quick_start.py`
