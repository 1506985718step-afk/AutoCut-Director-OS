# 字幕/花字工作流指南

## 概述

由于 DaVinci Resolve API 对字幕样式控制有限，我们采用 **SRT + Resolve 手动样式** 的混合方案，这是最稳定、最灵活的实现方式。

## 🎯 核心策略

### 方案选择

1. **SRT 字幕（推荐）** ⭐
   - ✅ 最稳定，Resolve 原生支持
   - ✅ 可以在 Resolve 中完全控制样式
   - ✅ 支持保存样式预设
   - ❌ 需要手动设置样式（首次）

2. **Fusion Title（高级）**
   - ✅ 完全控制样式和动画
   - ❌ API 支持有限
   - ❌ 需要 Resolve Studio 版本
   - ❌ 实现复杂

**结论**: 使用 SRT 方案，首次手动设置样式并保存预设，后续自动化应用。

---

## 📝 完整工作流

### 阶段 1: 生成 SRT 文件

#### 方式 1: 从 transcript 生成完整字幕

```python
from app.tools.srt_generator import transcript_to_srt

# 加载 transcript
transcript_data = json.load(open("transcript.json"))

# 生成 SRT
transcript_to_srt(
    transcript_segments=transcript_data["segments"],
    output_path="subtitles.srt"
)
```

#### 方式 2: 从 DSL 生成文字叠加

```python
from app.tools.srt_generator import overlay_text_to_srt

# 从 DSL 提取 overlay_text
text_items = [
    {
        "content": "第一步就错了",
        "start_frame": 30,
        "duration_frames": 60
    },
    {
        "content": "90%的人都不知道",
        "start_frame": 120,
        "duration_frames": 90
    }
]

# 生成 SRT
overlay_text_to_srt(
    text_items=text_items,
    fps=30,
    output_path="overlay.srt"
)
```

#### 方式 3: 命令行工具

```bash
# 从 transcript 生成
python app/tools/srt_generator.py transcript transcript.json subtitles.srt

# 从 DSL 生成
python app/tools/srt_generator.py dsl editing_dsl.json 30 output_dir
```

---

### 阶段 2: 在 Resolve 中设置样式（首次）

#### 步骤 1: 导入 SRT

1. 打开 DaVinci Resolve
2. 进入 Edit 页面
3. 导入 SRT 文件：
   - 方式 A: `File > Import > Subtitle`
   - 方式 B: 直接拖拽 SRT 文件到时间线

#### 步骤 2: 调整字幕样式

1. 选中字幕轨道上的字幕片段
2. 打开 Inspector 面板（右侧）
3. 在 Video 标签下调整：

**抖音爆款风格设置**:
```
字体 (Font):
  - 字体: 思源黑体 Bold / 微软雅黑 Bold
  - 大小: 72-80

颜色 (Color):
  - 填充颜色: 黄色 (#FFFF00)
  - 不透明度: 100%

描边 (Stroke):
  - 启用描边: ✓
  - 描边颜色: 黑色 (#000000)
  - 描边宽度: 3-4
  - 描边不透明度: 100%

位置 (Position):
  - 垂直位置: 底部偏上（约 80%）
  - 水平对齐: 居中

阴影 (Shadow) - 可选:
  - 启用阴影: ✓
  - 阴影颜色: 黑色
  - 阴影偏移: 2-3
  - 阴影模糊: 5-8
```

**B站简洁风格设置**:
```
字体: 思源黑体 Regular
大小: 56-64
填充颜色: 白色 (#FFFFFF)
描边: 黑色，宽度 2
位置: 底部（约 85%）
```

**YouTube Vlog 风格设置**:
```
字体: Arial / Helvetica
大小: 48-56
填充颜色: 白色 (#FFFFFF)
描边: 黑色，宽度 1-2
位置: 底部（约 90%）
背景: 半透明黑色条（可选）
```

#### 步骤 3: 保存样式预设

