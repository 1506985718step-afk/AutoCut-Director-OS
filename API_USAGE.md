# AutoCut Director API 使用指南

## 启动服务

### 方法 1: PowerShell 脚本（推荐）
```powershell
.\start.ps1
```

### 方法 2: 手动启动
```powershell
# 1. 设置环境
.\scripts\set_resolve_env.ps1

# 2. 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8787 --reload
```

### 方法 3: Python 脚本
```bash
python run_server.py
```

**服务地址**: http://localhost:8787  
**API 文档**: http://localhost:8787/docs

---

## API 端点

### 1. 根路径
```bash
GET http://localhost:8787/
```

**响应:**
```json
{
  "name": "AutoCut Director",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

---

### 2. 健康检查
```bash
GET http://localhost:8787/health
```

**响应:**
```json
{
  "status": "ok"
}
```

---

### 3. 分析素材（EDL -> scenes.json）

```bash
POST http://localhost:8787/api/analyze
```

**参数:**
- `edl_file`: EDL 文件（multipart/form-data）
- `fps`: 帧率（form field，默认 30）
- `primary_clip_path`: 主素材路径（form field）

**示例（curl）:**
```bash
curl -X POST http://localhost:8787/api/analyze \
  -F "edl_file=@examples/test.edl" \
  -F "fps=30" \
  -F "primary_clip_path=D:/Footage/input.mp4"
```

**示例（PowerShell）:**
```powershell
$form = @{
    edl_file = Get-Item "examples/test.edl"
    fps = "30"
    primary_clip_path = "D:/Footage/input.mp4"
}

Invoke-RestMethod -Uri "http://localhost:8787/api/analyze" `
    -Method Post `
    -Form $form
```

**响应:**
```json
{
  "job_id": "a1b2c3d4",
  "artifacts": {
    "scenes": "scenes.json"
  }
}
```

---

### 4. 获取任务状态

```bash
GET http://localhost:8787/api/analyze/job/{job_id}
```

**示例:**
```bash
curl http://localhost:8787/api/analyze/job/a1b2c3d4
```

**响应:**
```json
{
  "job_id": "a1b2c3d4",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-02-05T10:00:00",
  "updated_at": "2025-02-05T10:00:05",
  "result": {
    "job_id": "a1b2c3d4",
    "artifacts": {
      "scenes": "scenes.json"
    }
  }
}
```

---

### 5. 下载产物

```bash
GET http://localhost:8787/api/analyze/job/{job_id}/artifact/{artifact_name}
```

**示例:**
```bash
# 下载 scenes.json
curl http://localhost:8787/api/analyze/job/a1b2c3d4/artifact/scenes.json \
  -o scenes.json

# 下载 transcript.json
curl http://localhost:8787/api/analyze/job/a1b2c3d4/artifact/transcript.json \
  -o transcript.json
```

---

### 6. 执行剪辑（DSL -> Resolve）

```bash
POST http://localhost:8787/api/execute
```

**参数:**
- `dsl_file`: editing_dsl.json 文件（multipart/form-data）
- `scenes_file`: scenes.json 文件（multipart/form-data）

**示例（curl）:**
```bash
curl -X POST http://localhost:8787/api/execute \
  -F "dsl_file=@examples/editing_dsl.v1.json" \
  -F "scenes_file=@examples/scenes.v1.json"
```

**示例（PowerShell）:**
```powershell
$form = @{
    dsl_file = Get-Item "examples/editing_dsl.v1.json"
    scenes_file = Get-Item "examples/scenes.v1.json"
}

Invoke-RestMethod -Uri "http://localhost:8787/api/execute" `
    -Method Post `
    -Form $form
