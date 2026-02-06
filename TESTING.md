# AutoCut Director 测试指南

## 测试套件概览

### 1. 单元测试（无需 Resolve）

#### EDL 解析器测试
```bash
python test_edl_parser.py
```

**测试内容:**
- ✅ 时间码正则匹配
- ✅ TC -> 帧数转换
- ✅ scenes.v1.json 生成

**预期输出:**
```
✓ 解析成功，生成 3 个场景
  S0001: 00:00:00:00 -> 00:00:04:00 (120 帧)
  S0002: 00:00:04:00 -> 00:00:08:00 (120 帧)
  S0003: 00:00:08:00 -> 00:00:12:00 (120 帧)
```

#### DSL 验证器测试
```bash
python test_dsl_validator.py
```

**测试内容:**
- ✅ 正常 DSL 验证通过
- ✅ scene_id 不存在检测（AI 幻觉）
- ✅ trim_frames 超出范围检测
- ✅ trim_frames 顺序错误检测

**预期输出:**
```
✓ 正常 DSL 通过
✗ scene_id 不存在（AI 幻觉）- 成功拦截
✗ trim_frames 超出范围 - 成功拦截
✗ trim_frames 顺序错误 - 成功拦截
```

#### 端到端测试
```bash
python test_e2e.py
```

**测试内容:**
- ✅ EDL -> scenes.json
- ✅ DSL 创建（模拟 AI）
- ✅ 硬规则验证
- ✅ AI 幻觉检测

**预期输出:**
```
[Step 1] 解析 EDL -> scenes.json
✓ 解析成功，生成 3 个场景

[Step 2] 创建 editing_dsl.json（模拟 AI 生成）
✓ 已保存: test_output_dsl.json

[Step 3] 硬规则验证（防 AI 幻觉）
✓ 验证通过！DSL 可以安全执行

[Step 4] 测试 AI 幻觉检测
✓ 成功检测到 AI 幻觉！
```

---

### 2. Resolve 集成测试（需要 Resolve 运行）

#### 最小连接测试
```bash
python test_resolve_minimal.py
```

**前置条件:**
1. ✅ DaVinci Resolve 正在运行
2. ✅ 已打开一个项目
3. ✅ RESOLVE_SCRIPT_DIR 已设置

**测试内容:**
- ✅ 连接到 Resolve
- ✅ 获取项目信息
- ✅ 获取时间线信息
- ✅ 获取媒体池信息

**预期输出:**
```
[1] 连接到 Resolve...
✓ 连接成功

[2] 获取项目信息...
✓ 当前项目: My Project

[3] 获取时间线信息...
✓ 时间线数量: 2
✓ 当前时间线: Timeline 1

[4] 时间线属性:
  - 帧率: 30.0 fps
  - 分辨率: 1920x1080

[5] 获取媒体池信息...
✓ 媒体池根目录: Master
```

#### Adapter 功能测试
```bash
python test_resolve_adapter.py
```

**测试内容:**
- ✅ 连接到 Resolve
- ✅ 创建时间线
- ⏳ 导入媒体（需要实际文件）
- ⏳ 添加音频（需要实际文件）
- ⏳ 导入字幕（需要实际文件）
- ⏳ 导出设置（跳过实际渲染）

**预期输出:**
```
[1] 连接到 Resolve...
✓ 连接成功
  - 项目: My Project

[2] 创建测试时间线...
✓ 时间线创建成功: AutoCut_Test
  - 帧率: 30.0 fps
  - 分辨率: 1920x1080

[3-6] 其他测试...
⚠ 跳过（需要实际媒体文件）
```

#### 完整连接测试
```bash
python test_resolve_connection.py
```

**测试内容:**
- ✅ 检查 PYTHONPATH
- ✅ 导入 DaVinciResolveScript
- ✅ 连接到 Resolve
- ✅ 获取项目和时间线信息

---

## 测试流程

### 快速测试（5 分钟）

```bash
# 1. 单元测试（无需 Resolve）
python test_edl_parser.py
python test_dsl_validator.py
python test_e2e.py

# 2. 环境配置
.\scripts\set_resolve_env.ps1

# 3. Resolve 连接测试（需要启动 Resolve）
python test_resolve_minimal.py
```

### 完整测试（15 分钟）

```bash
# 1. 所有单元测试
python test_edl_parser.py
python test_dsl_validator.py
python test_e2e.py

# 2. 环境配置
.\scripts\set_resolve_env.ps1

# 3. 启动 DaVinci Resolve
# - 打开一个项目
# - 创建一个时间线（可选）

# 4. Resolve 集成测试
python test_resolve_minimal.py
python test_resolve_connection.py
python test_resolve_adapter.py

# 5. API 测试（可选）
python -m app.main  # 启动服务
# 使用 curl 或 Postman 测试 API 端点
```

---

## 故障排除

### 单元测试失败

**Q: ModuleNotFoundError: No module named 'app'**

**A:** 确保在 `autocut-director` 目录下运行：
```bash
cd autocut-director
python test_e2e.py
```

**Q: FileNotFoundError: examples/test.edl**

**A:** 确保示例文件存在：
```bash
ls examples/test.edl
```

### Resolve 连接失败

**Q: RuntimeError: Cannot connect to DaVinci Resolve**

**A:** 检查清单：
1. ✅ DaVinci Resolve 正在运行
2. ✅ 已打开一个项目
3. ✅ RESOLVE_SCRIPT_DIR 已设置
4. ✅ Resolve 版本 >= 16.0
5. ✅ 使用 Studio 版本（免费版不支持脚本 API）

**Q: ImportError: DLL load failed while importing fusionscript**

**A:** 这是正常的，只有在 Resolve 运行时才能导入。确保：
1. Resolve 正在运行
2. 已打开项目
3. 重新运行测试

**Q: RuntimeError: No current project opened in Resolve**

**A:** 在 Resolve 中打开或创建一个项目

### 环境配置问题

**Q: PYTHONPATH 未设置**

**A:** 运行配置脚本：
```powershell
.\scripts\set_resolve_env.ps1
```

或手动设置：
```powershell
$env:RESOLVE_SCRIPT_DIR = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
$env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"
```

---

## 测试覆盖率

### 已测试 ✅
- EDL 解析器（100%）
- DSL 验证器（100%）
- 端到端流程（100%）
- Resolve 连接（基础）
- 时间线创建（基础）

### 待测试 ⏳
- 媒体导入（需要实际文件）
- 音频添加（需要实际文件）
- 字幕导入（需要实际文件）
- 导出渲染（需要实际文件）
- API 端点（需要启动服务）

---

## 持续集成

### 本地 CI 脚本

创建 `run_tests.ps1`:
```powershell
# 运行所有单元测试
Write-Host "Running unit tests..." -ForegroundColor Cyan
python test_edl_parser.py
python test_dsl_validator.py
python test_e2e.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "All tests passed!" -ForegroundColor Green
} else {
    Write-Host "Tests failed!" -ForegroundColor Red
    exit 1
}
```

运行：
```bash
.\run_tests.ps1
```

---

## 下一步

1. ✅ 完成所有单元测试
2. ⏳ 准备测试媒体文件
3. ⏳ 完整 Resolve 集成测试
4. ⏳ API 端点测试
5. ⏳ 性能测试
6. ⏳ 压力测试
