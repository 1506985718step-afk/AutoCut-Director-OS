# Bug Report and Fixes

**日期**: 2026-02-06  
**检查范围**: 全项目代码深度检查  
**状态**: 发现 3 类问题，提供修复方案

---

## 🐛 发现的问题

### 1. 裸 except 语句（代码质量问题）⚠️

**问题描述**：
多处使用裸 `except:` 语句，会捕获所有异常（包括 KeyboardInterrupt、SystemExit），可能导致难以调试。

**影响范围**：
- `app/core/runtime_monitor.py` - 2 处
- `app/core/runtime_profile.py` - 6 处
- `app/core/orchestrator.py` - 1 处
- `app/tools/modality_analyzer.py` - 4 处
- `app/tools/audio_matcher.py` - 2 处
- `app/tools/visual_analyzer_local.py` - 3 处
- `app/tools/visual_analyzer_factory.py` - 4 处
- `app/executor/resolve_adapter.py` - 7 处

**严重程度**: 中等（不会导致崩溃，但影响调试）

**修复方案**：
```python
# 不好的写法
try:
    something()
except:
    pass

# 好的写法
try:
    something()
except Exception as e:
    # 可选：记录日志
    # print(f"Warning: {e}")
    pass
```

**建议修复的关键位置**：

1. **runtime_monitor.py** (第 121, 130 行)
```python
# 修复前
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    # ...
except:
    pass

# 修复后
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    # ...
except (ImportError, Exception) as e:
    # GPUtil 未安装或获取失败
    pass
```

2. **runtime_profile.py** (第 85, 107, 135, 143, 181, 183 行)
```python
# 修复前
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    # ...
except:
    pass

# 修复后
try:
    import GPUtil
    gpus = GPUtil.getGPUs()
    # ...
except (ImportError, AttributeError, Exception):
    pass
```

---

### 2. 潜在的空指针问题 ⚠️

**问题描述**：
`runtime_monitor.py` 中 `should_use_cpu_for_vision()` 方法可能在 `current` 为 `None` 时出错。

**位置**: `app/core/runtime_monitor.py:247-260`

**代码**:
```python
def should_use_cpu_for_vision(self) -> bool:
    """判断是否应该使用 CPU 模式进行视觉分析"""
    current = self.get_current_metrics()
    
    if not current:  # ✓ 有检查
        return False
    
    # GPU 显存 > 70% → CPU 模式
    if current.gpu_vram_used_percent > 70:  # ✓ 安全
        return True
    
    # Resolve 繁忙 → CPU 模式
    if current.resolve_busy:  # ✓ 安全
        return True
    
    # 内存 < 4GB → CPU 模式
    if current.memory_available_gb < 4.0:  # ✓ 安全
        return True
    
    return False
```

**状态**: ✅ 已正确处理，无需修复

---

### 3. 模态分析器中的异常处理 ⚠️

**问题描述**：
`modality_analyzer.py` 中 `_extract_audio_features()` 方法在 ffmpeg 失败时返回默认值，但可能导致误判。

**位置**: `app/tools/modality_analyzer.py:140-170`

**当前行为**:
```python
except Exception as e:
    print(f"⚠️  音频特征提取失败: {e}")
    # 返回默认值
    return {
        "has_audio": False,
        "avg_volume_db": -100,
        "volume_variance": 0,
        "silence_duration": 0,
        "speech_segments": 0,
        "duration": 0,
        "silence_ratio": 1.0,
        "speech_ratio": 0.0,
        "music_ratio": 0.0
    }
```

**潜在问题**：
- 如果 ffmpeg 不存在，会返回"无音频"
- 如果文件损坏，会返回"无音频"
- 可能导致错误的模态判断

**修复方案**：
```python
except FileNotFoundError:
    print(f"⚠️  文件不存在: {source_path}")
    raise  # 向上抛出，让调用者处理
except subprocess.TimeoutExpired:
    print(f"⚠️  音频分析超时")
    # 返回默认值（合理）
    return {...}
except Exception as e:
    print(f"⚠️  音频特征提取失败: {e}")
    # 返回默认值
    return {...}
```

---

### 4. 音频匹配器中的时间戳解析 ⚠️

**问题描述**：
`audio_matcher.py` 中 `_get_creation_time()` 方法在解析 ISO 8601 时间时可能失败。

**位置**: `app/tools/audio_matcher.py:220-250`

**当前代码**:
```python
try:
    # 解析 ISO 8601 时间
    dt = datetime.fromisoformat(creation_time_str.replace("Z", "+00:00"))
    return dt.timestamp()
except:
    pass
```

**潜在问题**：
- 不同格式的时间字符串可能解析失败
- 裸 except 会隐藏真正的错误

**修复方案**：
```python
try:
    # 解析 ISO 8601 时间
    dt = datetime.fromisoformat(creation_time_str.replace("Z", "+00:00"))
    return dt.timestamp()
except (ValueError, AttributeError) as e:
    # 时间格式不正确
    pass
```

---

## ✅ 已正确处理的部分