1. 调整好样式后，右键点击字幕片段
2. 选择 `Save Title Style` 或 `Create Preset`
3. 命名预设（如 "Douyin_Bold_Yellow"）
4. 后续可以快速应用此预设

---

### 阶段 3: 自动化导入（API）

#### 使用 ResolveAdapter

```python
from app.executor.resolve_adapter import ResolveAdapter

adapter = ResolveAdapter()
adapter.connect()

# 创建时间线
adapter.create_timeline(
    name="My_Video",
    framerate=30,
    resolution={"width": 1080, "height": 1920}
)

# 方法 1: 导入完整字幕
adapter.render_subtitles_from_transcript(
    transcript_segments=transcript_data["segments"],
    fps=30,
    style="bold_yellow"  # 样式说明（实际样式在 Resolve 中应用）
)

# 方法 2: 导入文字叠加
adapter.create_text_layer_from_dsl(
    text_items=[
        {"content": "第一步就错了", "start_frame": 30, "duration_frames": 60},
        {"content": "90%的人都不知道", "start_frame": 120, "duration_frames": 90}
    ],
    track_index=3
)
```

#### 应用预设样式

导入后，在 Resolve 中：
1. 选中所有字幕片段（Ctrl+A）
2. 右键 > `Apply Title Style`
3. 选择之前保存的预设

或者使用脚本批量应用（需要 Resolve Studio）。

---

## 🎨 样式预设参考

### 1. 抖音爆款风格

**特点**: 大字、黄色、黑边、醒目

```
字体: 思源黑体 Bold
大小: 72-80
颜色: 黄色 (#FFFF00)
描边: 黑色 3-4px
位置: 底部偏上（80%）
动画: 可选淡入淡出
```

**适用场景**: 短视频、快节奏内容、强调关键词

### 2. B站知识区风格

**特点**: 清晰、完整、不遮挡

```
字体: 思源黑体 Regular
大小: 56-64
颜色: 白色 (#FFFFFF)
描边: 黑色 2px
位置: 底部（85%）
背景: 可选半透明黑条
```

**适用场景**: 教程、讲解、长视频

### 3. YouTube Vlog 风格

**特点**: 简洁、自然、不抢镜

```
字体: Arial / Helvetica
大小: 48-56
颜色: 白色 (#FFFFFF)
描边: 黑色 1-2px
位置: 底部（90%）
动画: 无或轻微
```

**适用场景**: Vlog、纪录片、访谈

### 4. 快手热门风格

**特点**: 接地气、情感强、对比大

```
字体: 微软雅黑 Bold
大小: 68-76
颜色: 红色 (#FF0000) 或黄色
描边: 白色 3-4px
位置: 中上部（30-40%）
动画: 弹跳、缩放
```

**适用场景**: 情感类、故事类、反转类

---

## 🔧 高级技巧

### 1. 双字幕轨道

同时使用完整字幕和文字叠加：

```python
# 轨道 2: 完整字幕（底部）
adapter.render_subtitles_from_transcript(
    transcript_segments=transcript_segments,
    fps=30,
    style="clean_white"
)

# 轨道 3: 关键词强调（中上部）
adapter.create_text_layer_from_dsl(
    text_items=overlay_text_items,
    track_index=3
)
```

在 Resolve 中分别设置样式：
- 轨道 2: 小字、底部、白色
- 轨道 3: 大字、中上部、黄色

### 2. 分段样式

对不同段落使用不同样式：

```python
# Hook 段（前 5 秒）- 红色大字
hook_items = [...]
overlay_text_to_srt(hook_items, fps=30, output_path="hook.srt")

# Body 段 - 黄色中字
body_items = [...]
overlay_text_to_srt(body_items, fps=30, output_path="body.srt")

# CTA 段 - 绿色大字
cta_items = [...]
overlay_text_to_srt(cta_items, fps=30, output_path="cta.srt")
```

分别导入并应用不同预设。

### 3. 动画效果

