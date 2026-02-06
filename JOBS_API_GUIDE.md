# Jobs API 使用指南

## 🎯 概述

Jobs API 提供完整的任务管理功能，包括：
- 📊 查询任务状态和进度
- 📁 获取任务产物文件列表
- 📝 查看执行 trace 摘要
- 🎬 获取低码率预览视频
- ⬇️ 下载任务产物文件

---

## 📋 API 端点

### 1. GET /api/jobs/{job_id}

**功能**: 获取任务状态 + artifacts 列表 + trace 摘要

**请求**:
```bash
curl http://localhost:8000/api/jobs/job_20250205_143022
```

**响应**:
```json
{
  "job_id": "job_20250205_143022",
  "status": "completed",
  "progress": 100,
  "created_at": "2025-02-05T14:30:22",
  "updated_at": "2025-02-05T14:38:15",
  "error": null,
  "artifacts": {
    "input": [
      {
        "name": "input.mp4",
        "path": "job_20250205_143022/input/input.mp4",
        "size": 52428800,
        "modified": "2025-02-05T14:30:25"
      },
      {
        "name": "timeline.edl",
        "path": "job_20250205_143022/input/timeline.edl",
        "size": 2048,
        "modified": "2025-02-05T14:31:10"
      }
    ],
    "temp": [
      {
        "name": "input.wav",
        "path": "job_20250205_143022/temp/input.wav",
        "size": 10485760,
        "modified": "2025-02-05T14:30:45"
      }
    ],
    "output": [
      {
        "name": "scenes.json",
        "path": "job_20250205_143022/output/scenes.json",
        "size": 4096,
        "modified": "2025-02-05T14:32:00"
      },
      {
        "name": "transcript.json",
        "path": "job_20250205_143022/output/transcript.json",
        "size": 8192,
        "modified": "2025-02-05T14:34:30"
      },
      {
        "name": "editing_dsl.json",
        "path": "job_20250205_143022/output/editing_dsl.json",
        "size": 6144,
        "modified": "2025-02-05T14:35:15"
      },
      {
        "name": "trace.json",
        "path": "job_20250205_143022/output/trace.json",
        "size": 3072,
        "modified": "2025-02-05T14:38:10"
      },
      {
        "name": "final.mp4",
        "path": "job_20250205_143022/output/final.mp4",
        "size": 31457280,
        "modified": "2025-02-05T14:38:15"
      }
    ]
  },
  "trace_summary": {
    "total_actions": 10,
    "successful": 10,
    "failed": 0,
    "total_time_ms": 5432
  }
}
```

**字段说明**:
- `status`: 任务状态（created/processing/completed/failed）
- `progress`: 进度（0-100）
- `artifacts`: 产物文件列表，按类别分组
  - `input`: 输入文件（视频、EDL）
  - `temp`: 临时文件（音频、预览）
  - `output`: 输出文件（scenes.json、DSL、成片）
- `trace_summary`: 执行摘要
  - `total_actions`: 总动作数
  - `successful`: 成功数
  - `failed`: 失败数
  - `total_time_ms`: 总耗时（毫秒）

---

### 2. GET /api/jobs/{job_id}/artifacts

**功能**: 获取任务的所有产物文件列表

**请求**:
```bash
curl http://localhost:8000/api/jobs/job_20250205_143022/artifacts
```

**响应**:
```json
{
  "input": [...],
  "temp": [...],
  "output": [...]
}
```

---

### 3. GET /api/jobs/{job_id}/trace

**功能**: 获取任务的完整执行 trace

**请求**:
```bash
curl http://localhost:8000/api/jobs/job_20250205_143022/trace
```

**响应**:
```json
{
  "total_actions": 10,
  "successful": 10,
  "failed": 0,
  "total_time_ms": 5432,
  "actions": [
    {
      "action": "create_timeline",
      "detail": "Created timeline: AutoCut_20250205_143022",
      "ok": true,
      "took_ms": 234
    },
    {
      "action": "append_scene",
      "detail": "Appended scene S0001 [10-90]",
      "ok": true,
      "took_ms": 456
    },
    {
      "action": "render_subtitles",
      "detail": "Rendered 42 subtitle segments",
      "ok": true,
      "took_ms": 1234
    },
    {
      "action": "export_mp4",
      "detail": "Exported to final.mp4",
      "ok": true,
      "took_ms": 3456
    }
  ]
}
```

---

### 4. GET /api/jobs/{job_id}/preview

