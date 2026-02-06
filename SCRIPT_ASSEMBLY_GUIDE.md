# Script Assembly - 零散镜头组装指南

## 概述

Script Assembly 是 AutoCut Director 的第二种工作流，专门用于将多个零散的视频片段组装成完整的视频。

## 工作流对比

| 特性 | 单视频剪辑 | 零散镜头组装 |
|------|-----------|-------------|
| 输入 | 一个完整视频 | 多个视频片段 |
| 场景识别 | 自动检测 | 使用 asset_id |
| 语音识别 | 自动 ASR | 可选 |
| 组装逻辑 | AI 自动 | 脚本大纲指定 |
| 适用场景 | 长视频剪辑 | 素材库组装 |

## 使用方法

### 1. 准备素材清单

创建 `assets_manifest.json` 文件：

```json
{
  "manifest_version": "1.0",
  "project_name": "我的项目",
  "assets": [
    {
      "asset_id": "asset_001",
      "path": "C:/Videos/clips/intro.mp4",
      "type": "video",
      "duration_seconds": 5.2,
      "duration_frames": 156,
      "fps": 30,
      "resolution": "1920x1080",
      "metadata": {
        "description": "开场镜头",
        "tags": ["intro", "hook"]
      }
    },
    {
      "asset_id": "asset_002",
      "path": "C:/Videos/clips/main.mp4",
      "type": "video",
      "duration_seconds": 12.5,
      "duration_frames": 375,
      "fps": 30,
      "resolution": "1920x1080",
      "metadata": {
        "description": "主要内容",
        "tags": ["main", "teaching"]
      }
    }
  ]
}
```

**必填字段**：
- `asset_id` - 素材唯一标识
- `path` - 素材文件路径（绝对路径）
- `type` - 素材类型（video/audio/image）
- `duration_frames` - 时长（帧数）

**可选字段**：
- `duration_seconds` - 时长（秒）
- `fps` - 帧率
- `resolution` - 分辨率
- `metadata` - 元数据（描述、标签等）

### 2. 准备脚本大纲（可选）

创建 `script_outline.json` 文件：

```json
{
  "script_version": "1.0",
  "structure": {
    "intro": {
      "description": "开场部分",
      "duration_target": "3-5秒",
      "assets": ["asset_001"],
      "style": "快速吸引注意力"
    },
    "main_content": {
      "description": "主要内容",
      "sections": [
        {
          "section_id": "section_01",
          "assets": ["asset_002"]
        }
      ]
    },
    "outro": {
      "description": "结尾部分",
      "assets": ["asset_003"]
    }
  },
  "assembly_rules": {
    "pace": "fast",
    "transitions": "smooth",
    "music": "emotional"
  }
}
```

**如果不提供脚本大纲**：
- AI 会根据素材内容自动组装
- 根据 metadata 中的 tags 进行智能排序
- 自动添加转场和音乐

### 3. 在 UI 中使用

1. 打开 http://localhost:8787/
2. 选择 **🎞️ 零散镜头组装** 工作流
3. 上传 `assets_manifest.json`
4. （可选）上传 `script_outline.json`
5. 选择平台和风格
6. 点击 **✨ 开始 AI 剪辑**

### 4. 使用 API

```bash
curl -X POST http://localhost:8787/api/assembly/create \
  -F "assets_manifest=@assets_manifest.json" \
  -F "script_outline=@script_outline.json" \
  -F "platform=douyin" \
  -F "style=viral"
```

## DSL 差异

### 单视频剪辑 DSL

```json
{
  "editing_plan": {
    "timeline": [
      {
        "scene_id": "scene_001",
        "trim_frames": [0, 150]
      }
    ]
  }
}
```

### 零散镜头组装 DSL

```json
{
  "editing_plan": {
    "timeline": [
      {
        "asset_id": "asset_001",
        "trim_frames": [0, 150]
      }
    ]
  }
}
```

**关键差异**：
- 使用 `asset_id` 代替 `scene_id`
- 素材来自不同文件，不是同一个视频的不同场景

## Resolve 自动导入

### 导入流程

1. **检查 Resolve 状态**
   - 检查 DaVinci Resolve 是否启动
   - 检查是否打开了项目

2. **导入素材到 Media Pool**
   - 自动导入所有素材文件
   - 创建专用 bin（文件夹）
   - 建立 asset_id → MediaItem 映射

3. **UI 显示状态**
   - ✓ 已同步到剪辑引擎 (项目名称)
   - ⚠️ DaVinci Resolve 未启动，跳过同步