```

**响应:**
```json
{
  "job_id": "e5f6g7h8",
  "status": "success",
  "trace": [
    {
      "action": "CreateTimeline",
      "params": {"name": "AutoCut_douyin", "fps": 30.0},
      "ok": true,
      "detail": {"result": "success"},
      "took_ms": 150
    },
    {
      "action": "AppendScene",
      "params": {"scene_id": "S0001", "in_frame": 10, "out_frame": 100},
      "ok": true,
      "detail": {"result": "success"},
      "took_ms": 200
    }
  ],
  "output": "output/e5f6g7h8.mp4"
}
```

---

### 7. 验证 DSL（不执行）

```bash
POST http://localhost:8787/api/execute/validate
```

**请求体（JSON）:**
```json
{
  "dsl_data": {
    "meta": {"schema": "editing_dsl.v1", "target": "douyin", "aspect": "9:16"},
    "editing_plan": {
      "timeline": [
        {"order": 1, "scene_id": "S0001", "trim_frames": [10, 100], "purpose": "hook"}
      ],
      "subtitles": {"mode": "from_transcript"},
      "music": {"track_path": "D:/Music/bgm.mp3", "volume_db": -18}
    },
    "export": {"resolution": "1080x1920", "format": "mp4"}
  },
  "scenes_data": {
    "meta": {"schema": "scenes.v1", "fps": 30, "source": "davinci/edl"},
    "media": {"primary_clip_path": "D:/Footage/input.mp4"},
    "scenes": [
      {"scene_id": "S0001", "start_frame": 0, "end_frame": 120}
    ]
  }
}
```

**示例（curl）:**
```bash
curl -X POST http://localhost:8787/api/execute/validate \
  -H "Content-Type: application/json" \
  -d @validate_request.json
```

**响应（成功）:**
```json
{
  "valid": true,
  "errors": []
}
```

**响应（失败）:**
```json
{
  "valid": false,
  "errors": [
    "Scene ID 'S9999' not found in scenes.json",
    "Scene 'S0001': trim_end 999 > scene end 120"
  ]
}
```

---

## 完整工作流示例

### 1. 分析 EDL
```bash
curl -X POST http://localhost:8787/api/analyze \
  -F "edl_file=@timeline.edl" \
  -F "fps=30" \
  -F "primary_clip_path=D:/Footage/input.mp4"
```

**响应:** `{"job_id": "abc123", ...}`

### 2. 下载 scenes.json
```bash
curl http://localhost:8787/api/analyze/job/abc123/artifact/scenes.json \
  -o scenes.json
```

### 3. AI 生成 editing_dsl.json
```python
# 使用 LLM 读取 scenes.json，生成 editing_dsl.json
# 参考 PROTOCOL.md 中的 DSL 生成 prompt
```

### 4. 验证 DSL
```bash
curl -X POST http://localhost:8787/api/execute/validate \
  -H "Content-Type: application/json" \
  -d '{"dsl_data": {...}, "scenes_data": {...}}'
```

### 5. 执行剪辑
```bash
curl -X POST http://localhost:8787/api/execute \
  -F "dsl_file=@editing_dsl.json" \
  -F "scenes_file=@scenes.json"
```

**响应:** `{"job_id": "xyz789", "status": "success", "trace": [...]}`

---

## 错误处理

### 400 Bad Request
```json
{
  "detail": {
    "error": "DSL validation failed (AI hallucination detected)",
    "errors": [
      "Scene ID 'S9999' not found in scenes.json"
    ]
  }
}
```

### 404 Not Found
```json
{
  "detail": "任务不存在"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Cannot connect to DaVinci Resolve. Is Resolve running?"
}
```

---

## 使用 Swagger UI

访问 http://localhost:8787/docs 可以使用交互式 API 文档：

1. 点击端点展开
2. 点击 "Try it out"
3. 填写参数
4. 点击 "Execute"
5. 查看响应

---

## 使用 Python 客户端

```python
import requests

# 1. 分析 EDL
with open("timeline.edl", "rb") as f:
    response = requests.post(
        "http://localhost:8787/api/analyze",
        files={"edl_file": f},
        data={"fps": 30, "primary_clip_path": "D:/Footage/input.mp4"}
    )
    job_id = response.json()["job_id"]

# 2. 下载 scenes.json
response = requests.get(
    f"http://localhost:8787/api/analyze/job/{job_id}/artifact/scenes.json"
)
scenes = response.json()

