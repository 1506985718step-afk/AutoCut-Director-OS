# DSL ↔ UI 映射表

## 核心原则

**UI 控件 → DSL 的映射必须是一张表，不是写死在代码里。**

这保证了：
- ✅ UI 永远简单
- ✅ DSL 可以不断进化
- ✅ AI 能持续学习

---

## 1. 平台选择 → DSL Meta

| UI 控件 | 用户看到 | DSL 字段 | DSL 值 |
|---------|---------|---------|--------|
| 平台选择 | 抖音 / 短视频（9:16） | `meta.target_platform` | `"douyin"` |
| | | `meta.aspect_ratio` | `"9:16"` |
| | | `meta.resolution` | `"1080x1920"` |
| 平台选择 | B站（16:9） | `meta.target_platform` | `"bilibili"` |
| | | `meta.aspect_ratio` | `"16:9"` |
| | | `meta.resolution` | `"1920x1080"` |
| 平台选择 | YouTube（16:9） | `meta.target_platform` | `"youtube"` |
| | | `meta.aspect_ratio` | `"16:9"` |
| | | `meta.resolution` | `"1920x1080"` |

---

## 2. 剪辑风格 → DSL Style Prompt

| UI 控件 | 用户看到 | 传给 LLM 的 Prompt |
|---------|---------|-------------------|
| 风格选择 | 教学讲解 | "B站教学风格：节奏适中、字幕完整、强调知识点、保留完整讲解内容" |
| 风格选择 | 情绪故事 | "情感风格：温暖感人、保留情感瞬间、适度剪辑、强调情绪共鸣" |
| 风格选择 | 爆款短视频 | "抖音爆款风格：节奏快、文字多、强调关键词、开头3秒Hook、删除废话" |
| 风格选择 | 自定义（高级） | 用户自定义文本 |

---

## 3. 高级选项 → DSL Editing Plan

### 3.1 节奏控制

| UI 控件 | 用户看到 | DSL 影响 | 具体实现 |
|---------|---------|---------|---------|
| 节奏 | 慢 | `timeline[].trim_frames` | 保留更多内容，trim 范围更宽松 |
| | | `editing_plan.pace` | `"slow"` |
| 节奏 | 中 | `timeline[].trim_frames` | 标准 trim，删除明显停顿 |
| | | `editing_plan.pace` | `"medium"` |
| 节奏 | 快 | `timeline[].trim_frames` | 激进 trim，只保留核心内容 |
| | | `editing_plan.pace` | `"fast"` |

**LLM Prompt 调整**：
- 慢：`"保留完整内容，只删除明显的废话和长停顿"`
- 中：`"删除停顿和重复，保持流畅"`
- 快：`"激进剪辑，只保留核心内容，每3-5秒切换画面"`

### 3.2 字幕密度

| UI 控件 | 用户看到 | DSL 影响 | 具体实现 |
|---------|---------|---------|---------|
| 字幕密度 | 少 | `subtitles.style` | `"minimal"` |
| | | `subtitles.highlight_keywords` | `false` |
| 字幕密度 | 标准 | `subtitles.style` | `"standard"` |
| | | `subtitles.highlight_keywords` | `true` |
| 字幕密度 | 多 | `subtitles.style` | `"dense"` |
| | | `subtitles.highlight_keywords` | `true` |
| | | `subtitles.overlay_text` | 添加更多文字叠加 |

### 3.3 音乐偏好

| UI 控件 | 用户看到 | DSL 影响 | 具体实现 |
|---------|---------|---------|---------|
| 音乐偏好 | 无 | `music` | `null` 或 `[]` |
| 音乐偏好 | 情绪 | `music[0].intent` | `"emotional"` |
| | | `music[0].mood` | `"emotional"` |
| | | BGM 库查询 | `mood="emotional"` |
| 音乐偏好 | 紧张 | `music[0].intent` | `"suspense"` |
| | | `music[0].mood` | `"suspense"` |
| 音乐偏好 | 轻快 | `music[0].intent` | `"upbeat"` |
| | | `music[0].mood` | `"fast"` |

---

## 4. 预览页面调整 → DSL 重新生成

### 4.1 节奏调整

