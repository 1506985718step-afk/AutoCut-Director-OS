# BGM 子系统 MVP 设计

## 🎯 设计目标

创建一个简单、实用的本地 BGM 素材库管理系统，让 LLM 能够智能选择合适的背景音乐。

---

## 📁 目录结构

```
bgm_library/
├── calm/
│   ├── calm_090bpm.mp3
│   ├── calm_090bpm.json          # 元数据
│   ├── calm_100bpm.mp3
│   └── calm_100bpm.json
├── emotional/
│   ├── emo_120bpm.mp3
│   └── emo_120bpm.json
├── fast/
│   ├── fast_140bpm.mp3
│   └── fast_140bpm.json
└── suspense/
    ├── sus_110bpm.mp3
    └── sus_110bpm.json
```

**设计原则**:
- ✅ 按 mood 分类（calm, emotional, fast, suspense, happy, sad）
- ✅ 文件名包含关键信息（mood_bpm）
- ✅ 每首音乐配一个 metadata.json
- ✅ 支持自动生成元数据

---

## 📋 元数据格式

### metadata.json 示例

```json
{
  "id": "emo_120_01",
  "path": "bgm_library/emotional/emo_120bpm.mp3",
  "bpm": 120,
  "mood": "emotional",
  "energy": "medium",
  "usage": ["story", "teaching"],
  "copyright": "royalty_free",
  "duration_sec": 180.5,
  "tags": ["emotional", "medium", "120bpm"]
}
```

### 字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `id` | string | 唯一标识符 | "emo_120_01" |
| `path` | string | 文件路径（相对路径） | "bgm_library/emotional/emo_120bpm.mp3" |
| `bpm` | int | 节奏（每分钟拍数） | 120 |
| `mood` | string | 情绪分类 | "emotional" |
| `energy` | string | 能量级别 | "low", "medium", "high" |
| `usage` | list | 适用场景 | ["story", "teaching"] |
| `copyright` | string | 版权信息 | "royalty_free" |
| `duration_sec` | float | 时长（秒） | 180.5 |
| `tags` | list | 标签 | ["emotional", "medium"] |

---

## 🎵 Mood 分类

| Mood | BPM 范围 | Energy | 适用场景 |
|------|---------|--------|---------|
| **calm** | 80-100 | low | 教学、冥想、背景 |
| **emotional** | 100-130 | medium | 故事、戏剧、感人 |
| **fast** | 130-160 | high | 动作、运动、活力 |
| **suspense** | 90-120 | medium | 悬疑、神秘、紧张 |
| **happy** | 110-140 | medium-high | Vlog、庆祝、欢快 |
| **sad** | 70-90 | low | 戏剧、情感、反思 |

---

## 🔧 核心功能

### 1. BGMLibrary 类

```python
from app.tools.bgm_library import BGMLibrary

# 初始化
library = BGMLibrary("bgm_library")

# 扫描库（自动生成元数据）
bgm_list = library.scan_library(auto_generate_metadata=True)

# 搜索 BGM
results = library.search(
    mood="calm",
    energy="low",
    bpm_range=(80, 100),
    usage="teaching"
)

# 根据 ID 获取
bgm = library.get_by_id("calm_090_01")

# 导出为 LLM 格式
llm_data = library.export_for_llm()
```

---

### 2. 自动元数据生成

**文件名格式**: `{mood}_{bpm}bpm.mp3`

**自动推断规则**:
1. **mood**: 从目录名推断
2. **bpm**: 从文件名提取（如 "090bpm" → 90）
3. **energy**: 根据 BPM 推断
   - < 100: low
   - 100-130: medium
   - > 130: high
4. **usage**: 根据 mood 映射
5. **id**: 自动生成（mood_bpm_序号）

---

### 3. 搜索功能

```python
# 按 mood 搜索
library.search(mood="calm")

# 按 energy 搜索
library.search(energy="medium")

# 按 BPM 范围搜索
library.search(bpm_range=(100, 120))

# 按 usage 搜索
library.search(usage="teaching")

# 组合搜索
library.search(
    mood="emotional",
    energy="medium",
    usage="story"
)
```

---

### 4. LLM 集成

```python
from app.core.llm_engine import LLMDirector
from app.tools.bgm_library import create_bgm_library

# 加载 BGM 库
library = create_bgm_library("bgm_library")
bgm_data = library.export_for_llm()

# 生成 DSL（包含 BGM 选择）
director = LLMDirector()
dsl = director.generate_editing_dsl(
    scenes=scenes,
    transcript=transcript,
    style_prompt="抖音爆款风格",
    bgm_library=bgm_data  # 传入 BGM 库
)

# LLM 会在 music 字段中选择合适的 BGM
# {
#   "music": {
#     "bgm_id": "calm_090_01",
#     "volume_db": -18
#   }
# }
```

---

## 🚀 快速开始

### 1. 创建示例库

```bash
cd autocut-director
python test_bgm_library.py
```

这会创建示例目录结构和元数据文件。

---

### 2. 添加实际音频

将实际音频文件放入对应目录：

```bash
bgm_library/
├── calm/
│   ├── calm_090bpm.mp3  # 替换为实际音频
│   └── calm_090bpm.json # 保留元数据
```