# 3. 执行剪辑
with open("editing_dsl.json", "rb") as dsl_file, \
     open("scenes.json", "rb") as scenes_file:
    response = requests.post(
        "http://localhost:8787/api/execute",
        files={
            "dsl_file": dsl_file,
            "scenes_file": scenes_file
        }
    )
    result = response.json()
    print(f"执行完成: {result['output']}")
```

---

## 注意事项

1. **Resolve 必须运行**: 执行 `/api/execute` 前确保 DaVinci Resolve 已启动并打开项目
2. **文件路径**: 确保 DSL 中的文件路径（素材、音乐等）存在且可访问
3. **硬规则验证**: 所有 DSL 都会经过硬规则验证，防止 AI 幻觉
4. **Job 管理**: 所有任务都会在 `jobs/` 目录下创建独立文件夹
5. **Trace 日志**: 执行 trace 会保存在 `jobs/{job_id}/trace.json`

---

## 故障排除

### Q: 服务启动失败

**A:** 检查端口是否被占用：
```powershell
netstat -ano | findstr :8787
```

### Q: Resolve 连接失败

**A:** 
1. 确保 Resolve 正在运行
2. 确保已打开项目
3. 检查 RESOLVE_SCRIPT_DIR 环境变量

### Q: 文件上传失败

**A:** 检查文件大小限制和路径是否正确

---

**Happy Editing!** 🎬✨


---

## LLM API - AI 生成剪辑脚本

### 1. 生成 DSL

**端点**: `POST /api/llm/generate-dsl`

**描述**: 使用 LLM 根据场景和转录生成剪辑脚本

**请求**:
```bash
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@examples/scenes.v1.json" \
  -F "transcript_file=@examples/transcript.v1.json" \
  -F "style_prompt=抖音爆款风格：节奏快、文字多、强调关键词"
```

**响应**:
```json
{
  "success": true,
  "dsl": {
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
        "mode": "from_transcript",
        "style": "bold_yellow"
      }
    },
    "export": {
      "resolution": "1080x1920",
      "format": "mp4"
    }
  },
  "meta": {
    "scenes_count": 3,
    "transcript_segments": 5,
    "timeline_items": 4,
    "style": "抖音爆款风格"
  }
}
```

### 2. 验证 DSL

**端点**: `POST /api/llm/validate-dsl`

**描述**: 验证 DSL 硬规则（防止 AI 幻觉）

**请求**:
```bash
curl -X POST http://localhost:8000/api/llm/validate-dsl \
  -F "dsl_file=@examples/editing_dsl.v1.json" \
  -F "scenes_file=@examples/scenes.v1.json"
```

**响应（成功）**:
```json
{
  "valid": true,
  "message": "DSL 验证通过"
}
```

**响应（失败）**:
```json
{
  "valid": false,
  "errors": [
    "Scene S9999 not found in scenes",
    "trim_frames [200, 300] out of range for scene S0001 [0, 120]"
  ]
}
```

### 3. 获取风格预设

**端点**: `GET /api/llm/style-presets`

**描述**: 获取预设的剪辑风格模板

**请求**:
```bash
curl http://localhost:8000/api/llm/style-presets
```

**响应**:
```json
{
  "presets": {
    "douyin": {
      "name": "抖音爆款",
      "description": "节奏快、文字多、强调关键词",
      "prompt": "抖音爆款风格：\n1. 开头 3 秒必须有强烈的 Hook..."
    },
    "bilibili": {
      "name": "B站知识区",
      "description": "节奏适中、字幕完整、强调知识点",
      "prompt": "B站知识区风格：\n1. 开头简短介绍主题..."
    },
    "youtube": {
      "name": "YouTube Vlog",
      "description": "自然流畅、保留情感、适度剪辑",
      "prompt": "YouTube Vlog 风格：\n1. 保持自然的节奏..."
    },
    "kuaishou": {
      "name": "快手热门",
      "description": "接地气、情感强、节奏紧凑",
      "prompt": "快手热门风格：\n1. 开头直接切入主题..."
    }
  }
}
```

### 4. 批量生成

**端点**: `POST /api/llm/batch-generate`

**描述**: 一次性生成多个平台的剪辑脚本

**请求**:
```bash
curl -X POST http://localhost:8000/api/llm/batch-generate \
  -F "scenes_file=@examples/scenes.v1.json" \
  -F "transcript_file=@examples/transcript.v1.json" \
  -F "styles=douyin,bilibili,youtube"
