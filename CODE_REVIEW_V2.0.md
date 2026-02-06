# AutoCut Director v2.0.0 - 代码审查清单

**日期**: 2026-02-05  
**版本**: v2.0.0  
**审查目的**: 系统性检查所有新功能的实现质量

---

## 📋 审查概览

### 新增功能模块

1. **Visual Analyzer (AI 眼睛)** - v1.8.0
2. **Visual Storyteller (AI 大脑)** - v1.9.0
3. **Process Manager (OS 控制)** - v2.0.0
4. **Smart Bins (智能分类)** - v2.0.0
5. **Full Auto Director API** - v2.0.0

---

## 🔍 审查清单

### 1️⃣ Visual Analyzer (AI 眼睛)

**文件位置**: `app/tools/visual_analyzer.py`

#### 核心功能检查

- [ ] **类初始化**
  - [ ] OpenAI 客户端正确初始化
  - [ ] API Key 验证
  - [ ] Base URL 配置支持
  - [ ] 模型强制使用 `gpt-4o`

- [ ] **截帧功能** (`_extract_frame_base64`)
  - [ ] FFmpeg 命令正确
  - [ ] 临时文件管理（创建/清理）
  - [ ] 超时处理（10秒）
  - [ ] 错误处理完善
  - [ ] Base64 编码正确

- [ ] **视觉分析** (`analyze_scene_visuals`)
  - [ ] 批量处理逻辑
  - [ ] max_scenes 限制生效
  - [ ] 跳过已有视觉数据
  - [ ] 进度输出清晰
  - [ ] 返回更新后的 ScenesJSON

- [ ] **Vision API 调用** (`_call_vision_api`)
  - [ ] System prompt 清晰准确
  - [ ] JSON 格式要求明确
  - [ ] 返回数据验证（Pydantic）
  - [ ] 错误处理完善
  - [ ] Token 优化（detail: low）

#### 数据模型检查

**文件位置**: `app/models/schemas.py`

- [ ] **VisualMetadata 类**
  - [ ] 7 个字段完整
  - [ ] 字段类型正确
  - [ ] 描述清晰
  - [ ] 默认值合理

- [ ] **Scene 类更新**
  - [ ] visual 字段为 Optional
  - [ ] 向后兼容（旧数据不报错）


#### API 接口检查

**文件位置**: `app/api/routes_visual.py`

- [ ] **POST /api/visual/analyze**
  - [ ] 文件上传处理
  - [ ] 参数验证
  - [ ] 错误处理
  - [ ] 返回格式正确

- [ ] **POST /api/visual/analyze-from-job**
  - [ ] Job ID 验证
  - [ ] 文件路径正确
  - [ ] 结果保存

- [ ] **GET /api/visual/stats/{job_id}**
  - [ ] 统计数据准确
  - [ ] 聚类分析正确

#### 测试覆盖

**文件位置**: `test_visual_analyzer.py`

- [ ] **单元测试**
  - [ ] 截帧功能测试
  - [ ] Vision API 测试
  - [ ] 批量分析测试
  - [ ] 错误处理测试

- [ ] **集成测试**
  - [ ] 完整流程测试
  - [ ] 真实视频测试
  - [ ] 性能测试

#### 文档完整性

- [ ] **VISUAL_ANALYSIS_GUIDE.md**
  - [ ] 功能说明清晰
  - [ ] 使用示例完整
  - [ ] API 文档准确
  - [ ] 成本估算合理

- [ ] **VISUAL_ANALYSIS_QUICKREF.md**
  - [ ] 快速参考完整
  - [ ] 代码示例可运行

---

### 2️⃣ Visual Storyteller (AI 大脑)

**文件位置**: `app/core/visual_storyteller.py`

#### 核心功能检查

- [ ] **类初始化**
  - [ ] OpenAI 客户端正确
  - [ ] 模型使用 `gpt-4o`

- [ ] **主入口** (`generate_story_from_visuals`)
  - [ ] 参数验证完整
  - [ ] 流程步骤清晰（4步）
  - [ ] 进度输出友好
  - [ ] 返回数据完整
  - [ ] 错误处理完善

- [ ] **聚类分析** (`_cluster_scenes`)
  - [ ] 按内容分组（人物/风景/物品）
  - [ ] 景别统计
  - [ ] 情绪统计
  - [ ] 高频主体识别
  - [ ] 返回格式正确