| UI 控件 | 用户看到 | DSL 变化 | LLM Prompt 追加 |
|---------|---------|---------|----------------|
| 节奏 | 更慢 | `editing_plan.pace` → `"slower"` | "放慢节奏，保留更多内容和停顿" |
| | | `timeline[].trim_frames` 放宽 | |
| 节奏 | 保持 | 不变 | - |
| 节奏 | 更快 | `editing_plan.pace` → `"faster"` | "加快节奏，更激进地删除停顿和重复" |
| | | `timeline[].trim_frames` 收紧 | |

**实现逻辑**：
```python
if pace_adjustment == "faster":
    # 重新调用 LLM，追加 prompt
    new_prompt = original_prompt + "\n\n用户反馈：节奏太慢，请加快剪辑节奏，更激进地删除停顿。"
    new_dsl = llm_engine.generate_dsl(scenes, transcript, new_prompt)
```

### 4.2 开头 Hook 调整

| UI 控件 | 用户看到 | DSL 变化 | LLM Prompt 追加 |
|---------|---------|---------|----------------|
| 开头 | 更狠一点 | `timeline[0]` 场景替换 | "开头需要更强烈的Hook，选择最有冲击力的场景" |
| | | 可能添加 `overlay` 强调 | |
| 开头 | 现在这样 | 不变 | - |
| 开头 | 更自然 | `timeline[0]` 场景替换 | "开头更自然温和，不要太强烈" |

**实现逻辑**：
```python
if hook_adjustment == "stronger":
    # 重新排序场景，选择最有冲击力的
    new_prompt = original_prompt + "\n\n用户反馈：开头Hook不够强，请选择最有冲击力的场景作为开头。"
    new_dsl = llm_engine.generate_dsl(scenes, transcript, new_prompt)
```

### 4.3 音乐调整

| UI 控件 | 用户看到 | DSL 变化 | 实现逻辑 |
|---------|---------|---------|---------|
| 音乐 | 换一首 | `music[0].path` 改变 | 从 BGM 库查询下一首同类型音乐 |
| | | `music[0].id` 改变 | |
| 音乐 | 保持 | 不变 | - |
| 音乐 | 不要音乐 | `music` → `[]` | 移除所有音乐 |

**实现逻辑**：
```python
if music_adjustment == "change":
    # 从 BGM 库获取下一首
    current_mood = dsl["music"][0]["mood"]
    next_bgm = bgm_library.get_next(mood=current_mood, exclude=current_bgm_id)
    dsl["music"][0]["path"] = next_bgm["path"]
    dsl["music"][0]["id"] = next_bgm["id"]
```

### 4.4 字幕调整

| UI 控件 | 用户看到 | DSL 变化 | 实现逻辑 |
|---------|---------|---------|---------|
| 字幕 | 更少 | `subtitles.style` → `"minimal"` | 只保留关键句子 |
| | | `subtitles.highlight_keywords` → `false` | |
| 字幕 | 正常 | `subtitles.style` → `"standard"` | 标准字幕 |
| 字幕 | 更多 | `subtitles.style` → `"dense"` | 添加更多文字叠加 |
| | | `subtitles.overlay_text` 增加 | |

---

## 5. 版本管理 → Job Store

| UI 概念 | 后端实现 | 存储位置 |
|---------|---------|---------|
| V1 - 原始版本 | `job_id_v1` | `jobs/{job_id}_v1/` |
| V2 - 更快节奏 | `job_id_v2` | `jobs/{job_id}_v2/` |
| V3 - 当前版本 | `job_id_v3` | `jobs/{job_id}_v3/` |

**每个版本包含**：
- `dsl.json` - 该版本的 DSL
- `trace.json` - 执行记录
- `output/final.mp4` - 成片
- `temp/preview_480p.mp4` - 预览
- `meta.json` - 版本元信息

**meta.json 示例**：
```json
{
  "version": 3,
  "parent_version": 2,
  "created_at": "2026-02-05T14:30:00Z",
  "user_adjustments": {
    "pace": "faster",
    "hook": "stronger",
    "music": "change"
  },
  "summary": {
    "hook": "第 3 个场景（0:12–0:18）",
    "pace": "快",
    "music": "情绪型（120 BPM）",
    "duration": "42s"
  }
}
```

---

## 6. 映射表实现（代码级）

### 6.1 配置文件：`config/ui_dsl_mapping.json`