**功能**: 获取低码率预览视频（480p/720p）

**请求**:
```bash
# 480p 预览（默认）
curl http://localhost:8000/api/jobs/job_20250205_143022/preview \
  -o preview_480p.mp4

# 720p 预览
curl http://localhost:8000/api/jobs/job_20250205_143022/preview?quality=720p \
  -o preview_720p.mp4
```

**参数**:
- `quality`: 预览质量（480p/720p），默认 480p

**响应**: 视频文件流（MP4）

**特性**:
- ✅ 自动生成低码率预览
- ✅ 缓存预览文件（第二次请求直接返回）
- ✅ 优化流式播放（faststart）
- ✅ 文件大小显著减小（约为原视频的 10-20%）

**预览参数**:

| 质量 | 分辨率 | 视频码率 | 音频码率 | 文件大小（5分钟） |
|------|--------|----------|----------|-------------------|
| 480p | 854x480 | 500 kbps | 128 kbps | ~25 MB |
| 720p | 1280x720 | 1000 kbps | 128 kbps | ~45 MB |

---

### 5. GET /api/jobs/{job_id}/download/{category}/{filename}

**功能**: 下载任务的产物文件

**请求**:
```bash
# 下载 scenes.json
curl http://localhost:8000/api/jobs/job_20250205_143022/download/output/scenes.json \
  -o scenes.json

# 下载 editing_dsl.json
curl http://localhost:8000/api/jobs/job_20250205_143022/download/output/editing_dsl.json \
  -o editing_dsl.json

# 下载最终视频
curl http://localhost:8000/api/jobs/job_20250205_143022/download/output/final.mp4 \
  -o final.mp4
```

**参数**:
- `category`: 文件类别（input/temp/output）
- `filename`: 文件名

**响应**: 文件流

---

### 6. GET /api/jobs/

**功能**: 列出所有任务

**请求**:
```bash
curl http://localhost:8000/api/jobs/?limit=50
```

**参数**:
- `limit`: 返回数量限制（默认 50）

**响应**:
```json
{
  "total": 3,
  "jobs": [
    {
      "job_id": "job_20250205_143022",
      "status": "completed",
      "progress": 100,
      "created_at": "2025-02-05T14:30:22",
      "updated_at": "2025-02-05T14:38:15"
    },
    {
      "job_id": "job_20250205_120000",
      "status": "processing",
      "progress": 65,
      "created_at": "2025-02-05T12:00:00",
      "updated_at": "2025-02-05T12:05:30"
    },
    {
      "job_id": "job_20250205_100000",
      "status": "failed",
      "progress": 45,
      "created_at": "2025-02-05T10:00:00",
      "updated_at": "2025-02-05T10:03:15"
    }
  ]
}
```

---

### 7. DELETE /api/jobs/{job_id}

**功能**: 删除任务及其所有文件

**请求**:
```bash
curl -X DELETE http://localhost:8000/api/jobs/job_20250205_143022
```

**响应**:
```json
{
  "job_id": "job_20250205_143022",
  "message": "Job 已删除"
}
```

---

## 🔄 完整工作流

### 1. 创建任务（Ingest）

```bash
curl -X POST http://localhost:8000/api/ingest/ \
  -F "video=@input.mp4" \
  -F "extract_audio=true"
```

**返回**: `job_id`

---

### 2. 查询任务状态

```bash
curl http://localhost:8000/api/jobs/{job_id}
```

**轮询直到**: `status == "completed"`

---

### 3. 获取预览视频

```bash
curl http://localhost:8000/api/jobs/{job_id}/preview \
  -o preview.mp4
```

**用途**: 快速预览成片效果

---

### 4. 查看执行详情

```bash
curl http://localhost:8000/api/jobs/{job_id}/trace
```

**用途**: 调试、性能分析

---

### 5. 下载最终成片

```bash
curl http://localhost:8000/api/jobs/{job_id}/download/output/final.mp4 \
  -o final.mp4
```

---

## 📊 任务状态流转

```
created
  ↓
processing (0-100%)
  ↓
completed / failed
```

**状态说明**:
- `created`: 任务已创建，等待处理
- `processing`: 正在处理，progress 表示进度
- `completed`: 处理完成
- `failed`: 处理失败，error 字段包含错误信息

---

## 🎬 预览视频生成

### 自动生成流程

1. **首次请求**: 
   - 检查原始视频
   - 使用 ffmpeg 生成低码率预览
   - 缓存到 `temp/preview_{quality}.mp4`
   - 返回预览文件