- [ ] **视觉摘要** (`_summarize_visuals`)
  - [ ] 格式清晰易读
  - [ ] 信息完整
  - [ ] Token 优化

- [ ] **故事构思** (`_brainstorm_story`)
  - [ ] System prompt 专业
  - [ ] 风格偏好支持
  - [ ] 思考维度完整
  - [ ] 备选方案生成
  - [ ] JSON 格式验证

- [ ] **脚本生成** (`_generate_virtual_transcript`)
  - [ ] 时间分配合理
  - [ ] 文案风格匹配
  - [ ] 情绪递进
  - [ ] TranscriptJSON 封装正确

- [ ] **DSL 生成** (`generate_dsl_from_story`)
  - [ ] 与 LLMDirector 集成
  - [ ] 风格提示传递
  - [ ] 返回格式正确


#### API 接口检查

**文件位置**: `app/api/routes_storyteller.py`

- [ ] **POST /api/storyteller/create-story**
  - [ ] 文件上传处理
  - [ ] 参数验证（duration_target, style_preference）
  - [ ] 错误处理
  - [ ] 返回格式

- [ ] **POST /api/storyteller/create-story-from-job**
  - [ ] Job ID 验证
  - [ ] 文件加载
  - [ ] 结果保存

- [ ] **POST /api/storyteller/generate-dsl-from-story**
  - [ ] Story 数据验证
  - [ ] DSL 生成
  - [ ] 文件保存

- [ ] **GET /api/storyteller/story/{job_id}**
  - [ ] 文件读取
  - [ ] 错误处理

#### 测试覆盖

**文件位置**: `test_visual_storyteller.py`

- [ ] **单元测试**
  - [ ] 聚类分析测试
  - [ ] 故事构思测试
  - [ ] 脚本生成测试
  - [ ] DSL 生成测试

- [ ] **集成测试**
  - [ ] 完整流程测试
  - [ ] 多种风格测试
  - [ ] 边界条件测试

#### 文档完整性

- [ ] **VISUAL_STORYTELLER_GUIDE.md**
  - [ ] 三阶段模型说明
  - [ ] 使用场景清晰
  - [ ] API 文档完整
  - [ ] 示例代码可运行

- [ ] **VISUAL_STORYTELLER_QUICKREF.md**
  - [ ] 快速参考完整
  - [ ] 常见问题解答

---

### 3️⃣ Process Manager (OS 控制)

**文件位置**: `app/tools/process_manager.py`

#### 核心功能检查

- [ ] **类初始化**
  - [ ] 跨平台支持（Windows/macOS/Linux）
  - [ ] 进程名称识别
  - [ ] 可执行文件路径查找

- [ ] **进程检测** (`is_resolve_running`)
  - [ ] psutil 使用正确
  - [ ] 进程名称匹配
  - [ ] 异常处理

- [ ] **进程获取** (`get_resolve_process`)
  - [ ] 返回 psutil.Process 对象
  - [ ] 异常处理

- [ ] **状态获取** (`get_resolve_status`)
  - [ ] 运行状态
  - [ ] PID
  - [ ] 内存使用（MB）
  - [ ] CPU 使用率
  - [ ] 运行时间
  - [ ] 数据格式正确

- [ ] **启动 Resolve** (`start_resolve`)
  - [ ] 检查已运行
  - [ ] 可执行文件验证
  - [ ] 跨平台启动命令
  - [ ] 等待启动完成
  - [ ] 超时处理
  - [ ] 错误处理

- [ ] **停止 Resolve** (`stop_resolve`)
  - [ ] 优雅关闭（terminate）
  - [ ] 强制终止（kill）
  - [ ] 超时处理
  - [ ] 错误处理

- [ ] **重启 Resolve** (`restart_resolve`)
  - [ ] 停止 → 等待 → 启动
  - [ ] 流程完整

- [ ] **确保运行** (`ensure_resolve_running`)
  - [ ] 检测 + 自动启动
  - [ ] auto_start 参数生效

- [ ] **系统资源** (`get_system_resources`)
  - [ ] CPU 使用率
  - [ ] 内存使用率
  - [ ] 可用内存
  - [ ] 磁盘使用率


#### 单例模式

- [ ] **get_process_manager()**
  - [ ] 单例实现正确
  - [ ] 线程安全（如需要）

