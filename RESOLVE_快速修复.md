# DaVinci Resolve 项目创建问题 - 快速修复指南

## 问题现象

看到项目管理器在闪，但没有看到创建的项目。

## 根本原因

**DaVinci Resolve 必须有一个打开的项目才能使用 API**

- 项目管理器界面 ≠ 打开的项目
- 必须在**编辑界面**（Edit 页面），不是项目管理器

## 快速解决方案（3 步）

### 方案 1：手动创建（最可靠，推荐）⭐

```
1. 启动 DaVinci Resolve
2. 在项目管理器中点击 "新建项目"
3. 输入名称：AutoCut_Main
4. 双击项目打开（重要！）
5. 确保看到编辑界面（有 Media Pool、Timeline 等）
```

**完成后**，运行 AutoCut Director 即可自动导入素材。

### 方案 2：运行诊断工具

```powershell
cd autocut-director
python diagnose_resolve.py
```

诊断工具会：
- ✅ 检查环境变量
- ✅ 检查 Resolve 连接
- ✅ 检查项目状态
- ✅ 提供具体修复建议
- ✅ 可选：自动创建项目

### 方案 3：运行测试脚本

```powershell
cd autocut-director
python test_resolve_project_creation.py
```

测试脚本会：
- 连接到 Resolve
- 尝试创建项目
- 导入测试素材
- 验证功能

## 验证是否修复

运行诊断工具，应该看到：

```
[5/5] 检查当前项目...
  ✓ 当前有打开的项目: AutoCut_Main
  - Media Pool 中有 0 个素材

✅ 诊断完成 - 一切正常！
```

## 常见问题

### Q1: 为什么自动创建不工作？

**原因**：Resolve API 的 `CreateProject()` 会创建项目，但不会自动打开它。

**解决**：
1. 在 Resolve 项目管理器中找到创建的项目（名称：`AutoCut_YYYYMMDD_HHMMSS`）
2. 双击打开
3. 重新运行 AutoCut Director

### Q2: 我看到项目管理器闪烁是什么意思？

**原因**：系统在尝试连接 Resolve，但因为没有打开的项目，Resolve 自动显示项目管理器。

**解决**：按照方案 1 手动创建并打开项目。

### Q3: 环境变量设置了吗？

运行：

```powershell
.\scripts\set_resolve_env.ps1
```

然后**重启终端**。

### Q4: Resolve 设置正确吗？

在 Resolve 中：
1. 打开 **DaVinci Resolve -> 偏好设置**
2. 进入 **系统 -> 常规**
3. 找到 **外部脚本使用**
4. 确保勾选：
   - ✅ 网络
   - ✅ 本地

## 推荐工作流

```
1. 启动 DaVinci Resolve
2. 创建/打开项目（AutoCut_Main）
3. 运行诊断工具验证：python diagnose_resolve.py
4. 启动 AutoCut Director：python run_server.py
5. 在 Web UI 中上传视频
6. 系统自动导入素材到 Resolve
```

## 技术说明

### 为什么需要打开的项目？

Resolve API 的设计：
- `GetCurrentProject()` 返回当前打开的项目
- 如果没有打开的项目，返回 `None`
- `CreateProject()` 创建项目但不打开
- 必须手动打开项目才能使用 Media Pool、Timeline 等功能

### 自动创建的限制

代码中的自动创建逻辑：

```python
# 尝试创建项目
proj = pm.CreateProject(project_name)

# 如果创建失败，尝试加载现有项目
if not proj:
    projects = pm.GetProjectListInCurrentFolder()
    if projects:
        pm.LoadProject(projects[0])
        proj = pm.GetCurrentProject()
```

**问题**：`LoadProject()` 也不会自动打开项目到编辑界面。

**解决**：用户必须在 Resolve 中手动双击打开。

## 总结

**最简单的解决方案**：

1. ✅ 在 Resolve 中手动创建一个项目
2. ✅ 双击打开到编辑界面
3. ✅ 运行 AutoCut Director

**一劳永逸**：

创建一个专用项目 `AutoCut_Main`，每次使用 AutoCut Director 前先打开这个项目。

---

**版本**: v1.7.2  
**日期**: 2026-02-05  
**状态**: ✅ 快速修复指南
