# AutoCut Director 快速开始

## 5 分钟上手

### 1. 安装（1 分钟）

```bash
# 创建虚拟环境
python -m venv .venv
.\.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置 Resolve
.\scripts\set_resolve_env.ps1
```

### 2. 测试核心功能（2 分钟）

```bash
# 测试 EDL 解析器
python test_edl_parser.py

# 测试硬规则验证器
python test_dsl_validator.py

# 端到端测试
python test_e2e.py
```

### 3. 启动服务（1 分钟）

```bash
python -m app.main
```

访问 http://localhost:8000

### 4. 使用 API（1 分钟）

#### 分析 EDL

```bash
curl -X POST http://localhost:8000/api/analyze \
  -F "edl_file=@examples/test.edl"
```

返回：
```json
{
  "job_id": "abc123",
  "artifacts": {
    "scenes": "scenes.json"
  }
}
```

#### 下载 scenes.json

```bash
curl http://localhost:8000/api/job/abc123/artifact/scenes.json
```

#### 执行剪辑

```bash
curl -X POST http://localhost:8000/api/execute \
  -F "dsl_file=@examples/editing_dsl.v1.json" \
  -F "scenes_file=@examples/scenes.v1.json"
```

## 工作流程

```
1. 用户上传 EDL
   ↓
2. 生成 scenes.json
   ↓
3. LLM 读取 scenes.json，生成 editing_dsl.json
   ↓
4. 上传 DSL + scenes 到 /execute
   ↓
5. 硬规则验证（防 AI 幻觉）
   ↓
6. 执行 Resolve 操作
   ↓
7. 导出成品
```

## 三个核心文件

### scenes.json
```json
{
  "meta": { "schema": "scenes.v1", "fps": 30 },
  "media": { "primary_clip_path": "D:/Footage/input.mp4" },
  "scenes": [
    { "scene_id": "S0001", "start_frame": 0, "end_frame": 120 }
  ]
}
```

### editing_dsl.json
```json
{
  "meta": { "target": "douyin", "aspect": "9:16" },
  "editing_plan": {
    "timeline": [
      { "order": 1, "scene_id": "S0001", "trim_frames": [10, 90] }
    ]
  }
}
```

### transcript.json
```json
{
  "meta": { "language": "zh" },
  "segments": [
    { "start": 0.0, "end": 2.8, "text": "开场白" }
  ]
}
```

## 硬规则（防 AI 幻觉）

Executor 执行前必须验证：

1. ✅ `scene_id` 存在于 scenes.json
2. ✅ `trim_frames` 在场景帧范围内
3. ✅ `trim_frames` 顺序正确

任何失败 → 拒绝执行 → 返回详细错误

## 下一步

- 阅读 [PROTOCOL.md](PROTOCOL.md) 了解协议详情
- 阅读 [INSTALL.md](INSTALL.md) 了解安装细节
- 查看 [examples/](examples/) 目录的示例文件
- 启动 DaVinci Resolve 测试完整流程

## 故障排除

### Q: 测试失败

**A:** 确保在 `autocut-director` 目录下运行：
```bash
cd autocut-director
python test_e2e.py
```

### Q: Resolve 连接失败

**A:** 
1. 启动 DaVinci Resolve
2. 打开一个项目
3. 运行 `python test_resolve_connection.py`

### Q: 找不到模块

**A:** 确保虚拟环境已激活：
```bash
.\.venv\Scripts\activate
pip list  # 检查已安装的包
```