2. **后续请求**:
   - 直接返回缓存的预览文件
   - 响应速度快

### ffmpeg 参数

**480p 预览**:
```bash
ffmpeg -i input.mp4 \
  -vf scale=-2:480 \
  -b:v 500k \
  -c:v libx264 \
  -preset fast \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  preview_480p.mp4
```

**720p 预览**:
```bash
ffmpeg -i input.mp4 \
  -vf scale=-2:720 \
  -b:v 1000k \
  -c:v libx264 \
  -preset fast \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  preview_720p.mp4
```

**参数说明**:
- `scale=-2:480`: 高度 480px，宽度自动计算（保持比例）
- `b:v 500k`: 视频码率 500 kbps
- `preset fast`: 快速编码
- `movflags +faststart`: 优化流式播放（元数据前置）

---

## 🧪 测试

### 运行测试脚本

```bash
cd autocut-director
python test_jobs_api.py
```

### 测试内容

1. ✅ 列出所有 jobs
2. ✅ 获取 job 状态
3. ✅ 获取 artifacts 列表
4. ✅ 获取 trace 详情
5. ✅ 获取预览视频
6. ✅ 下载产物文件

---

## 💡 最佳实践

### 1. 轮询任务状态

```python
import time
import requests

def wait_for_job(job_id, timeout=300):
    """等待任务完成"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        response = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
        data = response.json()
        
        status = data['status']
        progress = data['progress']
        
        print(f"状态: {status}, 进度: {progress}%")
        
        if status == "completed":
            return True
        elif status == "failed":
            print(f"错误: {data['error']}")
            return False
        
        time.sleep(2)
    
    print("超时")
    return False
```

### 2. 下载所有产物

```python
def download_all_artifacts(job_id, output_dir):
    """下载所有产物文件"""
    import os
    
    # 获取 artifacts 列表
    response = requests.get(f"http://localhost:8000/api/jobs/{job_id}/artifacts")
    artifacts = response.json()
    
    for category, files in artifacts.items():
        category_dir = os.path.join(output_dir, category)
        os.makedirs(category_dir, exist_ok=True)
        
        for file in files:
            filename = file['name']
            url = f"http://localhost:8000/api/jobs/{job_id}/download/{category}/{filename}"
            
            response = requests.get(url, stream=True)
            output_path = os.path.join(category_dir, filename)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"✅ 已下载: {output_path}")
```

### 3. 预览优先

```python
def preview_before_download(job_id):
    """先预览，确认无误后再下载完整视频"""
    # 1. 获取 480p 预览
    response = requests.get(
        f"http://localhost:8000/api/jobs/{job_id}/preview",
        params={"quality": "480p"},
        stream=True
    )
    
    with open("preview.mp4", 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    
    print("✅ 预览已下载: preview.mp4")
    print("   请查看预览，确认无误后继续")
    
    # 2. 用户确认
    confirm = input("是否下载完整视频？(y/n): ")
    
    if confirm.lower() == 'y':
        # 3. 下载完整视频
        response = requests.get(
            f"http://localhost:8000/api/jobs/{job_id}/download/output/final.mp4",
            stream=True
        )
        
        with open("final.mp4", 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print("✅ 完整视频已下载: final.mp4")
```

---

## 📚 相关文档

- **[INGEST_GUIDE.md](INGEST_GUIDE.md)** - Ingest 层使用指南
- **[API_USAGE.md](API_USAGE.md)** - API 完整使用指南
- **[PIPELINE_GUIDE.md](PIPELINE_GUIDE.md)** - 流水线使用指南

---

## 🎉 总结

Jobs API 提供了完整的任务管理功能：

### 核心功能
- ✅ 任务状态查询（实时进度）
- ✅ 产物文件管理（分类清晰）
- ✅ 执行 trace 查看（调试利器）
- ✅ 低码率预览（快速预览）
- ✅ 文件下载（灵活获取）

### 使用场景
- 🎬 **Web 界面** - 实时显示任务进度
- 📱 **移动端** - 预览视频后再下载
- 🔧 **调试分析** - 查看 trace 定位问题
- 📊 **批量处理** - 管理多个任务

**立即开始**: `python run_server.py` → 访问 `http://localhost:8000/docs`

---

**版本**: v1.2.0  
**更新日期**: 2025-02-05  
**状态**: ✅ 生产就绪