#### 便捷函数

- [ ] **ensure_resolve_running()**
  - [ ] 调用单例
  - [ ] 参数传递

- [ ] **get_resolve_status()**
  - [ ] 调用单例
  - [ ] 返回正确

#### 测试覆盖

**文件位置**: `test_process_manager.py` (如果存在)

- [ ] **单元测试**
  - [ ] 进程检测测试
  - [ ] 状态获取测试
  - [ ] 系统资源测试

- [ ] **集成测试**
  - [ ] 启动/停止测试（需谨慎）
  - [ ] 跨平台测试

#### 文档完整性

- [ ] **SYSTEM_ARCHITECTURE_V2.md**
  - [ ] Process Manager 说明
  - [ ] 使用场景
  - [ ] API 文档

---

### 4️⃣ Smart Bins (智能分类)

**文件位置**: `app/executor/resolve_adapter.py`

#### 核心功能检查

- [ ] **create_smart_bins() 方法**
  - [ ] 参数验证（scenes_data）
  - [ ] 根 Bin 创建（AutoCut_智能分类）
  - [ ] 子 Bin 创建（4个分类）
  - [ ] 片段分类逻辑
  - [ ] 错误处理
  - [ ] 返回统计数据

- [ ] **分类逻辑**
  - [ ] **按内容分类**
    - [ ] 人物识别
    - [ ] 风景识别
    - [ ] 物品识别
    - [ ] 其他分类
  
  - [ ] **按景别分类**
    - [ ] 特写
    - [ ] 近景
    - [ ] 中景
    - [ ] 全景
    - [ ] 远景
  
  - [ ] **按情绪分类**
    - [ ] 开心
    - [ ] 平静
    - [ ] 紧张
    - [ ] 悲伤
    - [ ] 其他
  
  - [ ] **按质量分类**
    - [ ] 高质量（8-10分）
    - [ ] 中等（5-7分）
    - [ ] 低质量（1-4分）

- [ ] **Bin 结构**
  - [ ] 层级正确
  - [ ] 命名规范
  - [ ] 中文支持

#### 集成检查

- [ ] **与 Visual Analyzer 集成**
  - [ ] visual 字段读取
  - [ ] 缺失数据处理

- [ ] **与 Resolve API 集成**
  - [ ] AddSubFolder 调用
  - [ ] 片段添加
  - [ ] 错误处理

#### 测试覆盖

**文件位置**: `test_resolve_adapter.py`

- [ ] **Smart Bins 测试**
  - [ ] Bin 创建测试
  - [ ] 分类逻辑测试
  - [ ] 统计数据测试

#### 文档完整性

- [ ] **SYSTEM_ARCHITECTURE_V2.md**
  - [ ] Smart Bins 说明
  - [ ] Bin 结构图
  - [ ] 使用场景

---

### 5️⃣ Full Auto Director API

**文件位置**: `app/api/routes_analyze.py`

#### 核心功能检查

- [ ] **POST /api/analyze/story 端点**
  - [ ] 参数验证
    - [ ] video_file (必需)
    - [ ] duration_target (默认30)
    - [ ] style_preference (可选)
    - [ ] platform (默认douyin)
  
  - [ ] **流程步骤**
    - [ ] [1/5] 视频上传 + Job 创建
    - [ ] [2/5] 场景检测
    - [ ] [3/5] 视觉分析（限制10个场景）
    - [ ] [4/5] 故事构思
    - [ ] [5/5] DSL 生成
  
  - [ ] **文件保存**
    - [ ] scenes_with_visual.json
    - [ ] story_result.json
    - [ ] editing_dsl.json
  
  - [ ] **返回数据**
    - [ ] success 状态
    - [ ] job_id
    - [ ] story 摘要
    - [ ] dsl_summary
    - [ ] paths（文件路径）
    - [ ] message

  - [ ] **错误处理**
    - [ ] 文件上传错误
    - [ ] 场景检测错误
    - [ ] 视觉分析错误
    - [ ] 故事构思错误
    - [ ] DSL 生成错误
    - [ ] 完整的 traceback


#### 场景检测实现

- [ ] **临时实现检查**
  - [ ] FFprobe 获取视频信息
  - [ ] FPS 计算正确
  - [ ] 时长计算正确
  - [ ] 简单分段逻辑（每5秒）
  - [ ] Scene 对象创建正确
  - [ ] 时间码格式正确

