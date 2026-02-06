# UI → API 时序图

## 前端怎么一步步调后端

---

## 场景 1：新建剪辑（Create → Processing）

### 用户操作
1. 上传视频
2. 选择平台：抖音
3. 选择风格：爆款短视频
4. 点击"开始自动剪辑"

### API 调用时序

```
前端                                后端 API                              后端处理
│                                   │                                     │
│ 1. 上传视频                       │                                     │
├──────────────────────────────────>│ POST /api/create-project            │
│   FormData:                       │                                     │
│   - video: File                   │                                     │
│   - platform: "douyin"            │                                     │
│   - style: "viral"                │                                     │
│   - pace: "fast"                  │                                     │
│   - subtitle_density: "standard"  │                                     │
│   - music_preference: "emotional" │                                     │
│                                   ├────────────────────────────────────>│
│                                   │                                     │ 1. 创建 project_id
│                                   │                                     │ 2. 保存视频到 jobs/{project_id}/input/
│                                   │                                     │ 3. 提取音频（ffmpeg）
│                                   │                                     │ 4. 启动后台任务
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "project_id": "proj_20260205_143000",                              │
│     "status": "processing",       │                                     │
│     "message": "剪辑已开始"        │                                     │
│   }                               │                                     │
│                                   │                                     │
│ 2. 轮询进度（每 2 秒）             │                                     │
├──────────────────────────────────>│ GET /api/projects/{project_id}/status
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "project_id": "...",          │                                     │
│     "status": "processing",       │                                     │
│     "progress": 35,               │                                     │
│     "current_step": "audio_analysis",                                  │
│     "steps": [                    │                                     │
│       {"name": "video_import", "status": "completed"},                 │
│       {"name": "audio_analysis", "status": "active"},                  │
│       {"name": "scene_detection", "status": "pending"},                │
│       {"name": "dsl_generation", "status": "pending"},                 │
│       {"name": "editing", "status": "pending"}                         │
│     ],                            │                                     │
│     "estimated_remaining": 90     │                                     │
│   }                               │                                     │
│                                   │                                     │
│ 3. 继续轮询...                     │                                     │
│ （直到 status = "completed"）      │                                     │
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "status": "completed",        │                                     │
│     "progress": 100,              │                                     │
│     "preview_url": "/api/projects/{project_id}/preview"                │
│   }                               │                                     │
│                                   │                                     │
│ 4. 跳转到预览页面                  │                                     │
│                                   │                                     │
```

### 后端内部流程（用户不可见）

```
POST /api/create-project
    ↓
1. UITranslator.translate_platform("douyin")
   → meta.target_platform = "douyin"
   → meta.aspect_ratio = "9:16"
   
2. UITranslator.translate_style("viral")
   → style_prompt = "抖音爆款风格：节奏快、文字多..."
   
3. 保存视频 → jobs/{project_id}/input/video.mp4

4. 提取音频 → jobs/{project_id}/temp/audio.wav
   POST /api/ingest/extract-audio (内部调用)

5. 启动后台任务：
   - ASR（Whisper）→ transcript.json
   - 场景检测 → scenes.json
   - LLM 生成 DSL → editing_dsl.json
   - Resolve 执行 → output/final.mp4
   - 生成预览 → temp/preview_480p.mp4

6. 返回 project_id
```

---

## 场景 2：预览与调整（Review → Re-generate）

### 用户操作
1. 查看预览视频
2. 觉得节奏太慢
3. 选择"节奏 → 更快"
4. 点击"重新生成"

### API 调用时序

