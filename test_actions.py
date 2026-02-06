"""测试数据驱动的 Action 设计"""
from app.executor.actions import (
    Action,
    create_timeline,
    append_scene,
    import_srt,
    add_music,
    export_mp4
)

print("=" * 60)
print("数据驱动 Action 设计测试")
print("=" * 60)

# 1. 创建动作
print("\n[1] 创建动作对象")
print("-" * 60)

timeline_action = create_timeline(
    name="AutoCut_Test",
    fps=30.0,
    resolution={"width": 1920, "height": 1080}
)
print(f"✓ {timeline_action}")

scene_action = append_scene(
    scene_id="S0001",
    in_frame=10,
    out_frame=90,
    source="D:/Footage/input.mp4"
)
print(f"✓ {scene_action}")

srt_action = import_srt(path="D:/Subtitles/test.srt")
print(f"✓ {srt_action}")

music_action = add_music(
    path="D:/Music/bgm.mp3",
    volume_db=-18.0
)
print(f"✓ {music_action}")

export_action = export_mp4(
    path="output/final.mp4",
    resolution="1080x1920"
)
print(f"✓ {export_action}")

# 2. 验证数据结构
print("\n[2] 验证数据结构")
print("-" * 60)

assert timeline_action.name == "CreateTimeline"
assert timeline_action.params["name"] == "AutoCut_Test"
assert timeline_action.params["fps"] == 30.0
print("✓ CreateTimeline 数据结构正确")

assert scene_action.name == "AppendScene"
assert scene_action.params["scene_id"] == "S0001"
assert scene_action.params["in_frame"] == 10
assert scene_action.params["out_frame"] == 90
print("✓ AppendScene 数据结构正确")

assert music_action.name == "AddMusic"
assert music_action.params["volume_db"] == -18.0
print("✓ AddMusic 数据结构正确")

# 3. 构建动作队列
print("\n[3] 构建动作队列")
print("-" * 60)

action_queue = [
    create_timeline("Test Timeline", 30.0),
    append_scene("S0001", 0, 120, "input.mp4"),
    append_scene("S0002", 120, 240, "input.mp4"),
    import_srt("subtitles.srt"),
    add_music("bgm.mp3", -18.0),
    export_mp4("output.mp4", "1920x1080")
]

print(f"✓ 动作队列包含 {len(action_queue)} 个动作:")
for i, action in enumerate(action_queue, 1):
    print(f"  {i}. {action}")

# 4. 验证 Action 是数据类
print("\n[4] 验证 Action 是数据类")
print("-" * 60)

from dataclasses import is_dataclass
assert is_dataclass(Action)
print("✓ Action 是 dataclass")

# 可以序列化为字典
action_dict = {
    "name": timeline_action.name,
    "params": timeline_action.params
}
print(f"✓ 可序列化: {action_dict}")

print("\n" + "=" * 60)
print("✓ 所有测试通过！数据驱动设计正常工作")
print("=" * 60)
print("\n设计优势:")
print("- 动作是纯数据对象（dataclass）")
print("- 易于序列化和传输")
print("- Executor 只负责执行，不关心业务逻辑")
print("- 工厂函数提供类型安全的构造")