### 1. Runtime Monitor 的空值检查
```python
def get_status(self) -> Dict[str, Any]:
    current = self.get_current_metrics()
    
    if not current:  # ✓ 正确检查
        return {
            "running": self._running,
            "degraded": self._degraded,
            "degradation_reason": self._degradation_reason,
            "metrics": None
        }
```

### 2. Visual Analyzer Factory 的异常处理
```python
try:
    from ..core.execution_policy import get_execution_policy
    policy = get_execution_policy()
    # ...
except Exception as e:
    print(f"⚠️  无法获取执行策略，使用默认配置: {e}")
```

### 3. Orchestrator 的资源锁检查
```python
def can_enter_state(self, job_id: str, target_state: JobState) -> tuple[bool, str]:
    # 检查状态转换是否合法
    current_state = self.current_jobs.get(job_id)
    if current_state and not StateTransition.can_transition(current_state, target_state):
        return False, f"不允许从 {current_state.value} 转换到 {target_state.value}"
```

---

## 🔧 修复优先级

### 高优先级（建议立即修复）
1. ❌ 无

### 中优先级（建议在下次迭代修复）
1. ⚠️  裸 except 语句 → 改为 `except Exception:`
2. ⚠️  模态分析器异常处理 → 区分不同异常类型
3. ⚠️  音频匹配器时间解析 → 指定异常类型

### 低优先级（代码质量改进）
1. 💡 添加更多日志记录
2. 💡 添加类型检查（mypy）
3. 💡 添加单元测试覆盖率检查

---

## 📝 修复脚本

### 批量修复裸 except 语句

```python
# 创建一个脚本来批量替换
import re
from pathlib import Path

def fix_bare_except(file_path):
    """修复裸 except 语句"""
    content = file_path.read_text(encoding='utf-8')
    
    # 替换 except: 为 except Exception:
    # 但保留 except Exception: 和 except SomeError:
    pattern = r'(\s+)except:\s*$'
    replacement = r'\1except Exception:\n'
    
    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if new_content != content:
        file_path.write_text(new_content, encoding='utf-8')
        return True
    return False

# 运行修复
files_to_fix = [
    "app/core/runtime_monitor.py",
    "app/core/runtime_profile.py",
    "app/core/orchestrator.py",
    "app/tools/modality_analyzer.py",
    "app/tools/audio_matcher.py",
    "app/tools/visual_analyzer_local.py",
    "app/tools/visual_analyzer_factory.py",
]

for file in files_to_fix:
    path = Path(file)
    if path.exists():
        if fix_bare_except(path):
            print(f"✓ 修复: {file}")
```

---

## 🧪 测试建议

### 1. 添加异常测试
```python
def test_modality_analyzer_with_invalid_file():
    """测试无效文件的处理"""
    analyzer = ModalityAnalyzer()
    
    # 测试不存在的文件
    with pytest.raises(FileNotFoundError):
        analyzer.analyze("nonexistent.mp4")
    
    # 测试损坏的文件
    result = analyzer.analyze("corrupted.mp4")
    assert result.recommended_mode == "SKIP"
```

### 2. 添加边界测试
```python
def test_runtime_monitor_empty_metrics():
    """测试空指标的处理"""
    monitor = RuntimeMonitor()
    
    # 未启动时
    assert monitor.should_use_cpu_for_vision() == False
    
    # 获取状态
    status = monitor.get_status()
    assert status["metrics"] is None
```

---

## 📊 代码质量评分

| 模块 | 评分 | 主要问题 |
|------|------|---------|
| runtime_profile.py | 8/10 | 裸 except 语句 |
| runtime_monitor.py | 9/10 | 裸 except 语句 |
| execution_policy.py | 10/10 | 无问题 |
| orchestrator.py | 9/10 | 1 处裸 except |
| modality_analyzer.py | 8/10 | 异常处理可改进 |
| audio_matcher.py | 8/10 | 时间解析异常处理 |
| smart_pipeline.py | 10/10 | 无问题 |
| visual_analyzer_factory.py | 9/10 | 裸 except 语句 |

**总体评分**: 8.8/10 ✅

---

## 🎯 总结

### 发现的问题
- ⚠️  裸 except 语句：约 30 处（代码质量问题）
- ⚠️  异常处理可改进：3 处（功能问题）
- ✅ 空指针检查：已正确处理
- ✅ 类型注解：正确使用

### 严重程度
- 🔴 严重 BUG：0 个
- 🟡 中等问题：3 个
- 🟢 轻微问题：30 个

### 建议
1. **立即修复**：无严重 BUG
2. **下次迭代**：修复裸 except 语句
3. **长期改进**：添加类型检查和测试覆盖率

### 结论
✅ **项目代码质量良好，无严重 BUG**

主要问题是代码风格（裸 except），不影响功能运行。建议在下次迭代中统一修复。

---

## 📞 如何应用修复

### 手动修复（推荐）
逐个文件检查并修复，确保理解每个异常的含义。

### 自动修复（快速）
运行上面的修复脚本，批量替换裸 except。

### 测试验证
```bash
# 运行所有测试
python test_runtime_profile.py
python test_modality_analyzer.py
python test_orchestrator.py

# 确保所有测试通过
```

---

**代码质量检查完成！** ✅
