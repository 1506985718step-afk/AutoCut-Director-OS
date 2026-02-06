# AutoCut Director

🧠 AI 驱动的自动视频剪辑系统 - 让 AI 成为你的剪辑导演

## ✨ 核心特性

### 🎯 三个协议文件驱动

1. **scenes.json** - 场景切分（EDL/FCPXML 解析）
2. **transcript.json** - 音频转录（Whisper ASR）
3. **editing_dsl.json** - 剪辑指令（AI 生成，唯一指挥通道）

### 🔍 Content Modality Analyzer - 0 号步骤（v2.1.0 新增）⭐

- ✅ **极轻量分析**：< 1 秒判断"用耳朵听"还是"用眼睛看"
- ✅ **智能决策**：5 种模式（ASR_PRIMARY/VISION_PRIMARY/HYBRID）
- ✅ **三级音频匹配**：显式/时间戳/波形匹配
- ✅ **选择性 Vision**：避免不必要的 Vision 调用，节省 50-90% 成本
- ✅ **完整流水线**：Ingest → Triage → Match → Modality → ASR/Vision → Fuse

### 🧠 Runtime Profile - 自我感知系统（v2.0.0）

- ✅ **自我感知**：自动检测硬件配置（CPU/GPU/内存）
- ✅ **自我解释**：告诉用户为什么这么运行
- ✅ **自我适应**：动态监控，自动降级防崩溃
- ✅ **零配置**：开箱即用，智能选择最佳策略
- ✅ **5 个等级**：从高端工作站到纯 CPU 自动适配

### 👁️ 视觉分析 - AI 导演的"眼睛"（v1.8.0）

- ✅ 本地模型（Ollama）+ 云端模型（GPT-4o）双模式
- ✅ 识别景别、主体、情绪、光线
- ✅ 智能镜头选择（内容匹配、情绪流控制）
- ✅ 遵循蒙太奇原则（景别组接）
- ✅ 质量优先（自动评分 1-10）

### 🎬 Visual Storyteller - 无脚本模式（v1.9.0）

- ✅ 从零散素材自动构思故事线
- ✅ 智能聚类（人物、风景、物品）
- ✅ 创意构思（提供多个主题方案）
- ✅ 自动编剧（生成配套文案）
- ✅ 完整输出（transcript + DSL）

### 🤖 全自动导演模式（v2.0.0）

- ✅ **一键式工作流**：扔进视频，吐出故事
- ✅ **OS 进程管理**：自动启动/监控 Resolve
- ✅ **Smart Bins**：AI 自动归类素材
- ✅ **完整闭环**：从上传到剪辑全自动化
- ✅ **状态机调度**：防止资源冲突和系统崩溃

### 🧠 LLM Director - AI 大脑

- ✅ 根据素材自动生成剪辑脚本
- ✅ 支持多平台风格（抖音、B站、YouTube、快手）
- ✅ 硬规则验证，防止 AI 幻觉
- ✅ 批量生成，一次性输出多个平台版本
- ✅ **视觉增强**：根据画面内容智能选择镜头

### 🎬 智能字幕渲染

- ✅ 从 transcript 自动生成完整字幕
- ✅ 支持文字叠加（overlay_text）
- ✅ 三种预设样式（抖音、简洁、优雅）
- ✅ 完全自定义样式（字体、颜色、位置、描边）

### 🔒 硬规则验证

- ✅ scene_id 存在性检查
- ✅ trim_frames 范围验证
- ✅ trim_frames 顺序验证
- ✅ 防止 AI 幻觉，确保可执行

## 🚀 快速开始

> ⚠️ **DaVinci Resolve 用户必读**：如果遇到项目创建问题，请先查看 [RESOLVE_快速修复.md](RESOLVE_快速修复.md)

### 1. 安装

```bash
# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置 Resolve
.\scripts\set_resolve_env.ps1
```

详见 [INSTALL.md](INSTALL.md)

### 1.5 验证 Resolve 连接（推荐）

```bash
# 运行诊断工具
python diagnose_resolve.py
```

诊断工具会检查：
- ✅ 环境变量配置
- ✅ Resolve 连接状态
- ✅ 项目是否打开
- ✅ 提供修复建议

### 2. 配置 LLM

在 `.env` 文件中：

```bash
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o

# 本地视觉模型（推荐，零成本）
USE_LOCAL_VISION=True
LOCAL_VISION_MODEL=moondream
OLLAMA_HOST=http://localhost:11434
```

**推荐安装 Ollama**（本地视觉分析，零成本）：
```bash
# 下载安装包
https://ollama.com/download/windows

# 下载模型
ollama pull moondream
```

详见 [OLLAMA_SETUP_GUIDE.md](OLLAMA_SETUP_GUIDE.md)

### 3. 启动服务

```bash
python run_server.py
```