---

### 3. 重新扫描

```python
from app.tools.bgm_library import BGMLibrary

library = BGMLibrary("bgm_library")
library.scan_library()  # 重新扫描
```

---

### 4. 在 LLM 中使用

```python
# 加载 BGM 库
library = create_bgm_library("bgm_library")
bgm_data = library.export_for_llm()

# 生成 DSL
dsl = director.generate_editing_dsl(
    scenes, transcript, style, 
    bgm_library=bgm_data
)
```

---

## 📊 LLM 输出格式

### DSL 中的 music 字段

```json
{
  "editing_plan": {
    "music": {
      "bgm_id": "calm_090_01",  // 从 BGM 库中选择
      "volume_db": -18          // 音量（dB）
    }
  }
}
```

### LLM 选择逻辑

LLM 会根据以下因素选择 BGM：

1. **视频内容**: 教学视频 → calm, 故事视频 → emotional
2. **剪辑节奏**: 快节奏 → fast, 慢节奏 → calm
3. **情感基调**: 感人 → emotional, 紧张 → suspense
4. **BPM 匹配**: 剪辑节奏与 BGM 节奏协调

---

## 🎯 使用场景

### 场景 1: 教学视频

```python
# 搜索适合教学的 BGM
results = library.search(
    mood="calm",
    energy="low",
    usage="teaching"
)

# LLM 会选择: calm_090_01 或 calm_100_01
```

---

### 场景 2: 故事视频

```python
# 搜索适合故事的 BGM
results = library.search(
    mood="emotional",
    usage="story"
)

# LLM 会选择: emo_120_01
```

---

### 场景 3: 快节奏 Vlog

```python
# 搜索快节奏 BGM
results = library.search(
    mood="fast",
    energy="high"
)

# LLM 会选择: fast_140_01
```

---

## 🔍 测试验证

### 运行测试

```bash
cd autocut-director
python test_bgm_library.py
```

### 测试内容

1. ✅ 创建示例库
2. ✅ 扫描 BGM 库
3. ✅ 搜索功能（mood, energy, BPM, usage）
4. ✅ 导出为 LLM 格式
5. ✅ 根据 ID 获取
6. ✅ 便捷函数

---

## 📝 元数据管理

### 手动创建元数据

```json
{
  "id": "custom_bgm_01",
  "path": "bgm_library/custom/my_bgm.mp3",
  "bpm": 115,
  "mood": "happy",
  "energy": "medium",
  "usage": ["vlog", "celebration"],
  "copyright": "licensed",
  "duration_sec": 240.0,
  "tags": ["happy", "upbeat", "115bpm"]
}
```

保存为 `my_bgm.json`，与音频文件同名。

---

### 批量更新元数据

```python
library = BGMLibrary("bgm_library")

# 重新扫描并生成元数据
library.scan_library(auto_generate_metadata=True)

# 所有音频文件都会生成对应的 .json 文件
```

---

## 🎨 扩展建议

### 1. 添加更多 Mood

```python
# 在 _generate_metadata() 中添加
usage_map = {
    "calm": ["teaching", "meditation"],
    "emotional": ["story", "drama"],
    "fast": ["action", "sports"],
    "suspense": ["thriller", "mystery"],
    "happy": ["vlog", "celebration"],  # 新增
    "sad": ["drama", "reflective"],    # 新增
    "epic": ["trailer", "cinematic"],  # 新增
}
```

---

### 2. 添加音频分析

使用 `librosa` 或 `pydub` 自动分析：
- 实际 BPM
- 音频时长
- 音量峰值
- 频谱特征

```python
import librosa

def analyze_audio(audio_path):
    y, sr = librosa.load(audio_path)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    duration = librosa.get_duration(y=y, sr=sr)
    
    return {
        "bpm": int(tempo),
        "duration_sec": duration
    }
```

---

### 3. 添加版权管理

```json
{
  "copyright": "licensed",
  "license_type": "CC BY 4.0",
  "attribution": "Artist Name",
  "license_url": "https://..."
}
```

---

## 📚 相关文档

- **[bgm_library.py](app/tools/bgm_library.py)** - BGM 库管理器
- **[llm_engine.py](app/core/llm_engine.py)** - LLM 引擎（BGM 集成）
- **[test_bgm_library.py](test_bgm_library.py)** - 测试脚本
- **[AUDIO_VOLUME_FIX.md](AUDIO_VOLUME_FIX.md)** - 音频音量设置

---

## 🎉 总结

### 核心特性

1. ✅ **简单**: 目录结构清晰，易于管理
2. ✅ **自动化**: 自动生成元数据
3. ✅ **智能**: LLM 智能选择 BGM
4. ✅ **灵活**: 支持多种搜索条件
5. ✅ **可扩展**: 易于添加新功能

### MVP 完成度

- ✅ 本地素材库管理
- ✅ 元数据自动生成
- ✅ 搜索和过滤
- ✅ LLM 集成
- ✅ 测试验证

### 下一步

1. 添加实际音频文件
2. 测试 LLM 选择效果
3. 根据需要扩展 mood 分类
4. 考虑添加音频分析功能

---

**版本**: v1.3.0  
**状态**: ✅ MVP 完成  
**日期**: 2025-02-05

