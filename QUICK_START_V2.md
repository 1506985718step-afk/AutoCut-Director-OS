# AutoCut Director - 快速开始 v2.0

## 🚀 5 分钟快速上手

### 1. 启动服务器

```bash
cd autocut-director
python run_server.py
```

看到这个就成功了：
```
============================================================
AutoCut Director - Starting Server
============================================================

Server: http://localhost:8787
API Docs: http://localhost:8787/docs
```

### 2. 打开浏览器

访问: **http://localhost:8787/**

你会看到一个简洁的 4 步流程界面。

### 3. 上传视频并开始剪辑

#### 步骤 1: 新建剪辑
1. 拖拽视频到上传区域（或点击选择）
2. 选择目标平台：
   - 抖音（竖屏 9:16）
   - B站（横屏 16:9）
   - YouTube（横屏 16:9）
   - 快手（竖屏 9:16）
3. 选择视频风格：
   - 🔥 爆款风格（快节奏、强视觉）
   - 📚 教学风格（清晰完整）
   - 💝 情感风格（温暖感人）
   - 📹 Vlog 风格（自然真实）
4. 点击 **✨ 开始 AI 剪辑**

#### 步骤 2: 等待处理（3-5 分钟）
系统会自动完成：
- ✓ 视频已导入
- ✓ 音频已分析
- ✓ 场景已拆分
- ✓ AI 生成剪辑方案
- ✓ 自动剪辑

你会看到实时进度和预计剩余时间。

#### 步骤 3: 预览 & 修改
1. 播放预览视频
2. 查看剪辑摘要（Hook/节奏/BGM/时长）
3. 如果不满意，点击调整按钮：
   - 🔥 Hook 更狠 / 💝 Hook 更温和
   - ⚡ 节奏更快 / 🐢 节奏更慢
   - 🎵 换一首音乐
   - 📝 字幕更大
4. 满意后点击 **✓ 满意，导出成片**

#### 步骤 4: 导出 & 下载
1. 选择导出质量：
   - 📱 1080p（适合抖音/快手）
   - 🖥️ 4K（高清质量）
2. 点击导出
3. 等待导出完成（1-2 分钟）
4. 点击 **💾 下载成片**

---

## 🎯 核心特点

### 1. 用户友好
- ❌ 不需要懂技术
- ❌ 不需要看 API 文档
- ❌ 不需要编辑 JSON
- ✅ 只需表达意图

### 2. 意图式调整
你说：**"节奏更快"**  
系统做：重新生成 DSL → 重新剪辑 → 生成新预览

你说：**"Hook 更狠"**  
系统做：选择更有冲击力的开场 → 重新剪辑

### 3. 版本管理
- 每次调整自动创建新版本（V1, V2, V3...）
- 可以随时回到之前的版本
- 不会丢失任何工作

### 4. 实时反馈
- 实时进度条
- 时间线式步骤展示
- 预计剩余时间
- 详细日志（可折叠）

---

## 📋 API 快速参考

### 产品级 API（用户使用）

```bash
# 创建项目
curl -X POST http://localhost:8787/api/projects/create \
  -F "video=@video.mp4" \
  -F "platform=douyin" \
  -F "style=viral"

# 获取项目状态
curl http://localhost:8787/api/projects/{project_id}/status

# 获取项目详情
curl http://localhost:8787/api/projects/{project_id}

# 获取预览视频
curl http://localhost:8787/api/projects/{project_id}/preview

# 调整项目
curl -X POST http://localhost:8787/api/projects/{project_id}/adjust \
  -H "Content-Type: application/json" \
  -d '{"adjustments": {"pace": "faster", "hook": "stronger"}}'

# 获取版本列表
curl http://localhost:8787/api/projects/{project_id}/versions

# 创建导出
curl -X POST http://localhost:8787/api/exports/ \
  -H "Content-Type: application/json" \
  -d '{"project_id": "proj_xxx", "quality": "1080p"}'

# 下载成片
curl http://localhost:8787/api/exports/{export_id}/download -o video.mp4
```

### 技术级 API（开发者使用）

访问: http://localhost:8787/docs

---

## 🔧 配置说明

### 平台选择

| 平台 | 比例 | 分辨率 | 最大时长 |
|------|------|--------|---------|
| 抖音 | 9:16 | 1080×1920 | 60秒 |
| 快手 | 9:16 | 1080×1920 | 60秒 |
| B站 | 16:9 | 1920×1080 | 10分钟 |
| YouTube | 16:9 | 1920×1080 | 15分钟 |

### 风格选择