```

**响应**:
```json
{
  "results": {
    "douyin": {
      "success": true,
      "dsl": {...},
      "validation_errors": null
    },
    "bilibili": {
      "success": true,
      "dsl": {...},
      "validation_errors": null
    },
    "youtube": {
      "success": true,
      "dsl": {...},
      "validation_errors": null
    }
  }
}
```

---

## 完整 AI 工作流示例

### 方式 1: 分步调用

```bash
# 1. 分析素材（EDL → scenes.json + Audio → transcript.json）
curl -X POST http://localhost:8000/api/analyze \
  -F "edl_file=@input.edl" \
  -F "audio_file=@input.mp4" \
  -F "fps=30" \
  -F "primary_clip_path=D:/Footage/input.mp4" \
  > analysis_result.json

# 2. AI 生成剪辑脚本
curl -X POST http://localhost:8000/api/llm/generate-dsl \
  -F "scenes_file=@scenes.json" \
  -F "transcript_file=@transcript.json" \
  -F "style_prompt=抖音爆款风格" \
  > dsl_result.json

# 3. 执行剪辑
curl -X POST http://localhost:8000/api/execute \
  -F "dsl_file=@editing_dsl.json" \
  -F "scenes_file=@scenes.json" \
  > execution_result.json
```

### 方式 2: Python 客户端

```python
import requests

# 1. 分析素材
with open("input.edl", "rb") as edl, open("input.mp4", "rb") as audio:
    response = requests.post(
        "http://localhost:8000/api/analyze",
        files={
            "edl_file": edl,
            "audio_file": audio
        },
        data={
            "fps": 30,
            "primary_clip_path": "D:/Footage/input.mp4"
        }
    )
    analysis = response.json()

# 2. AI 生成 DSL
with open("scenes.json", "rb") as scenes, open("transcript.json", "rb") as transcript:
    response = requests.post(
        "http://localhost:8000/api/llm/generate-dsl",
        files={
            "scenes_file": scenes,
            "transcript_file": transcript
        },
        data={
            "style_prompt": "抖音爆款风格：节奏快、文字多、强调关键词"
        }
    )
    dsl_result = response.json()

# 3. 执行剪辑
with open("editing_dsl.json", "rb") as dsl, open("scenes.json", "rb") as scenes:
    response = requests.post(
        "http://localhost:8000/api/execute",
        files={
            "dsl_file": dsl,
            "scenes_file": scenes
        }
    )
    execution = response.json()

print("剪辑完成！")
```

---

## 配置说明

### LLM 配置

在 `.env` 文件中配置：

```bash
# LLM 配置
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=  # 可选：自定义端点
```

### 推荐模型

- **gpt-4o** - 长窗口，JSON 模式支持好（推荐）
- **gpt-4-turbo** - 性能好，成本适中
- **gpt-3.5-turbo** - 成本低，但可能不够稳定

---

## 错误处理

### LLM 相关错误

**错误**: `OPENAI_API_KEY not configured`
```json
{
  "detail": "LLM 调用失败: OPENAI_API_KEY not configured in .env"
}
```
**解决**: 在 `.env` 中配置 API Key

**错误**: `AI 生成了无效的 JSON`
```json
{
  "detail": "LLM 调用失败: AI 生成了无效的 JSON"
}
```
**解决**: 使用支持 JSON 模式的模型（如 gpt-4o）

**错误**: `AI 幻觉检测`
```json
{
  "error": "AI 生成的 DSL 验证失败（AI 幻觉检测）",
  "validation_errors": [
    "Scene S9999 not found in scenes"
  ]
}
```
**解决**: 系统自动拦截，可以重新生成或手动修正

---

更多详细信息请参考：
- [LLM_INTEGRATION.md](LLM_INTEGRATION.md) - LLM 集成完整指南
- [PROTOCOL.md](PROTOCOL.md) - 协议文件规范
- [ARCHITECTURE.md](ARCHITECTURE.md) - 架构设计文档
