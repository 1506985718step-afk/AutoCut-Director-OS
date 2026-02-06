# AutoCut Director - 产品级设计完成

## 📋 完成清单

### ✅ 1. UI Flow 设计文档
- **文件**: `docs/UI_FLOW.md`
- **内容**: 4 个一级页面的完整设计
- **原则**: 用户是"导演"，系统是"剪辑助理"

### ✅ 2. DSL ↔ UI 映射表
- **文件**: `docs/DSL_UI_MAPPING.md`
- **内容**: 完整的 UI 控件 → DSL 字段映射
- **特点**: 配置驱动，易于维护和扩展

### ✅ 3. UI → API 时序图
- **文件**: `docs/UI_API_SEQUENCE.md`
- **内容**: 4 个核心场景的完整 API 调用流程
- **场景**: 创建、调整、导出、历史

### ✅ 4. 映射配置文件
- **文件**: `config/ui_dsl_mapping.json`
- **内容**: 所有映射关系的 JSON 配置
- **优势**: 不写死在代码里，AI 可持续学习

### ✅ 5. UI 翻译器实现
- **文件**: `app/core/ui_translator.py`
- **功能**: 将 UI 意图翻译成 DSL 和 LLM Prompt
- **特点**: 单例模式，配置驱动

---

## 🎯 核心设计原则

### 1. 用户视角
- ✅ 用户永远不接触 job_id / endpoint / DSL
- ✅ 用户只表达意图，系统负责实现
- ✅ 技术细节完全隐藏

### 2. 意图优先
- ✅ "节奏更快" 而不是 "trim_frames 收紧"
- ✅ "Hook 更狠" 而不是 "scene 排序"
- ✅ "换一首音乐" 而不是 "music.path 改变"

### 3. 配置驱动
- ✅ 所有映射关系在配置文件中
- ✅ UI 和 DSL 解耦
- ✅ 易于维护和扩展

### 4. 版本管理
- ✅ 每次调整生成新版本
- ✅ 可回溯、可对比
- ✅ 不会丢失之前的工作

---

## 📁 文件结构

```
autocut-director/
├── docs/
│   ├── UI_FLOW.md                  # UI 流程设计
│   ├── DSL_UI_MAPPING.md           # DSL ↔ UI 映射表
│   ├── UI_API_SEQUENCE.md          # UI → API 时序图
│   └── PRODUCT_LEVEL_DESIGN.md     # 本文档
│
├── config/
│   └── ui_dsl_mapping.json         # 映射配置文件
│
├── app/
│   ├── core/
│   │   └── ui_translator.py        # UI 翻译器
│   │
│   └── api/
│       ├── routes_create.py        # 创建项目 API（待实现）
│       ├── routes_adjust.py        # 调整项目 API（待实现）
│       └── routes_export.py        # 导出项目 API（待实现）
│
└── app/static/
    ├── app.html                    # 用户 UI（已实现）
    ├── style.css                   # 样式（已实现）
    └── app.js                      # 前端逻辑（待更新）
```

---

## 🔄 UI → DSL 映射示例

### 示例 1：创建项目

**用户操作**：
- 平台：抖音
- 风格：爆款短视频
- 节奏：快
- 字幕：标准
- 音乐：情绪

**翻译结果**：

```python
# 1. 平台 → DSL meta
meta = {
    "target_platform": "douyin",
    "aspect_ratio": "9:16",
    "resolution": "1080x1920",
    "max_duration": 60
}

# 2. 风格 + 节奏 + 字幕 + 音乐 → LLM Prompt
prompt = """
抖音爆款风格：节奏快、文字多、强调关键词、开头3秒Hook、删除所有废话和停顿、每3-5秒切换画面或文字

目标平台：douyin
视频比例：9:16
最大时长：60秒

剪辑节奏：激进剪辑，只保留核心内容，每3-5秒切换画面。删除所有停顿、口误、重复内容。

字幕要求：
- 密度：standard
- 关键词高亮：是
- 文字叠加：否

音乐要求：
- 使用背景音乐
- 情绪：emotional
- 能量：medium
"""

# 3. 调用 LLM 生成 DSL
dsl = llm_engine.generate_dsl(scenes, transcript, prompt)
```

### 示例 2：调整项目

**用户操作**：
- 节奏：更快
- Hook：更狠
- 音乐：保持
- 字幕：保持

**翻译结果**：

```python
# 1. 获取原始 prompt
original_prompt = "..."

# 2. 追加调整说明
adjustment_prompt = """
--- 用户调整 ---
用户反馈：节奏太慢，请加快剪辑节奏，更激进地删除停顿和重复内容。每个场景保持3-5秒。
用户反馈：开头Hook不够强，请选择最有冲击力、最吸引人的场景作为开头。可以使用数字、对比、悬念等手法。
"""

# 3. 重新调用 LLM
new_dsl = llm_engine.generate_dsl(
    scenes, 
    transcript, 
    original_prompt + adjustment_prompt
)

# 4. 创建新版本
version_metadata = {
    "version": 2,
    "parent_version": 1,
    "created_at": "2026-02-05T14:35:00Z",
    "user_adjustments": {
        "pace": "faster",
        "hook": "stronger"
    }
}
```