服务运行在 `http://localhost:8000`

**启动时自动**：
- ✅ 检测硬件配置（CPU/GPU/内存）
- ✅ 生成执行策略（本地/云端）
- ✅ 启动运行时监控
- ✅ 保存配置到 `runtime_profile.json`

详见 [RUNTIME_PROFILE_QUICKREF.md](RUNTIME_PROFILE_QUICKREF.md)

### 4. 完整工作流

```bash
# 1. 分析素材（生成 scenes.json + transcript.json）
curl -X POST http://localhost:8000/api/analyze \
  -F "edl_file=@timeline.edl" \
  -F "audio_file=@audio.mp3"

# 2. 视觉分析（可选，让 AI 导演"看懂"画面）
curl -X POST http://localhost:8000/api/visual/analyze-from-job \
  -F "job_id=job_xxx"

# 3. AI 生成剪辑脚本
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@scenes_with_visual.json" \
  -F "transcript_file=@transcript.json" \
  -F "style_prompt=抖音爆款风格"

# 4. 执行剪辑（自动化字幕 + 文字叠加）
curl -X POST http://localhost:8000/api/execute \
  -F "dsl_file=@editing_dsl.json" \
  -F "scenes_file=@scenes.json"
```

## 协议文件示例

### scenes.json
```json
{
  "meta": { "schema": "scenes.v1", "fps": 30, "source": "davinci/edl" },
  "media": { "primary_clip_path": "D:/Footage/input.mp4" },
  "scenes": [
    { "scene_id": "S0001", "start_frame": 0, "end_frame": 120 }
  ]
}
```

### editing_dsl.json
```json
{
  "meta": { "schema": "editing_dsl.v1", "target": "douyin", "aspect": "9:16" },
  "editing_plan": {
    "timeline": [
      { "order": 1, "scene_id": "S0001", "trim_frames": [10, 90], "purpose": "hook" }
    ],
    "subtitles": { "mode": "from_transcript" },
    "music": { "track_path": "D:/Music/bgm.mp3", "volume_db": -18 }
  },
  "export": { "resolution": "1080x1920", "format": "mp4" }
}
```

完整协议规范见 [PROTOCOL.md](PROTOCOL.md)

## 架构

```
autocut-director/
├── app/
│   ├── main.py              # FastAPI 入口
│   ├── api/
│   │   ├── routes_analyze.py   # 分析路由
│   │   └── routes_execute.py   # 执行路由（含硬规则验证）
│   ├── models/
│   │   └── schemas.py          # 三个协议的 Pydantic 模型
│   ├── core/
│   │   ├── job_store.py        # Job 管理
│   │   └── timecode.py         # TC <-> Frame 转换
│   ├── tools/
│   │   ├── scene_from_edl.py   # EDL -> scenes.json
│   │   └── asr_whisper.py      # Whisper ASR
│   └── executor/
│       ├── runner.py           # 动作队列执行
│       ├── actions.py          # Resolve 操作封装
│       └── resolve_adapter.py  # DaVinci API 适配器
├── examples/                # 协议文件示例
├── scripts/                 # 环境配置脚本
└── jobs/                    # 任务目录（自动创建）
```

## 硬规则验证

```python
# Executor 执行前必须检查
DSLValidator.validate_dsl_against_scenes(dsl, scenes)

# 检查项：
# 1. scene_id 是否存在于 scenes.json
# 2. trim_frames 是否在场景帧范围内
# 3. trim_frames 顺序是否正确

# 任何失败 -> 拒绝执行 -> 返回详细错误
```

## 文档

- [SYSTEM_ARCHITECTURE_V2.md](SYSTEM_ARCHITECTURE_V2.md) - 系统架构总览 🆕
- [INSTALL.md](INSTALL.md) - 安装指南
- [PROTOCOL.md](PROTOCOL.md) - 协议文件规范
- [SETUP.md](SETUP.md) - Resolve 环境配置
- [VISUAL_ANALYSIS_GUIDE.md](VISUAL_ANALYSIS_GUIDE.md) - 视觉分析功能指南
- [VISUAL_STORYTELLER_GUIDE.md](VISUAL_STORYTELLER_GUIDE.md) - 无脚本模式指南
- [FULL_AUTO_DIRECTOR_GUIDE.md](FULL_AUTO_DIRECTOR_GUIDE.md) - 全自动导演模式指南

## 依赖

- Python 3.11+
- DaVinci Resolve Studio (脚本 API)
- FFmpeg (faster-whisper 需要)

## 开发路线

- ✅ MVP v1: 三个协议文件 + 硬规则验证
- ✅ EDL 解析器
- ✅ Whisper ASR
- ✅ Resolve Adapter 基础功能
- ⏳ 多素材支持
- ⏳ 转场效果
- ⏳ 动态字幕样式

## License

MIT
