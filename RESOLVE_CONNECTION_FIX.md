# 达芬奇连接问题诊断和解决

## 问题诊断

### 错误信息
```
DLL load failed while importing fusionscript: 找不到指定的模块。
```

### 根本原因

达芬奇的 Python 脚本 API 依赖于达芬奇进程中的 DLL 文件。这些 DLL 只有在达芬奇运行时才能被加载。

---

## 解决方案

### 步骤 1: 启动达芬奇

1. 打开 DaVinci Resolve
2. 等待完全启动

### 步骤 2: 创建或打开项目

**重要**: 必须有一个打开的项目，脚本 API 才能正常工作

1. 在达芬奇中创建新项目，或
2. 打开现有项目

### 步骤 3: 启用外部脚本（如果需要）

某些达芬奇版本需要启用外部脚本访问：

1. 打开 DaVinci Resolve
2. 进入 **Preferences** (偏好设置)
3. 找到 **System** → **General**
4. 确保 **External scripting using** 选项已启用

### 步骤 4: 测试连接

运行测试脚本：

```powershell
python test_resolve_quick.py
```

预期输出：
```
============================================================
达芬奇连接快速测试
============================================================

[1] 检查模块路径
  路径: C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules
  存在: True

[2] 尝试导入 DaVinciResolveScript
  ✓ 模块导入成功

[3] 尝试连接达芬奇
  ✓ 连接成功
  版本: 18.x.x
  ✓ 项目管理器可用
  ✓ 当前项目: Untitled Project

============================================================
✓ 测试完成
============================================================
```

---

## 常见问题

### Q1: 达芬奇已启动，但仍然连接失败

**检查清单**:
1. ✅ 达芬奇是否完全启动（不是启动画面）
2. ✅ 是否有打开的项目
3. ✅ 达芬奇版本是否支持脚本 API（需要 Studio 版本或免费版 16+）
4. ✅ 是否启用了外部脚本

### Q2: 提示 "没有打开的项目"

**解决方案**:
1. 在达芬奇中点击 **File** → **New Project**
2. 输入项目名称（如 "AutoCut Test"）
3. 点击 **Create**
4. 重新运行测试脚本

### Q3: 提示 "找不到指定的模块"

**可能原因**:
1. 达芬奇未启动
2. 达芬奇版本太旧（需要 16+ 版本）
3. Python 版本不兼容（推荐 Python 3.6-3.11）

**解决方案**:
1. 确保达芬奇正在运行
2. 更新到最新版本的达芬奇
3. 检查 Python 版本：`python --version`

### Q4: 提示 "连接失败"

**可能原因**:
1. 达芬奇的脚本服务未启动
2. 防火墙阻止了连接
3. 达芬奇版本不支持脚本 API

**解决方案**:
1. 重启达芬奇
2. 检查防火墙设置
3. 确认达芬奇版本（需要 Studio 版本或免费版 16+）

---

## 自动化解决方案

### 创建启动脚本

创建一个脚本，在启动 AutoCut Director 之前检查达芬奇状态：

```powershell
# start_with_resolve_check.ps1

Write-Host "检查达芬奇状态..." -ForegroundColor Cyan

# 检查达芬奇是否运行
$resolve = Get-Process -Name "Resolve" -ErrorAction SilentlyContinue

if (-not $resolve) {
    Write-Host "⚠️  达芬奇未运行" -ForegroundColor Yellow
    Write-Host "请先启动 DaVinci Resolve 并打开一个项目" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "按任意键继续..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# 启动 AutoCut Director
Write-Host "启动 AutoCut Director..." -ForegroundColor Green
python run_server.py
```

使用方法：
```powershell
.\start_with_resolve_check.ps1
```

---

## 工作流程

### 正确的启动顺序

1. **启动达芬奇**
   - 打开 DaVinci Resolve
   - 等待完全启动

2. **创建/打开项目**
   - 创建新项目或打开现有项目
   - 确保项目已加载

3. **启动 AutoCut Director**
   - 运行 `python run_server.py`
   - 或使用 Web UI

4. **开始处理**
   - 上传视频
   - 系统会自动连接到达芬奇

### 推荐工作流

```
1. 启动达芬奇 → 2. 打开项目 → 3. 启动 AutoCut → 4. 处理视频
```

---

## 测试命令

### 快速测试

```powershell
# 测试达芬奇连接
python test_resolve_quick.py

# 完整诊断
python diagnose_resolve.py

# 测试项目创建
python test_resolve_project_creation.py
```

---

## 技术细节

### 为什么需要达芬奇运行？

达芬奇的 Python API 使用了以下机制：

1. **进程间通信 (IPC)**: Python 脚本通过 IPC 与达芬奇进程通信
2. **DLL 依赖**: `fusionscript.pyd` 等 DLL 需要达芬奇的运行时环境
3. **COM/RPC**: 使用 COM 或 RPC 机制调用达芬奇的内部 API

因此，达芬奇必须运行才能加载这些 DLL 和建立连接。

### 环境变量

虽然环境变量不是必需的（可以在代码中动态设置），但设置后可以简化配置：

```powershell
# 设置环境变量（可选）
$env:RESOLVE_SCRIPT_DIR = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
$env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"
```

---

## 总结

✅ **必须条件**:
1. 达芬奇正在运行
2. 有打开的项目
3. 达芬奇版本支持脚本 API（16+ 或 Studio）

✅ **推荐配置**:
1. 使用最新版本的达芬奇
2. 启用外部脚本访问
3. 使用 Python 3.6-3.11

✅ **正确顺序**:
1. 启动达芬奇
2. 打开项目
3. 启动 AutoCut Director
4. 开始处理

---

## 下一步

1. **启动达芬奇**: 打开 DaVinci Resolve
2. **创建项目**: 创建一个测试项目
3. **运行测试**: `python test_resolve_quick.py`
4. **启动服务**: `python run_server.py`

如果仍有问题，请查看详细日志或联系技术支持。
