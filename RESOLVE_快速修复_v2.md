# 达芬奇连接问题 - 快速修复

## 问题

你看到的错误：
```
DLL load failed while importing fusionscript: 找不到指定的模块。
```

## 原因

**达芬奇必须运行才能连接！**

达芬奇的 Python API 依赖于达芬奇进程中的 DLL 文件，这些 DLL 只有在达芬奇运行时才能被加载。

---

## 解决方案（3 步）

### 1️⃣ 启动达芬奇

打开 **DaVinci Resolve**，等待完全启动

### 2️⃣ 创建或打开项目

**重要**: 必须有一个打开的项目！

- 点击 **File** → **New Project**
- 输入项目名称（如 "AutoCut Test"）
- 点击 **Create**

### 3️⃣ 测试连接

运行测试脚本：

```powershell
python test_resolve_quick.py
```

如果看到 "✓ 连接成功"，就可以使用了！

---

## 正确的启动顺序

```
1. 启动达芬奇 → 2. 打开项目 → 3. 启动 AutoCut → 4. 处理视频
```

### 使用自动检查脚本

我已经创建了一个启动脚本，会自动检查达芬奇状态：

```powershell
.\start_with_resolve_check.ps1
```

这个脚本会：
- ✅ 检查达芬奇是否运行
- ✅ 检查 Python 环境
- ✅ 检查项目依赖
- ✅ 启动 AutoCut Director

---

## 常见问题

### Q: 达芬奇已启动，但仍然连接失败？

**检查**:
1. 是否有打开的项目？（必须有！）
2. 达芬奇是否完全启动？（不是启动画面）
3. 达芬奇版本是否支持脚本？（需要 16+ 版本）

### Q: 我的达芬奇版本支持脚本吗？

**支持的版本**:
- ✅ DaVinci Resolve Studio（所有版本）
- ✅ DaVinci Resolve 免费版（16+ 版本）
- ✗ 旧版本（15 及以下）

### Q: 需要启用什么设置吗？

**可选设置**（某些版本需要）:
1. 打开达芬奇
2. 进入 **Preferences** (偏好设置)
3. **System** → **General**
4. 启用 **External scripting using**

---

## 测试命令

```powershell
# 快速测试（推荐）
python test_resolve_quick.py

# 完整诊断
python diagnose_resolve.py

# 测试项目创建
python test_resolve_project_creation.py
```

---

## 总结

✅ **必须做的**:
1. 启动达芬奇
2. 打开一个项目
3. 然后启动 AutoCut Director

✅ **推荐使用**:
```powershell
.\start_with_resolve_check.ps1
```

这个脚本会自动检查所有条件！

---

## 下一步

1. **现在**: 启动达芬奇并打开一个项目
2. **然后**: 运行 `python test_resolve_quick.py` 测试连接
3. **最后**: 运行 `.\start_with_resolve_check.ps1` 启动服务

如果还有问题，查看详细文档：[RESOLVE_CONNECTION_FIX.md](RESOLVE_CONNECTION_FIX.md)