### 手动导入

如果自动导入失败，可以手动导入：

```python
from app.tools.resolve_importer import get_importer

importer = get_importer()

# 从清单导入
result = importer.import_from_manifest("assets_manifest.json")

print(result["message"])
# 成功导入 5 个文件
```

## 完整示例

### 示例 1：教学视频组装

**素材清单**：
- intro.mp4 - 开场介绍
- step1.mp4 - 步骤1演示
- step2.mp4 - 步骤2演示
- step3.mp4 - 步骤3演示
- outro.mp4 - 结尾总结

**脚本大纲**：
```json
{
  "structure": {
    "intro": {"assets": ["intro"]},
    "main_content": {
      "sections": [
        {"assets": ["step1"]},
        {"assets": ["step2"]},
        {"assets": ["step3"]}
      ]
    },
    "outro": {"assets": ["outro"]}
  }
}
```

### 示例 2：产品宣传片

**素材清单**：
- product_shot_01.mp4
- product_shot_02.mp4
- product_shot_03.mp4
- customer_testimonial.mp4
- cta.mp4

**不提供脚本大纲**，让 AI 自动组装：
- AI 会根据 metadata 中的 tags 排序
- 自动添加转场效果
- 自动匹配背景音乐

## 最佳实践

### 1. 素材命名

使用有意义的 asset_id：
- ✅ `intro_hook`
- ✅ `main_demo_01`
- ✅ `outro_cta`
- ❌ `clip1`
- ❌ `video_final_v2`

### 2. 元数据标签

添加有用的标签：
```json
{
  "metadata": {
    "tags": ["intro", "hook", "fast-paced"],
    "emotion": "exciting",
    "importance": "high"
  }
}
```

### 3. 文件路径

使用绝对路径：
- ✅ `C:/Videos/clips/intro.mp4`
- ✅ `/Users/username/Videos/intro.mp4`
- ❌ `./intro.mp4`
- ❌ `intro.mp4`

### 4. 时长信息

提供准确的时长：
```json
{
  "duration_seconds": 5.2,
  "duration_frames": 156,
  "fps": 30
}
```

### 5. 脚本大纲

如果有明确的组装逻辑，提供脚本大纲：
- 指定素材顺序
- 指定转场位置
- 指定节奏要求

如果没有，让 AI 自动组装：
- AI 会分析素材内容
- 根据标签智能排序
- 自动优化节奏

## 故障排除

### 问题 1：素材导入失败

**原因**：
- 文件路径不存在
- DaVinci Resolve 未启动
- 文件格式不支持

**解决**：
- 检查文件路径是否正确
- 启动 DaVinci Resolve 并打开项目
- 转换文件格式为 MP4

### 问题 2：组装顺序不对

**原因**：
- 没有提供脚本大纲
- AI 自动排序不符合预期

**解决**：
- 提供明确的脚本大纲
- 在 metadata 中添加 `order` 字段
- 使用更清晰的标签

### 问题 3：时长计算错误

**原因**：
- duration_frames 不准确
- fps 不匹配

**解决**：
- 使用 ffprobe 获取准确时长
- 确保 fps 与实际视频一致

## API 参考

### 创建组装项目

```
POST /api/assembly/create
```

**参数**：
- `assets_manifest` (file) - 素材清单文件
- `script_outline` (file, optional) - 脚本大纲文件
- `platform` (string) - 平台选择
- `style` (string) - 风格选择
- `pace` (string) - 节奏选择
- `subtitle_density` (string) - 字幕密度
- `music_preference` (string) - 音乐偏好

**响应**：
```json
{
  "project_id": "asm_20260205_143000",
  "status": "processing",
  "workflow": "script_assembly",
  "message": "项目创建成功，正在处理中..."
}
```

### 获取组装状态

```
GET /api/assembly/{project_id}/status
```

**响应**：
```json
{
  "project_id": "asm_20260205_143000",
  "workflow": "script_assembly",
  "status": "processing",
  "progress": 65,
  "current_step": "dsl_generation"
}
```

## 总结

Script Assembly 工作流适合：
- ✅ 有多个零散视频片段
- ✅ 需要按特定顺序组装
- ✅ 素材来自不同来源
- ✅ 需要灵活的组装逻辑

不适合：
- ❌ 只有一个完整视频（使用单视频剪辑）
- ❌ 需要场景检测（使用单视频剪辑）
- ❌ 需要语音识别（使用单视频剪辑）

---

**版本**: v1.7.0  
**日期**: 2026-02-05  
**状态**: ✅ 已实现
