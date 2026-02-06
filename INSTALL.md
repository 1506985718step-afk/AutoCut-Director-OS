# AutoCut Director 安装指南

## 1. 创建虚拟环境

```bash
python -m venv .venv
```

## 2. 激活虚拟环境

**Windows:**
```powershell
.\.venv\Scripts\activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

## 3. 安装依赖

```bash
pip install -r requirements.txt
```

## 4. 配置 DaVinci Resolve

运行环境配置脚本：

```powershell
.\scripts\set_resolve_env.ps1
```

或手动设置：

```powershell
$env:RESOLVE_SCRIPT_DIR = "C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
$env:PYTHONPATH = "$env:RESOLVE_SCRIPT_DIR;$env:PYTHONPATH"
```

## 5. 验证安装

```bash
# 测试 Resolve 连接（需要先启动 Resolve）
python test_resolve_connection.py
```

## 6. 启动服务

```bash
python -m app.main
```

服务运行在 `http://localhost:8000`

## 依赖说明

- **fastapi==0.115.0** - Web 框架
- **uvicorn[standard]==0.30.6** - ASGI 服务器
- **pydantic==2.8.2** - 数据验证
- **python-multipart==0.0.9** - 文件上传支持
- **orjson==3.10.7** - 高性能 JSON
- **faster-whisper==1.0.3** - ASR 转录
- **ffmpeg-python==0.2.0** - 视频处理

## 故障排除

### Q: pip install 失败

**A:** 确保使用 Python 3.11+：
```bash
python --version
```

### Q: faster-whisper 安装失败

**A:** 需要先安装 ffmpeg：
```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### Q: DaVinci Resolve 连接失败

**A:** 
1. 确保 Resolve 正在运行
2. 打开一个项目
3. 检查 Preferences > System > General > "External scripting using"