---

## 🚀 下一步实现

### 高优先级

#### 1. 实现产品级 API
- [ ] `POST /api/create-project` - 创建项目
- [ ] `GET /api/projects/{id}/status` - 获取状态
- [ ] `POST /api/projects/{id}/adjust` - 调整项目
- [ ] `POST /api/projects/{id}/export` - 导出成片
- [ ] `GET /api/projects/{id}/versions` - 获取版本列表

#### 2. 更新前端 UI
- [ ] 使用新的 API 端点
- [ ] 实现轮询进度
- [ ] 实现版本管理
- [ ] 隐藏所有技术细节

#### 3. 集成 UI 翻译器
- [ ] 在 API 中使用 `UITranslator`
- [ ] 测试所有映射关系
- [ ] 验证 LLM prompt 生成

### 中优先级

#### 4. 版本管理系统
- [ ] 实现版本存储
- [ ] 实现版本切换
- [ ] 实现版本对比
- [ ] 实现版本删除

#### 5. 优化用户体验
- [ ] 添加加载动画
- [ ] 优化错误提示
- [ ] 添加进度实时更新（WebSocket）
- [ ] 添加预览视频缓存

### 低优先级

#### 6. 高级功能
- [ ] 批量处理
- [ ] 模板管理
- [ ] 用户账号系统
- [ ] 云端存储

---

## 📊 API 端点对比

### 旧 API（技术视角）

| 端点 | 说明 | 用户可见 |
|------|------|---------|
| `/api/ingest/upload` | 上传视频 | ❌ |
| `/api/ingest/extract-audio` | 提取音频 | ❌ |
| `/api/llm/generate-dsl` | 生成 DSL | ❌ |
| `/api/execute/execute` | 执行剪辑 | ❌ |
| `/api/jobs/{id}` | 获取 job | ❌ |

### 新 API（产品视角）

| 端点 | 说明 | 用户可见 |
|------|------|---------|
| `/api/create-project` | 创建项目 | ✅ |
| `/api/projects/{id}/status` | 获取状态 | ✅ |
| `/api/projects/{id}/adjust` | 调整项目 | ✅ |
| `/api/projects/{id}/export` | 导出成片 | ✅ |
| `/api/projects/{id}/versions` | 版本列表 | ✅ |

---

## 🎓 使用示例

### Python 后端

```python
from app.core.ui_translator import get_translator

# 获取翻译器
translator = get_translator()

# 翻译平台选择
meta = translator.translate_platform("douyin")
# → {"target_platform": "douyin", "aspect_ratio": "9:16", ...}

# 构建初始 prompt
prompt = translator.build_initial_prompt(
    platform="douyin",
    style="viral",
    pace="fast",
    subtitle_density="standard",
    music_preference="emotional"
)

# 构建调整 prompt
adjustments = {"pace": "faster", "hook": "stronger"}
new_prompt = translator.build_adjustment_prompt(prompt, adjustments)

# 提取摘要
summary = translator.extract_summary_from_dsl(dsl)
# → {"hook": "场景 3", "pace": "快", "music": "情绪型（120 BPM）", ...}
```

### JavaScript 前端

```javascript
// 创建项目
const response = await fetch('/api/create-project', {
    method: 'POST',
    body: formData
});

// 轮询进度
const status = await fetch(`/api/projects/${projectId}/status`);

// 调整项目
const result = await fetch(`/api/projects/${projectId}/adjust`, {
    method: 'POST',
    body: JSON.stringify({adjustments})
});
```

---

## ✅ 验收标准

### 1. 用户体验
- [ ] 用户看不到任何技术术语
- [ ] 用户只需表达意图
- [ ] 用户可以轻松回溯版本

### 2. 技术实现
- [ ] 所有映射关系在配置文件中
- [ ] UI 和 DSL 完全解耦
- [ ] 代码易于维护和扩展

### 3. 功能完整性
- [ ] 支持 4 个平台
- [ ] 支持 4 种风格
- [ ] 支持所有调整选项
- [ ] 支持版本管理

---

## 📝 总结

本次设计完成了从技术视角到产品视角的完整转变：

1. **UI Flow** - 定义了 4 个一级页面的完整流程
2. **DSL Mapping** - 建立了 UI 控件到 DSL 的完整映射
3. **API Sequence** - 设计了前后端交互的完整时序
4. **Config File** - 创建了配置驱动的映射文件
5. **Translator** - 实现了 UI 意图翻译器

**关键成果**：
- ✅ 用户永远不接触技术细节
- ✅ 系统可以持续进化
- ✅ AI 可以持续学习
- ✅ 代码易于维护

**下一步**：
- 实现产品级 API
- 更新前端 UI
- 端到端测试

---

**版本**: v1.5.0  
**日期**: 2026-02-05  
**状态**: 设计完成，待实现