- [ ] **TODO 标记**
  - [ ] 是否标记了真正的场景检测算法待实现
  - [ ] 是否有替代方案说明

#### 测试覆盖

**文件位置**: `test_full_auto_director.py`

- [ ] **端到端测试**
  - [ ] 完整流程测试
  - [ ] 真实视频测试
  - [ ] 多种风格测试
  - [ ] 错误场景测试

- [ ] **性能测试**
  - [ ] 执行时间测量
  - [ ] 成本估算验证

#### 文档完整性

- [ ] **FULL_AUTO_DIRECTOR_GUIDE.md**
  - [ ] 功能说明完整
  - [ ] 使用场景清晰
  - [ ] API 文档准确
  - [ ] 示例代码可运行
  - [ ] 性能指标准确
  - [ ] 成本估算合理

---

## 🔗 集成检查

### LLM Director 增强

**文件位置**: `app/core/llm_engine.py`

- [ ] **System Prompt 更新**
  - [ ] 视觉理解能力说明
  - [ ] visual 字段使用指导
  - [ ] 画面匹配内容规则
  - [ ] 情绪流控制规则
  - [ ] 景别组接规则
  - [ ] Hook 设计规则

- [ ] **向后兼容**
  - [ ] 无 visual 字段时正常工作
  - [ ] 不破坏现有功能

### 数据流检查

- [ ] **完整数据流**
  ```
  Video → VisualAnalyzer → scenes_with_visual.json
       → VisualStoryteller → story_result.json + transcript.json
       → LLMDirector → editing_dsl.json
       → ResolveAdapter → Smart Bins + Timeline
  ```

- [ ] **文件格式兼容**
  - [ ] scenes.v1.json 格式
  - [ ] transcript.v1.json 格式
  - [ ] editing_dsl.v1.json 格式

### API 路由集成

- [ ] **路由注册**
  - [ ] routes_visual.py 注册
  - [ ] routes_storyteller.py 注册
  - [ ] routes_analyze.py 更新

- [ ] **CORS 配置**
  - [ ] 跨域支持（如需要）

---

## 📝 代码质量检查

### 代码风格

- [ ] **命名规范**
  - [ ] 类名：PascalCase
  - [ ] 函数名：snake_case
  - [ ] 常量：UPPER_CASE
  - [ ] 私有方法：_leading_underscore

- [ ] **类型注解**
  - [ ] 函数参数类型
  - [ ] 返回值类型
  - [ ] Optional 使用正确

- [ ] **文档字符串**
  - [ ] 类文档字符串
  - [ ] 方法文档字符串
  - [ ] 参数说明
  - [ ] 返回值说明
  - [ ] 示例代码

### 错误处理

- [ ] **异常捕获**
  - [ ] 具体异常类型
  - [ ] 错误信息清晰
  - [ ] 日志记录
  - [ ] 用户友好提示

- [ ] **资源清理**
  - [ ] 临时文件清理
  - [ ] 文件句柄关闭
  - [ ] 进程清理

### 性能优化

- [ ] **Token 优化**
  - [ ] Vision API 使用 detail: low
  - [ ] 视觉摘要简化
  - [ ] max_scenes 限制

- [ ] **并发处理**
  - [ ] 是否需要异步处理
  - [ ] 批量处理优化

### 安全性

- [ ] **输入验证**
  - [ ] 文件类型验证
  - [ ] 文件大小限制
  - [ ] 路径遍历防护

- [ ] **API Key 保护**
  - [ ] 环境变量使用
  - [ ] 不在日志中泄露

---

## 🧪 测试检查

### 测试文件清单

- [ ] `test_visual_analyzer.py`
- [ ] `test_visual_storyteller.py`
- [ ] `test_full_auto_director.py`
- [ ] `test_process_manager.py` (如果存在)
- [ ] `test_resolve_adapter.py` (Smart Bins 部分)

### 测试覆盖率

- [ ] **单元测试覆盖**
  - [ ] 核心函数测试
  - [ ] 边界条件测试
  - [ ] 错误场景测试

- [ ] **集成测试覆盖**
  - [ ] 端到端流程测试
  - [ ] 跨模块集成测试

- [ ] **性能测试**
  - [ ] 执行时间测量
  - [ ] 资源使用监控