```
前端                                后端 API                              后端处理
│                                   │                                     │
│ 1. 加载预览页面                    │                                     │
├──────────────────────────────────>│ GET /api/projects/{project_id}      │
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "project_id": "...",          │                                     │
│     "current_version": 1,         │                                     │
│     "summary": {                  │                                     │
│       "hook": "第 3 个场景（0:12–0:18）",                              │
│       "pace": "中等偏快",          │                                     │
│       "music": "情绪型（120 BPM）",│                                     │
│       "duration": "45s"           │                                     │
│     },                            │                                     │
│     "preview_url": "/api/projects/{project_id}/preview"                │
│   }                               │                                     │
│                                   │                                     │
│ 2. 加载预览视频                    │                                     │
├──────────────────────────────────>│ GET /api/projects/{project_id}/preview
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK (video/mp4)                  │
│   [视频流]                         │                                     │
│                                   │                                     │
│ 3. 用户调整：节奏更快               │                                     │
├──────────────────────────────────>│ POST /api/projects/{project_id}/adjust
│   {                               │                                     │
│     "adjustments": {              │                                     │
│       "pace": "faster",           │                                     │
│       "hook": "keep",             │                                     │
│       "music": "keep",            │                                     │
│       "subtitle": "keep"          │                                     │
│     }                             │                                     │
│   }                               │                                     │
│                                   ├────────────────────────────────────>│
│                                   │                                     │ 1. 创建新版本 v2
│                                   │                                     │ 2. 获取原 DSL (v1)
│                                   │                                     │ 3. UITranslator.translate_adjustment("pace", "faster")
│                                   │                                     │    → prompt_append = "节奏太慢，请加快..."
│                                   │                                     │ 4. 重新调用 LLM
│                                   │                                     │    new_dsl = llm_engine.generate_dsl(
│                                   │                                     │        scenes, transcript,
│                                   │                                     │        original_prompt + prompt_append
│                                   │                                     │    )
│                                   │                                     │ 5. 保存新 DSL → jobs/{project_id}_v2/dsl.json
│                                   │                                     │ 6. 执行新 DSL → Resolve
│                                   │                                     │ 7. 生成新预览
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "project_id": "...",          │                                     │
│     "new_version": 2,             │                                     │
│     "status": "processing",       │                                     │
│     "message": "正在重新生成..."   │                                     │
│   }                               │                                     │
│                                   │                                     │
│ 4. 轮询新版本进度                  │                                     │
├──────────────────────────────────>│ GET /api/projects/{project_id}/status?version=2
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "status": "processing",       │                                     │
│     "progress": 60,               │                                     │
│     "current_step": "editing"     │                                     │
│   }                               │                                     │
│                                   │                                     │
│ 5. 完成后自动刷新预览               │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "status": "completed",        │                                     │
│     "progress": 100,              │                                     │
│     "preview_url": "/api/projects/{project_id}/preview?version=2"      │
│   }                               │                                     │
│                                   │                                     │
```

---

## 场景 3：导出成片（Export）

### 用户操作
1. 满意当前版本
2. 选择导出质量：1080p
3. 点击"导出成片"
4. 下载视频

### API 调用时序

```
前端                                后端 API                              后端处理
│                                   │                                     │
│ 1. 请求导出                        │                                     │
├──────────────────────────────────>│ POST /api/projects/{project_id}/export
│   {                               │                                     │
│     "version": 2,                 │                                     │
│     "quality": "1080p"            │                                     │
│   }                               │                                     │
│                                   ├────────────────────────────────────>│
│                                   │                                     │ 1. 检查版本是否存在
│                                   │                                     │ 2. 从 Resolve 导出最终成片
│                                   │                                     │    → jobs/{project_id}_v2/output/final.mp4
│                                   │                                     │ 3. 如果需要转码（4K），使用 ffmpeg
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "export_id": "export_123",    │                                     │
│     "status": "exporting",        │                                     │
│     "message": "正在导出..."       │                                     │
│   }                               │                                     │
│                                   │                                     │
│ 2. 轮询导出进度                    │                                     │
├──────────────────────────────────>│ GET /api/exports/{export_id}/status │
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "status": "completed",        │                                     │
│     "download_url": "/api/exports/{export_id}/download"                │
│   }                               │                                     │
│                                   │                                     │
│ 3. 下载成片                        │                                     │
├──────────────────────────────────>│ GET /api/exports/{export_id}/download
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK (video/mp4)                  │
│   [视频文件流]                     │                                     │
│                                   │                                     │
```

---

## 场景 4：查看历史版本（History）

### 用户操作
1. 进入导出页面
2. 查看历史版本列表
3. 预览 V1 版本
4. 切换回 V2 版本

### API 调用时序

