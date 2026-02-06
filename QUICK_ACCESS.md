# AutoCut Director - 快速访问

## 🚀 启动服务器

```bash
cd autocut-director
python run_server.py
```

## 🌐 访问地址

| 功能 | 地址 | 说明 |
|------|------|------|
| **用户界面** | http://localhost:8787/ | 主要使用入口 |
| **管理界面** | http://localhost:8787/admin | 重定向到 API 文档 |
| **API 文档** | http://localhost:8787/docs | Swagger UI（开发者） |
| **健康检查** | http://localhost:8787/health | 服务器状态 |

## 📋 使用流程

### 1️⃣ 上传视频
- 拖拽或选择视频文件
- 选择平台（抖音/B站/YouTube/快手）
- 选择风格（爆款/教学/情感/Vlog）
- 点击"开始 AI 剪辑"

### 2️⃣ 等待处理
- 视频导入 → 音频分析 → 场景拆分 → AI 生成 → 自动剪辑
- 预计时间: 3-5 分钟

### 3️⃣ 预览修改
- 查看视频预览
- 查看剪辑摘要
- 意图式调整（Hook/节奏/BGM/字幕）
- 满意后点击"导出成片"

### 4️⃣ 导出下载
- 选择质量（1080p / 4K）
- 下载成片
- 管理历史版本

## 🎯 意图调整选项

| 调整 | 效果 |
|------|------|
| 🔥 Hook 更狠 | 使用更强烈的开场片段 |
| 💝 Hook 更温和 | 使用更柔和的开场片段 |
| ⚡ 节奏更快 | 加快剪辑节奏，删除更多停顿 |
| 🐢 节奏更慢 | 放慢剪辑节奏，保留更多内容 |
| 🎵 换一首音乐 | 更换背景音乐 |
| 📝 字幕更大 | 增大字幕尺寸 |

## 🔧 开发者 API

### 主要端点

```bash
# 上传视频
POST /api/ingest/
  -F "video=@video.mp4"
  -F "extract_audio=true"

# 生成剪辑方案
POST /api/llm/generate-dsl
  -F "scenes_file=@scenes.json"
  -F "transcript_file=@transcript.json"
  -F "style_prompt=抖音爆款风格"

# 执行剪辑
POST /api/execute/run
  -F "dsl_file=@editing_dsl.json"

# 获取 job 状态
GET /api/jobs/{job_id}

# 获取预览视频
GET /api/jobs/{job_id}/preview?quality=480p

# 下载成片
GET /api/jobs/{job_id}/download/output/final.mp4
```

## 📁 文件位置

```
jobs/{job_id}/
├── input/          # 原始视频和音频
├── temp/           # 临时文件和预览
└── output/         # 最终成片
```

## ⚠️ 常见问题

### 服务器无法启动
```bash
# 检查端口占用
netstat -ano | findstr :8787

# 检查 Python 环境
python --version
pip list | findstr fastapi
```

### 视频上传失败
- 检查文件大小（< 2GB）
- 检查文件格式（MP4/MOV/AVI）
- 检查磁盘空间

### 预览无法播放
- 检查浏览器支持（Chrome/Edge 推荐）
- 刷新页面
- 检查服务器日志

### Resolve 连接失败
- 确保 DaVinci Resolve 已启动
- 检查 Resolve 脚本 API 设置
- 检查环境变量 `RESOLVE_SCRIPT_API`

## 📚 相关文档

| 文档 | 说明 |
|------|------|
| `USER_GUIDE.md` | 详细用户指南 |
| `FLOW_UI_UPDATE.md` | UI 更新说明 |
| `API_USAGE.md` | API 使用指南 |
| `ARCHITECTURE.md` | 系统架构 |
| `QUICKSTART.md` | 快速开始 |

## 🎬 视频格式支持

| 格式 | 支持 | 推荐 |
|------|------|------|
| MP4 | ✅ | ⭐⭐⭐ |
| MOV | ✅ | ⭐⭐ |
| AVI | ✅ | ⭐ |
| MKV | ⚠️ | 需转换 |
| FLV | ❌ | 不支持 |

## 🎨 平台规格

| 平台 | 分辨率 | 比例 | 时长 |
|------|--------|------|------|
| 抖音 | 1080×1920 | 9:16 | 15-60s |
| 快手 | 1080×1920 | 9:16 | 15-60s |
| B站 | 1920×1080 | 16:9 | 3-10min |
| YouTube | 1920×1080 | 16:9 | 5-15min |

## 🔐 环境变量

```bash
# .env 文件
DEEPSEEK_API_KEY=sk-676928216d4d41dca06428f254cbd069
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
RESOLVE_SCRIPT_API=C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting
```

## 📊 系统要求

- **操作系统**: Windows 10/11
- **Python**: 3.9+
- **内存**: 8GB+
- **磁盘**: 20GB+ 可用空间
- **DaVinci Resolve**: 19.0+

## 🆘 获取帮助

1. 查看日志: `jobs/{job_id}/trace.json`
2. 查看 API 文档: http://localhost:8787/docs
3. 查看详细指南: `USER_GUIDE.md`
4. 查看架构文档: `ARCHITECTURE.md`

---

**版本**: v1.4.0  
**更新**: 2026-02-05  
**状态**: ✅ 生产就绪