---

## 📚 文档检查

### 核心文档

- [ ] **SYSTEM_ARCHITECTURE_V2.md**
  - [ ] 系统概述完整
  - [ ] 架构图清晰
  - [ ] 两种模式说明
  - [ ] 模块详解完整
  - [ ] API 接口文档
  - [ ] 数据协议说明
  - [ ] 性能指标准确
  - [ ] 版本历史完整

- [ ] **FULL_AUTO_DIRECTOR_GUIDE.md**
  - [ ] 功能说明
  - [ ] 使用指南
  - [ ] API 文档
  - [ ] 示例代码
  - [ ] 最佳实践

- [ ] **VISUAL_ANALYSIS_GUIDE.md**
  - [ ] 功能说明
  - [ ] 使用指南
  - [ ] API 文档
  - [ ] 成本估算

- [ ] **VISUAL_STORYTELLER_GUIDE.md**
  - [ ] 三阶段模型
  - [ ] 使用场景
  - [ ] API 文档
  - [ ] 示例代码

### 快速参考

- [ ] **VISUAL_ANALYSIS_QUICKREF.md**
  - [ ] 快速上手
  - [ ] 代码示例
  - [ ] 常见问题

- [ ] **VISUAL_STORYTELLER_QUICKREF.md**
  - [ ] 快速上手
  - [ ] 代码示例
  - [ ] 常见问题

### 更新文档

- [ ] **VISUAL_ANALYSIS_UPDATE.md**
  - [ ] 更新说明
  - [ ] 变更记录

- [ ] **VISUAL_STORYTELLER_UPDATE.md**
  - [ ] 更新说明
  - [ ] 变更记录

### 主文档更新

- [ ] **README.md**
  - [ ] v2.0.0 功能说明
  - [ ] 快速开始更新
  - [ ] 文档链接更新

- [ ] **CHANGELOG.md**
  - [ ] v2.0.0 变更记录
  - [ ] v1.9.0 变更记录
  - [ ] v1.8.0 变更记录

---

## 🎯 功能验证

### Visual Analyzer 验证

```bash
# 1. 独立测试
cd autocut-director
python -m app.tools.visual_analyzer test_video.mp4 scenes.json

# 2. API 测试
curl -X POST http://localhost:8000/api/visual/analyze \
  -F "video_file=@test_video.mp4" \
  -F "scenes_file=@scenes.json"

# 3. 单元测试
python test_visual_analyzer.py
```

- [ ] 独立测试通过
- [ ] API 测试通过
- [ ] 单元测试通过

### Visual Storyteller 验证

```bash
# 1. API 测试
curl -X POST http://localhost:8000/api/storyteller/create-story \
  -F "scenes_file=@scenes_with_visual.json" \
  -F "duration_target=30" \
  -F "style_preference=情感叙事"

# 2. 单元测试
python test_visual_storyteller.py
```

- [ ] API 测试通过
- [ ] 单元测试通过
- [ ] 多种风格测试

### Process Manager 验证

```bash
# 1. 独立测试
cd autocut-director
python -m app.tools.process_manager

# 2. 集成测试
python test_process_manager.py
```

- [ ] 独立测试通过
- [ ] 进程检测正确
- [ ] 启动/停止功能正常（谨慎测试）

### Smart Bins 验证

```bash
# 1. 集成测试
python test_resolve_adapter.py

# 2. 手动验证
# - 打开 DaVinci Resolve
# - 运行 Smart Bins 创建
# - 检查 Media Pool 结构
```

- [ ] Bin 结构正确
- [ ] 分类逻辑正确
- [ ] 片段添加成功

### Full Auto Director 验证

```bash
# 1. 端到端测试
curl -X POST http://localhost:8000/api/analyze/story \
  -F "video_file=@test_video.mp4" \
  -F "duration_target=30" \
  -F "style_preference=高燃踩点"

# 2. 单元测试
python test_full_auto_director.py
```

- [ ] 完整流程通过
- [ ] 文件生成正确
- [ ] 返回数据完整
- [ ] 性能符合预期

---

## 🐛 已知问题检查

### 临时实现

- [ ] **场景检测**
  - [ ] 当前使用简单分段（每5秒）
  - [ ] TODO: 实现真正的场景检测算法
  - [ ] 是否影响功能演示？

