# 生产测试指南

## 🎯 测试目标

验证 AutoCut Director 在生产环境中的完整功能，确保从素材到成片的完整闭环可用。

---

## ✅ 前置条件检查

### 1. 环境准备

```bash
# 1. Python 环境
python --version  # 需要 Python 3.8+

# 2. 安装依赖
cd autocut-director
pip install -r requirements.txt

# 3. ffmpeg（用于音频提取和预览生成）
ffmpeg -version

# 4. DaVinci Resolve
# - 已安装 DaVinci Resolve Studio（或免费版）
# - Resolve 正在运行
# - 已打开一个项目
```

### 2. 配置文件

创建 `.env` 文件：

```bash
# autocut-director/.env

# LLM 配置（用于 AI 生成 DSL）
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=  # 可选

# Whisper 配置
WHISPER_MODEL=base
WHISPER_DEVICE=cpu

# Resolve 环境（Windows）
# 运行脚本自动设置: .\scripts\set_resolve_env.ps1
```

### 3. Resolve 环境配置

```powershell
# Windows PowerShell
cd autocut-director
.\scripts\set_resolve_env.ps1
```

验证：
```powershell
echo $env:RESOLVE_SCRIPT_API
echo $env:RESOLVE_SCRIPT_LIB
```

---

## 📋 测试流程

### 阶段 1: 基础功能测试（无 Resolve）

#### 1.1 铁律验证测试

```bash
cd autocut-director
python test_iron_rules.py
```

**预期结果**:
```
✅ 铁律 1 验证逻辑正确
✅ 铁律 2 验证逻辑正确
✅ fps 验证逻辑正确
✅ 转换逻辑正确
✅ 所有测试通过
```

#### 1.2 EDL 解析测试

```bash
python test_edl_parser.py
```

**预期结果**:
```
✅ EDL 解析成功
✅ scenes.json 生成正确
✅ 帧号和时间码转换正确
```

#### 1.3 DSL 验证测试

```bash
python test_dsl_validator.py
```

**预期结果**:
```
✅ scene_id 存在性检查通过
✅ trim_frames 范围检查通过
✅ 硬规则验证通过
```

#### 1.4 Ingest 测试

```bash
python test_ingest.py
```

**预期结果**:
```
✅ Job 目录创建
✅ 音频提取成功（需要 ffmpeg）
✅ 场景切点检测提示生成
```

---

### 阶段 2: Resolve 集成测试

#### 2.1 Resolve Smoke Test ⭐

```bash
python test_resolve_smoke.py
```

**测试内容**:
1. ✅ 连接 Resolve
2. ✅ 新建时间线
3. ✅ 插入素材
4. ⚠️ 导出 mp4（手动完成）

**预期结果**:
```
✅ 连接成功
✅ 时间线创建成功: SmokeTest_Timeline
✅ 素材插入成功
⚠️  导出 mp4（需手动完成）
```

**手动导出步骤**:
1. 在 Resolve 中切换到 **Deliver** 页面
2. 选择 **H.264** 预设
3. 设置输出路径: `test_output/smoke_test_output.mp4`
4. 点击 **Add to Render Queue**
5. 点击 **Start Render**
6. 等待渲染完成

#### 2.2 最小 DSL 测试 ⭐

```bash
python test_minimal_dsl.py
```

**测试内容**:
- 3 段视频片段
- 字幕（from_transcript）
- 背景音乐（可选）
- 不包含 fancy overlay

**预期结果**:
```
✅ DSL 验证通过
✅ 生成 5-6 个 Actions
✅ 所有 Actions 执行成功
```

---

### 阶段 3: 完整流水线测试

#### 3.1 准备测试素材

```
test_materials/
├── input.mp4          # 测试视频（5-10 分钟）
└── timeline.edl       # Resolve 导出的 EDL
```

**获取 EDL 步骤**:
1. 在 Resolve 中导入 `input.mp4`
2. 右键 → **Scene Cut Detection**
3. 检测完成后，拖到时间线
4. File → Export → Timeline → **EDL**
5. 选择 **CMX 3600** 格式
6. 保存为 `timeline.edl`

#### 3.2 运行完整流水线

**方式 1: 交互式（推荐）**

```bash
python quick_start.py
```

**流程**:
1. 输入视频路径: `test_materials/input.mp4`
2. 等待 Ingest 完成（音频提取）
3. 导出 EDL 到 job 目录
4. 选择剪辑风格（如：抖音爆款）
5. 等待 AI 生成 DSL
6. 等待 Resolve 执行
7. 查看成片

**方式 2: 命令行**

```bash
python run_pipeline.py \
  --edl test_materials/timeline.edl \
  --audio test_materials/input.mp4 \
  --clip test_materials/input.mp4 \
  --style "抖音爆款风格" \
  --output test_output/final.mp4
```

**方式 3: API 服务**

```bash
# 启动服务
python run_server.py

# 在另一个终端测试
python test_jobs_api.py
```

---

### 阶段 4: API 测试

#### 4.1 启动 API 服务

```bash
cd autocut-director
python run_server.py
```

访问: http://localhost:8000/docs

#### 4.2 测试 Ingest API

```bash
curl -X POST http://localhost:8000/api/ingest/ \
  -F "video=@test_materials/input.mp4" \
  -F "extract_audio=true"
```

**预期响应**:
```json
{
  "job_id": "job_20250205_143022",
  "job_path": "jobs/job_20250205_143022",
  "video_path": "...",
  "audio_path": "...",
  "message": "Ingest 完成，请在 Resolve 中完成场景切点检测并上传 EDL"
}
```

#### 4.3 测试 Jobs API

