# DaVinci Resolve 环境配置指南

## 脚本 API 位置

DaVinci Resolve 的 Python 脚本 API 通常位于：

**Windows:**
```
C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules\
```

**macOS:**
```
/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules/
```

**Linux:**
```
/opt/resolve/Developer/Scripting/Modules/
```

## 快速配置（Windows）

### 方法 1: 简化版（推荐）

如果你知道 Resolve 的安装路径：

```powershell
.\scripts\set_resolve_env_simple.ps1
```

或直接在终端运行：

```powershell
$env:RESOLVE_SCRIPT_DIR = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
$env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"
```

### 方法 2: 自动检测版

自动搜索 Resolve 安装路径：

```powershell
.\scripts\set_resolve_env_auto.ps1
```

### 方法 3: 完整版

带验证和错误处理：

```powershell
.\scripts\set_resolve_env.ps1
```

## 手动配置

### 1. 找到脚本 API 路径

运行以下命令查找：

```powershell
Get-ChildItem -Path "C:\ProgramData\Blackmagic Design" -Recurse -Filter "DaVinciResolveScript.py" | Select-Object FullName
```

### 2. 设置 PYTHONPATH

**临时设置（当前会话）：**

```powershell
$env:PYTHONPATH = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules;$env:PYTHONPATH"
```

**永久设置（用户环境变量）：**

```powershell
[System.Environment]::SetEnvironmentVariable(
    "PYTHONPATH",
    "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules",
    "User"
)
```

### 3. 验证配置

```python
python -c "import DaVinciResolveScript; print('✓ 配置成功')"
```

## 常见问题

### Q: 找不到 DaVinciResolveScript.py

**A:** 确保：
1. 已安装 **DaVinci Resolve Studio** 版本（免费版不支持脚本 API）
2. 版本 >= 16.0
3. 检查 `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer` 目录是否存在

### Q: ImportError: No module named 'DaVinciResolveScript'

**A:** 
1. 检查 PYTHONPATH 是否正确设置
2. 重启终端/IDE
3. 确保 Resolve 已启动

### Q: 连接失败 "无法连接到 DaVinci Resolve"

**A:**
1. 确保 DaVinci Resolve 正在运行
2. 在 Resolve 中打开一个项目
3. 检查 Resolve 设置：Preferences > System > General > "External scripting using" 已启用

## 测试连接

创建测试脚本 `test_resolve.py`：

```python
import DaVinciResolveScript as dvr_script

resolve = dvr_script.scriptapp("Resolve")
if resolve:
    print("✓ 成功连接到 DaVinci Resolve")
    
    pm = resolve.GetProjectManager()
    project = pm.GetCurrentProject()
    
    if project:
        print(f"✓ 当前项目: {project.GetName()}")
    else:
        print("⚠ 没有打开的项目")
else:
    print("✗ 连接失败")
```

运行：
```bash
python test_resolve.py
```
