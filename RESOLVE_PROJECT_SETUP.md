# DaVinci Resolve 项目自动创建指南

## 问题：项目管理器闪烁但没有创建项目

### 原因分析

当你看到 DaVinci Resolve 的项目管理器在闪烁，但没有看到新创建的项目时，可能是以下原因：

1. **没有打开的项目** - 系统尝试连接但找不到活动项目
2. **自动创建失败** - 权限或配置问题导致无法创建项目
3. **项目在其他数据库** - 项目可能创建在了不同的数据库中

## 解决方案

### 方案 1：手动创建项目（推荐）

**最简单可靠的方法**：

1. **启动 DaVinci Resolve**
2. **在项目管理器中**：
   - 点击 "新建项目"
   - 输入项目名称（例如：`AutoCut_Project`）
   - 点击 "创建"
3. **打开项目** - 双击项目进入编辑界面
4. **运行 AutoCut Director** - 现在系统会自动连接到这个项目

### 方案 2：使用自动创建功能

**系统会自动尝试**：

1. **检查是否有打开的项目**
2. **如果没有，自动创建** - 项目名称：`AutoCut_YYYYMMDD_HHMMSS`
3. **如果创建失败，加载现有项目** - 加载数据库中的第一个项目

**要启用自动创建**，确保：

```python
# 系统会自动执行以下逻辑
from app.tools.resolve_importer import get_importer

importer = get_importer()
importer.connect()  # 会自动创建项目
```

### 方案 3：检查和修复

运行测试脚本检查连接：

```bash
cd autocut-director
python test_resolve_project_creation.py
```

**测试内容**：
1. ✅ 连接到 DaVinci Resolve
2. ✅ 检查/创建项目
3. ✅ 导入测试素材
4. ✅ 创建 Bin（文件夹）

## 详细步骤

### 步骤 1：确保 Resolve 正确启动

1. **启动 DaVinci Resolve**
2. **等待完全加载** - 看到项目管理器界面
3. **不要关闭项目管理器** - 保持打开状态

### 步骤 2：检查外部脚本设置

1. 在 Resolve 中，打开 **DaVinci Resolve -> 偏好设置**
2. 进入 **系统 -> 常规**
3. 找到 **外部脚本使用** 部分
4. 确保以下选项已启用：
   - ✅ **网络**
   - ✅ **本地**

### 步骤 3：设置环境变量

运行环境变量设置脚本：

```powershell
# PowerShell
cd autocut-director
.\scripts\set_resolve_env.ps1
```

**或手动设置**：

```powershell
$env:RESOLVE_SCRIPT_API = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting"
$env:RESOLVE_SCRIPT_LIB = "C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
$env:PYTHONPATH = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
```

### 步骤 4：创建项目

**选项 A：手动创建（推荐）**

1. 在项目管理器中点击 **"新建项目"**
2. 输入名称：`AutoCut_Project`
3. 点击 **"创建"**
4. **双击项目打开**

**选项 B：自动创建**

运行测试脚本：

```bash
python test_resolve_project_creation.py
```

系统会自动：
- 连接到 Resolve
- 检查是否有项目
- 如果没有，创建新项目
- 显示项目信息

### 步骤 5：验证连接

运行快速测试：

```python
from app.tools.resolve_importer import get_importer

importer = get_importer()
status = importer.check_resolve_status()

print(f"连接状态: {status['connected']}")
print(f"项目名称: {status['project_name']}")
print(f"素材数量: {status['media_pool_items']}")
```

**预期输出**：

```
连接状态: True
项目名称: AutoCut_Project
素材数量: 0
```

## 常见问题

### Q1: 项目管理器一直闪烁

**原因**：系统在尝试连接，但没有活动项目

**解决**：
1. 手动创建一个项目
2. 打开项目（双击）
3. 重新运行 AutoCut Director

### Q2: 提示 "Cannot connect to DaVinci Resolve"

**原因**：Resolve 未启动或环境变量未设置

**解决**：
1. 确保 Resolve 已启动
2. 运行 `set_resolve_env.ps1`
3. 重启终端/命令行

### Q3: 提示 "No current project opened"

**原因**：没有打开的项目

**解决**：
1. 在 Resolve 中创建项目
2. **双击项目打开**（重要！）
3. 确保看到编辑界面，不是项目管理器

### Q4: 自动创建的项目在哪里？

**位置**：
- 默认数据库：`C:\Users\<用户名>\AppData\Roaming\Blackmagic Design\DaVinci Resolve\Resolve Disk Database`
- 项目名称：`AutoCut_YYYYMMDD_HHMMSS`

**查看**：
1. 在项目管理器中
2. 查看当前数据库
3. 找到以 `AutoCut_` 开头的项目

### Q5: 如何切换数据库？

1. 在项目管理器右下角
2. 点击数据库名称
3. 选择其他数据库
4. 或创建新数据库

## 最佳实践

### 1. 使用专用项目

为 AutoCut Director 创建专用项目：

```
项目名称: AutoCut_Main
用途: 所有自动剪辑任务
```

### 2. 定期清理

定期清理旧项目：
- 删除测试项目
- 归档完成的项目
- 保持数据库整洁

### 3. 备份项目

重要项目要备份：
1. 右键项目 -> 导出项目
2. 保存为 `.drp` 文件
3. 定期备份到云端

### 4. 使用 Bin 组织

在 Media Pool 中使用 Bin：
- `AutoCut_Input` - 原始素材
- `AutoCut_Output` - 剪辑结果
- `AutoCut_Temp` - 临时文件

## 自动化脚本

### 创建项目并导入素材

```python
from app.tools.resolve_importer import get_importer

# 连接并创建项目
importer = get_importer()
importer.connect()

# 导入素材
result = importer.import_media([
    "C:/Videos/video1.mp4",
    "C:/Videos/video2.mp4"
])

print(f"导入结果: {result['message']}")
```

### 从清单批量导入

```python
from app.tools.resolve_importer import get_importer

importer = get_importer()
result = importer.import_from_manifest("assets_manifest.json")

if result["success"]:
    print(f"成功导入 {len(result['imported'])} 个素材")
    
    # 显示 asset_id 映射
    for asset_id, media_item in result["asset_mapping"].items():
        print(f"{asset_id} -> {media_item}")
```

## 故障排除流程

```
1. Resolve 是否启动？
   ├─ 否 → 启动 Resolve
   └─ 是 → 继续

2. 是否有打开的项目？
   ├─ 否 → 创建/打开项目
   └─ 是 → 继续

3. 环境变量是否设置？
   ├─ 否 → 运行 set_resolve_env.ps1
   └─ 是 → 继续

4. 外部脚本是否启用？
   ├─ 否 → 在设置中启用
   └─ 是 → 继续

5. 运行测试脚本
   ├─ 失败 → 查看错误信息
   └─ 成功 → 可以使用了！
```

## 总结

**推荐工作流**：

1. ✅ **启动 DaVinci Resolve**
2. ✅ **手动创建项目**（最可靠）
3. ✅ **打开项目**（双击进入编辑界面）
4. ✅ **运行 AutoCut Director**
5. ✅ **系统自动导入素材**

**关键点**：
- 必须有**打开的项目**（不是项目管理器）
- 必须在**编辑界面**（不是项目管理器）
- 环境变量必须正确设置

---

**版本**: v1.7.1  
**日期**: 2026-02-05  
**状态**: ✅ 已更新自动创建功能