```bash
# 获取 job 状态
curl http://localhost:8000/api/jobs/{job_id}

# 获取预览视频
curl http://localhost:8000/api/jobs/{job_id}/preview \
  -o preview.mp4

# 获取 trace
curl http://localhost:8000/api/jobs/{job_id}/trace
```

---

## 🎯 生产测试清单

### 必须通过的测试 ✅

- [ ] **铁律验证** - test_iron_rules.py
- [ ] **EDL 解析** - test_edl_parser.py
- [ ] **DSL 验证** - test_dsl_validator.py
- [ ] **Resolve 连接** - test_resolve_smoke.py (步骤 1-2)
- [ ] **最小 DSL 执行** - test_minimal_dsl.py
- [ ] **完整流水线** - quick_start.py 或 run_pipeline.py

### 可选测试 ⚠️

- [ ] **Ingest 测试** - test_ingest.py（需要 ffmpeg）
- [ ] **LLM 生成** - test_llm_director.py（需要 API Key）
- [ ] **SRT 生成** - test_srt_generation.py
- [ ] **Jobs API** - test_jobs_api.py（需要运行服务）

---

## 🐛 常见问题排查

### 问题 1: 无法连接 Resolve

```
❌ Cannot connect to DaVinci Resolve
```

**解决**:
1. 确认 Resolve 正在运行
2. 确认已打开一个项目
3. 运行环境配置脚本:
   ```powershell
   .\scripts\set_resolve_env.ps1
   ```
4. 重启 PowerShell 终端

### 问题 2: ffmpeg 未安装

```
❌ ffmpeg 未安装
```

**解决**:
```bash
# Windows (Chocolatey)
choco install ffmpeg

# 或手动下载
# https://ffmpeg.org/download.html
```

### 问题 3: OpenAI API Key 未配置

```
❌ OPENAI_API_KEY not configured
```

**解决**:
在 `.env` 文件中配置:
```bash
OPENAI_API_KEY=sk-your-api-key-here
```

### 问题 4: 导入错误

```
❌ ModuleNotFoundError: No module named 'xxx'
```

**解决**:
```bash
pip install -r requirements.txt
```

### 问题 5: Resolve API 限制

```
⚠️  API 导出失败
```

**解决**:
使用手动导出步骤（见 Smoke Test）

---

## 📊 测试报告模板

### 测试环境

- **操作系统**: Windows 11
- **Python 版本**: 3.10.x
- **DaVinci Resolve 版本**: 18.x
- **ffmpeg 版本**: 6.x
- **测试日期**: 2025-02-05

### 测试结果

| 测试项 | 状态 | 备注 |
|--------|------|------|
| 铁律验证 | ✅ | 全部通过 |
| EDL 解析 | ✅ | 15 个场景 |
| DSL 验证 | ✅ | 无错误 |
| Resolve 连接 | ✅ | 连接成功 |
| 时间线创建 | ✅ | 30fps, 1920x1080 |
| 素材插入 | ✅ | 3 段片段 |
| 字幕渲染 | ✅ | 42 段字幕 |
| 导出成片 | ⚠️ | 手动完成 |
| 完整流水线 | ✅ | 8 分钟完成 |

### 性能数据

- **EDL 解析**: < 1s
- **音频提取**: 45s (5 分钟视频)
- **Whisper 转录**: 2m 15s (base 模型)
- **AI 生成 DSL**: 18s
- **Resolve 执行**: 3m 30s
- **总耗时**: 6m 48s

### 问题记录

1. ⚠️ Resolve API 导出功能有限，需要手动完成
2. ✅ 其他功能正常

### 结论

- ✅ **可以进行生产测试**
- ✅ 核心功能完整
- ⚠️ 导出环节需要手动操作（Resolve API 限制）

---

## 🚀 生产部署建议

### 1. 环境隔离

```bash
# 使用虚拟环境
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 配置管理

```bash
# 生产环境配置
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 3. 日志记录

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.INFO)
```

### 4. 监控和告警

- 监控 job 状态
- 监控 Resolve 连接
- 监控 API 响应时间
- 监控磁盘空间（job 目录）

### 5. 备份策略

- 定期备份 jobs 目录
- 保留重要的 DSL 和 trace
- 清理过期的临时文件

---

## 📚 相关文档

- **[QUICKSTART.md](QUICKSTART.md)** - 快速开始
- **[PIPELINE_GUIDE.md](PIPELINE_GUIDE.md)** - 流水线指南
- **[JOBS_API_GUIDE.md](JOBS_API_GUIDE.md)** - Jobs API 指南
- **[IRON_RULES.md](IRON_RULES.md)** - 两条铁律
- **[INGEST_GUIDE.md](INGEST_GUIDE.md)** - Ingest 指南

---

## 🎉 总结

### 可以进行生产测试 ✅

**理由**:
1. ✅ 完整的 Ingest 层（音频提取 + job 管理）
2. ✅ 稳定的 EDL 解析（CMX 3600）
3. ✅ 严格的 DSL 验证（两条铁律）
4. ✅ 完整的 Resolve 集成（连接 + 执行）
5. ✅ Trace + Preview 回传（调试利器）

**限制**:
- ⚠️ Resolve API 导出功能有限，需要手动完成最后一步
- ⚠️ 需要 DaVinci Resolve 环境（本地或远程）

**建议**:
1. 先运行 **Smoke Test** 验证 Resolve 连接
2. 再运行 **最小 DSL 测试** 验证执行流程
3. 最后运行 **完整流水线** 进行端到端测试

**立即开始**:
```bash
cd autocut-director
python test_resolve_smoke.py
```

---

**版本**: v1.2.0  
**状态**: ✅ 生产就绪  
**测试日期**: 2025-02-05