在 Resolve 中添加动画：
1. 选中字幕片段
2. 切换到 Fusion 页面
3. 添加动画节点：
   - Transform: 位置、缩放、旋转
   - Text+: 字符动画
   - Merge: 混合模式

常用动画：
- 淡入淡出（Fade In/Out）
- 弹跳（Bounce）
- 打字机效果（Typewriter）
- 描边动画（Stroke Animation）

### 4. 批量处理

使用 Python 脚本批量生成和导入：

```python
# 批量生成多个视频的字幕
videos = ["video1", "video2", "video3"]

for video in videos:
    # 生成 SRT
    transcript_to_srt(
        transcript_segments=load_transcript(f"{video}.json"),
        output_path=f"{video}_subtitles.srt"
    )
    
    # 导入到 Resolve（需要手动切换项目）
    adapter.render_subtitles_from_transcript(...)
```

---

## 📊 性能优化

### 1. SRT 文件大小

- 单个 SRT 文件建议不超过 1000 条字幕
- 超过时拆分为多个文件
- 使用简洁的文本，避免冗余

### 2. 导入速度

- 预先生成所有 SRT 文件
- 批量导入而非逐条添加
- 使用 SSD 存储临时文件

### 3. 样式应用

- 首次设置好预设
- 后续使用预设快速应用
- 避免逐条手动调整

---

## 🐛 常见问题

### Q1: SRT 导入后没有显示？

**解决**:
1. 检查 SRT 文件编码（必须是 UTF-8）
2. 检查时间格式（必须是 HH:MM:SS,mmm）
3. 检查时间线帧率是否匹配

### Q2: 字幕样式无法保存？

**解决**:
1. 确保使用 Resolve Studio 版本
2. 在 Inspector 中调整后，右键保存预设
3. 预设保存在 Resolve 配置目录

### Q3: 中文字幕显示乱码？

**解决**:
1. 确保 SRT 文件使用 UTF-8 编码
2. 在 Resolve 中选择支持中文的字体
3. 检查系统字体库

### Q4: API 导入失败？

**解决**:
1. 检查 Resolve 是否运行
2. 检查 RESOLVE_SCRIPT_DIR 环境变量
3. 检查 SRT 文件路径是否正确
4. 查看 Resolve 控制台错误信息

### Q5: 样式不一致？

**解决**:
1. 使用预设确保一致性
2. 检查是否选中了所有字幕片段
3. 确保应用了正确的预设

---

## 📚 参考资源

### DaVinci Resolve 字幕文档

- [Resolve 官方文档](https://www.blackmagicdesign.com/support)
- [Scripting API 参考](https://deric.github.io/DaVinciResolve-API-Docs/)

### SRT 格式规范

- [SRT 格式说明](https://en.wikipedia.org/wiki/SubRip)
- [字幕格式转换工具](https://subtitletools.com/)

### 字体推荐

- **中文**: 思源黑体、微软雅黑、阿里巴巴普惠体
- **英文**: Arial, Helvetica, Roboto, Open Sans
- **免费商用**: 思源黑体、阿里巴巴普惠体、站酷字体

---

## 🎯 最佳实践

### 1. 工作流标准化

```
1. 生成 SRT 文件（自动化）
2. 导入到 Resolve（API）
3. 应用预设样式（手动/脚本）
4. 微调个别字幕（手动）
5. 渲染导出（API）
```

### 2. 样式管理

- 为每个平台创建专用预设
- 定期备份预设文件
- 团队共享预设配置

### 3. 质量检查

- 检查字幕时间是否准确
- 检查文字是否遮挡关键画面
- 检查样式是否一致
- 检查特殊字符是否正常显示

---

**相关文档**:
- [LLM_INTEGRATION.md](LLM_INTEGRATION.md) - LLM 集成指南
- [BRAIN_AND_RENDER.md](BRAIN_AND_RENDER.md) - 功能概览
- [API_USAGE.md](API_USAGE.md) - API 使用指南
