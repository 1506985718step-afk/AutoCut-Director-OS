# 音频音量修复总结

## ✅ 修复完成

修复了 `resolve_adapter.py` 中 `add_audio()` 方法无法设置音量的问题。

---

## 🔧 核心修复

### 问题
- `AppendToTimeline()` 返回 `TimelineItem` 列表，但原代码没有使用
- 无法调用 `SetProperty()` 设置音量

### 解决方案
```python
# 正确获取 TimelineItem 列表
appended_items = self.media_pool.AppendToTimeline(audio_clips)

# 设置音量（多版本兼容）
for item in appended_items:
    # 尝试 AudioLevel (Resolve 19+)
    success = item.SetProperty("AudioLevel", volume)
    
    # 尝试 Volume (Resolve 18)
    if not success:
        success = item.SetProperty("Volume", volume)
    
    # 尝试 AudioVolume (早期版本)
    if not success:
        success = item.SetProperty("AudioVolume", volume)
    
    # 优雅降级
    if not success:
        print("⚠️ 请手动调整音量")
```

---

## 📁 修改文件

1. **app/executor/resolve_adapter.py** - 修复 `add_audio()` 方法
2. **test_audio_volume.py** - 新增测试脚本
3. **AUDIO_VOLUME_FIX.md** - 完整修复文档
4. **CHANGELOG.md** - 更新日志

---

## 🧪 测试

```bash
cd autocut-director
python test_audio_volume.py
```

**测试内容**:
- 默认音量 (1.0)
- 降低音量 (0.5)
- 更低音量 (0.2)

---

## 🎯 使用示例

```python
# 添加背景音乐，音量 20%
adapter.add_audio("bgm.mp3", volume=0.2)

# 或使用 dB 格式（在 Action 中）
action = AddAudioAction(
    audio_path="bgm.mp3",
    volume_db=-18  # ≈ 12.6% 线性音量
)
```

---

## 📊 音量参考

| 用途 | dB | 线性 |
|------|-----|------|
| 原始 | 0 | 1.0 |
| 背景音乐 | -18 | 0.126 |
| 环境音 | -24 | 0.063 |

---

**状态**: ✅ 已修复  
**版本**: v1.2.1  
**日期**: 2025-02-05