```
前端                                后端 API                              后端处理
│                                   │                                     │
│ 1. 获取项目所有版本                 │                                     │
├──────────────────────────────────>│ GET /api/projects/{project_id}/versions
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "project_id": "...",          │                                     │
│     "versions": [                 │                                     │
│       {                           │                                     │
│         "version": 1,             │                                     │
│         "created_at": "2026-02-05T14:30:00Z",                          │
│         "summary": {              │                                     │
│           "pace": "中",            │                                     │
│           "music": "情绪型"        │                                     │
│         },                        │                                     │
│         "preview_url": "/api/projects/{project_id}/preview?version=1"  │
│       },                          │                                     │
│       {                           │                                     │
│         "version": 2,             │                                     │
│         "created_at": "2026-02-05T14:35:00Z",                          │
│         "summary": {              │                                     │
│           "pace": "快",            │                                     │
│           "music": "情绪型"        │                                     │
│         },                        │                                     │
│         "preview_url": "/api/projects/{project_id}/preview?version=2",│
│         "is_current": true        │                                     │
│       }                           │                                     │
│     ]                             │                                     │
│   }                               │                                     │
│                                   │                                     │
│ 2. 预览 V1 版本                    │                                     │
├──────────────────────────────────>│ GET /api/projects/{project_id}/preview?version=1
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK (video/mp4)                  │
│   [V1 视频流]                      │                                     │
│                                   │                                     │
│ 3. 切换到 V1 作为当前版本           │                                     │
├──────────────────────────────────>│ POST /api/projects/{project_id}/switch-version
│   {                               │                                     │
│     "version": 1                  │                                     │
│   }                               │                                     │
│                                   │                                     │
│<──────────────────────────────────┤ 200 OK                              │
│   {                               │                                     │
│     "message": "已切换到 V1",      │                                     │
│     "current_version": 1          │                                     │
│   }                               │                                     │
│                                   │                                     │
```

---

## API 端点总结

### 核心 API（产品级）

| 端点 | 方法 | 说明 | 用户可见 |
|------|------|------|---------|
| `/api/create-project` | POST | 创建新项目 | ✅ |
| `/api/projects/{id}/status` | GET | 获取项目状态 | ✅ |
| `/api/projects/{id}` | GET | 获取项目详情 | ✅ |
| `/api/projects/{id}/preview` | GET | 获取预览视频 | ✅ |
| `/api/projects/{id}/adjust` | POST | 调整项目 | ✅ |
| `/api/projects/{id}/export` | POST | 导出成片 | ✅ |
| `/api/projects/{id}/versions` | GET | 获取所有版本 | ✅ |
| `/api/exports/{id}/download` | GET | 下载成片 | ✅ |

### 内部 API（开发者可见）

| 端点 | 方法 | 说明 | 用户可见 |
|------|------|------|---------|
| `/api/ingest/*` | * | 素材预处理 | ❌ |
| `/api/analyze/*` | * | 场景分析 | ❌ |
| `/api/llm/*` | * | LLM 生成 | ❌ |
| `/api/execute/*` | * | Resolve 执行 | ❌ |
| `/api/jobs/*` | * | Job 管理 | ❌ |

---

## 前端实现示例

### 1. 创建项目

```javascript
async function createProject(formData) {
    const response = await fetch('/api/create-project', {
        method: 'POST',
        body: formData
    });
    
    const result = await response.json();
    
    if (result.status === 'processing') {
        // 跳转到处理页面
        window.location.href = `/processing?project_id=${result.project_id}`;
    }
}
```

### 2. 轮询进度

```javascript
async function pollProgress(projectId) {
    const interval = setInterval(async () => {
        const response = await fetch(`/api/projects/${projectId}/status`);
        const status = await response.json();
        
        // 更新 UI
        updateProgressBar(status.progress);
        updateTimeline(status.steps);
        
        if (status.status === 'completed') {
            clearInterval(interval);
            // 跳转到预览页面
            window.location.href = `/review?project_id=${projectId}`;
        }
    }, 2000);  // 每 2 秒轮询一次
}
```

### 3. 调整项目

```javascript
async function adjustProject(projectId, adjustments) {
    const response = await fetch(`/api/projects/${projectId}/adjust`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({adjustments})
    });
    
    const result = await response.json();
    
    if (result.status === 'processing') {
        // 显示处理中提示
        showProcessingModal();
        // 轮询新版本进度
        pollProgress(projectId, result.new_version);
    }
}
```

---

## 关键设计决策

### 1. 为什么用轮询而不是 WebSocket？
- ✅ 实现简单
- ✅ 兼容性好
- ✅ 适合 MVP
- ⚠️ 后续可升级为 WebSocket

### 2. 为什么每次调整都创建新版本？
- ✅ 可回溯
- ✅ 用户可对比
- ✅ 不会丢失之前的工作
- ✅ 符合"导演"心智模型

### 3. 为什么预览和成片分开？
- ✅ 预览快速（480p）
- ✅ 成片高质量（1080p/4K）
- ✅ 节省带宽和存储

---

**版本**: v1.5.0  
**日期**: 2026-02-05  
**状态**: 产品级 API 设计