```json
{
  "platform_mapping": {
    "douyin": {
      "target_platform": "douyin",
      "aspect_ratio": "9:16",
      "resolution": "1080x1920"
    },
    "bilibili": {
      "target_platform": "bilibili",
      "aspect_ratio": "16:9",
      "resolution": "1920x1080"
    }
  },
  "style_prompts": {
    "teaching": "B站教学风格：节奏适中、字幕完整、强调知识点",
    "emotional": "情感风格：温暖感人、保留情感瞬间",
    "viral": "抖音爆款风格：节奏快、文字多、强调关键词、开头3秒Hook"
  },
  "pace_mapping": {
    "slow": {
      "dsl_value": "slow",
      "llm_prompt": "保留完整内容，只删除明显的废话和长停顿"
    },
    "medium": {
      "dsl_value": "medium",
      "llm_prompt": "删除停顿和重复，保持流畅"
    },
    "fast": {
      "dsl_value": "fast",
      "llm_prompt": "激进剪辑，只保留核心内容，每3-5秒切换画面"
    }
  },
  "adjustment_prompts": {
    "pace_faster": "用户反馈：节奏太慢，请加快剪辑节奏，更激进地删除停顿。",
    "pace_slower": "用户反馈：节奏太快，请放慢节奏，保留更多内容和停顿。",
    "hook_stronger": "用户反馈：开头Hook不够强，请选择最有冲击力的场景作为开头。",
    "hook_softer": "用户反馈：开头太强烈，请选择更自然温和的场景作为开头。"
  }
}
```

### 6.2 Python 实现：`app/core/ui_translator.py`

```python
class UITranslator:
    """UI 意图 → DSL 的翻译层"""
    
    def __init__(self, mapping_file="config/ui_dsl_mapping.json"):
        with open(mapping_file) as f:
            self.mapping = json.load(f)
    
    def translate_platform(self, ui_platform: str) -> dict:
        """平台选择 → DSL meta"""
        return self.mapping["platform_mapping"][ui_platform]
    
    def translate_style(self, ui_style: str) -> str:
        """风格选择 → LLM prompt"""
        return self.mapping["style_prompts"][ui_style]
    
    def translate_pace(self, ui_pace: str) -> dict:
        """节奏选择 → DSL + LLM prompt"""
        return self.mapping["pace_mapping"][ui_pace]
    
    def translate_adjustment(self, adjustment_type: str, adjustment_value: str) -> str:
        """用户调整 → LLM prompt 追加"""
        key = f"{adjustment_type}_{adjustment_value}"
        return self.mapping["adjustment_prompts"].get(key, "")
```

---

## 7. 前端实现示例

### 7.1 创建页面提交

```javascript
async function startEditing() {
    const formData = {
        platform: document.getElementById('platform').value,  // "douyin"
        style: document.getElementById('style').value,        // "viral"
        pace: document.getElementById('pace').value,          // "fast"
        subtitle_density: document.getElementById('subtitle').value,  // "standard"
        music_preference: document.getElementById('music').value      // "emotional"
    };
    
    // 后端会自动翻译成 DSL
    const response = await fetch('/api/create-project', {
        method: 'POST',
        body: JSON.stringify(formData)
    });
}
```

### 7.2 预览页面调整

```javascript
async function applyAdjustment() {
    const adjustments = {
        pace: document.querySelector('input[name="pace"]:checked').value,
        hook: document.querySelector('input[name="hook"]:checked').value,
        music: document.querySelector('input[name="music"]:checked').value,
        subtitle: document.querySelector('input[name="subtitle"]:checked').value
    };
    
    // 后端会重新生成 DSL
    const response = await fetch(`/api/adjust-project/${currentProjectId}`, {
        method: 'POST',
        body: JSON.stringify(adjustments)
    });
}
```

---

## 总结

这个映射表确保了：

1. **UI 和 DSL 解耦** - UI 可以随时改变，不影响 DSL 结构
2. **配置驱动** - 所有映射关系都在配置文件中，易于维护
3. **AI 友好** - LLM 可以根据 prompt 持续优化
4. **版本可追溯** - 每次调整都生成新版本，可回溯

**关键文件**：
- `config/ui_dsl_mapping.json` - 映射配置
- `app/core/ui_translator.py` - 翻译逻辑
- `app/api/routes_create.py` - 创建项目 API
- `app/api/routes_adjust.py` - 调整项目 API