### 性能问题

- [ ] **视觉分析成本**
  - [ ] 是否有 max_scenes 限制？
  - [ ] 是否使用 detail: low？
  - [ ] 成本估算是否准确？

### 兼容性问题

- [ ] **跨平台支持**
  - [ ] Windows 测试
  - [ ] macOS 测试（如可能）
  - [ ] Linux 测试（如可能）

- [ ] **Resolve 版本**
  - [ ] 支持的最低版本
  - [ ] API 兼容性

### 边界条件

- [ ] **空数据处理**
  - [ ] 无视觉数据场景
  - [ ] 空场景列表
  - [ ] 无效视频文件

- [ ] **大文件处理**
  - [ ] 长视频处理
  - [ ] 大量场景处理
  - [ ] 内存使用

---

## ✅ 审查结果

### 通过标准

- [ ] 所有核心功能正常工作
- [ ] 测试覆盖率 > 80%
- [ ] 文档完整准确
- [ ] 无严重 Bug
- [ ] 性能符合预期
- [ ] 代码质量良好

### 需要改进

**高优先级**:
- [ ] 实现真正的场景检测算法
- [ ] 补充缺失的测试
- [ ] 修复已知 Bug

**中优先级**:
- [ ] 性能优化
- [ ] 文档补充
- [ ] 代码重构

**低优先级**:
- [ ] 代码风格统一
- [ ] 注释补充
- [ ] 示例代码

---

## 📊 审查统计

### 代码统计

- **新增文件**: 
  - `app/tools/visual_analyzer.py` (~250 行)
  - `app/core/visual_storyteller.py` (~350 行)
  - `app/tools/process_manager.py` (~300 行)
  - `app/api/routes_visual.py` (~150 行)
  - `app/api/routes_storyteller.py` (~150 行)
  - `app/api/routes_analyze.py` (新增 story 端点, ~150 行)

- **修改文件**:
  - `app/models/schemas.py` (新增 VisualMetadata)
  - `app/core/llm_engine.py` (增强 system prompt)
  - `app/executor/resolve_adapter.py` (新增 create_smart_bins)

- **总新增代码**: ~1500 行
- **总修改代码**: ~200 行

### 文档统计

- **新增文档**: 8 个
- **更新文档**: 3 个
- **总文档行数**: ~2000 行

### 测试统计

- **新增测试**: 3 个
- **测试用例**: ~50 个
- **测试覆盖率**: 预估 85%

---

## 🎓 审查建议

### 代码审查重点

1. **Visual Analyzer**
   - 重点检查 FFmpeg 命令和临时文件管理
   - 验证 Vision API 调用和错误处理
   - 确认 Token 优化措施

2. **Visual Storyteller**
   - 重点检查三阶段思考模型实现
   - 验证聚类分析逻辑
   - 确认 LLM Prompt 质量

3. **Process Manager**
   - 重点检查跨平台兼容性
   - 验证进程管理安全性
   - 确认资源清理

4. **Smart Bins**
   - 重点检查分类逻辑
   - 验证 Resolve API 调用
   - 确认 Bin 结构

5. **Full Auto Director**
   - 重点检查完整流程
   - 验证错误处理
   - 确认性能指标

### 测试建议

1. **优先测试**
   - 端到端流程测试
   - 真实视频测试
   - 错误场景测试

2. **性能测试**
   - 执行时间测量
   - 成本估算验证
   - 资源使用监控

3. **兼容性测试**
   - 跨平台测试
   - Resolve 版本测试
   - 数据格式兼容测试

### 文档审查建议

1. **完整性检查**
   - 所有新功能有文档
   - 所有 API 有说明
   - 所有示例可运行

2. **准确性检查**
   - 代码示例正确
   - 参数说明准确
   - 性能指标真实

3. **可读性检查**
   - 结构清晰
   - 语言流畅
   - 格式统一

---

## 📝 审查记录

**审查人**: _____________  
**审查日期**: _____________  
**审查版本**: v2.0.0  
**审查结果**: ⬜ 通过 / ⬜ 需改进 / ⬜ 不通过  

**主要发现**:
1. 
2. 
3. 

**改进建议**:
1. 
2. 
3. 

**签名**: _____________

---

**文档版本**: v1.0  
**创建日期**: 2026-02-05  
**最后更新**: 2026-02-05