| 风格 | 特点 | 适用场景 |
|------|------|---------|
| 爆款 | 节奏快、文字多、强调关键词 | 短视频、营销 |
| 教学 | 节奏适中、字幕完整、强调知识点 | 教程、讲解 |
| 情感 | 温暖感人、保留情感瞬间 | 故事、Vlog |
| Vlog | 自然真实、保留有趣瞬间 | 生活记录 |

### 调整选项

| 调整 | 效果 |
|------|------|
| 节奏更快 | 删除更多停顿，每个场景 3-5 秒 |
| 节奏更慢 | 保留更多内容和停顿 |
| Hook 更狠 | 使用更有冲击力的开场 |
| Hook 更温和 | 使用更自然的开场 |
| 换一首音乐 | 从 BGM 库选择下一首 |
| 字幕更大 | 增大字幕尺寸 |

---

## 🐛 常见问题

### Q: 视频上传失败？
A: 
- 检查文件大小（最大 2GB）
- 检查文件格式（支持 MP4, MOV, AVI）
- 检查网络连接

### Q: 处理时间太长？
A: 
- 正常处理时间：3-5 分钟
- 如果超过 10 分钟，检查服务器日志
- 可以查看详细日志了解当前进度

### Q: 预览视频无法播放？
A: 
- 检查浏览器（推荐 Chrome/Edge）
- 刷新页面
- 检查服务器是否正常运行

### Q: 调整不生效？
A: 
- 等待处理完成（按钮会显示"✓ 已应用"）
- 刷新预览查看效果
- 可以多次调整

### Q: 如何查看 API 文档？
A: 
- 访问 http://localhost:8787/admin
- 或直接访问 http://localhost:8787/docs

---

## 📁 文件位置

### 项目文件

```
jobs/
├── proj_20260205_143000/          # 项目 V1
│   ├── project_meta.json          # 项目元数据
│   ├── input/                     # 原始视频
│   ├── temp/                      # 临时文件
│   │   ├── audio.wav              # 提取的音频
│   │   ├── transcript.json        # 语音识别结果
│   │   ├── scenes.json            # 场景切分
│   │   ├── editing_dsl.json       # 剪辑指令
│   │   └── preview_480p.mp4       # 预览视频
│   └── output/                    # 输出文件
│       └── final.mp4              # 最终成片
│
└── proj_20260205_143000_v2/       # 项目 V2（调整后）
    └── ...
```

### 导出文件

```
exports/
├── export_20260205_143000_1080p.mp4
└── export_20260205_143000_4k.mp4
```

---

## 🎓 进阶使用

### 1. 批量处理

```python
import requests

videos = ["video1.mp4", "video2.mp4", "video3.mp4"]

for video in videos:
    with open(video, 'rb') as f:
        response = requests.post(
            "http://localhost:8787/api/projects/create",
            files={'video': f},
            data={
                'platform': 'douyin',
                'style': 'viral'
            }
        )
        print(f"Created: {response.json()['project_id']}")
```

### 2. 自定义映射

编辑 `config/ui_dsl_mapping.json` 添加自定义风格：

```json
{
  "style_prompts": {
    "my_style": "我的自定义风格：..."
  }
}
```

### 3. 监控进度

```python
import requests
import time

project_id = "proj_xxx"

while True:
    response = requests.get(f"http://localhost:8787/api/projects/{project_id}/status")
    status = response.json()
    
    print(f"Progress: {status['progress']}%")
    
    if status['status'] == 'completed':
        break
    
    time.sleep(2)
```

---

## 🆘 获取帮助

### 文档

- **用户指南**: `USER_GUIDE.md`
- **API 文档**: http://localhost:8787/docs
- **架构文档**: `ARCHITECTURE.md`
- **实现文档**: `IMPLEMENTATION_COMPLETE.md`

### 日志

- **服务器日志**: 终端输出
- **项目日志**: `jobs/{project_id}/trace.json`
- **前端日志**: 浏览器控制台

### 测试

```bash
# 测试 UI 翻译器
python test_product_api.py

# 测试完整流程（需要测试视频）
# 创建 test_video.mp4 后运行
python test_product_api.py
```

---

## ✅ 检查清单

启动前检查：
- [ ] Python 3.9+ 已安装
- [ ] 依赖已安装（`pip install -r requirements.txt`）
- [ ] DaVinci Resolve 已安装（如需实际剪辑）
- [ ] 端口 8787 未被占用

使用前检查：
- [ ] 服务器已启动
- [ ] 浏览器已打开 http://localhost:8787/
- [ ] 视频文件已准备（MP4/MOV/AVI，< 2GB）

---

**版本**: v2.0  
**更新**: 2026-02-05  
**状态**: ✅ 生产就绪（核心功能）

开始使用吧！🎬
