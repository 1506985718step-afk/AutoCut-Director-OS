"""完整工作流示例：EDL -> scenes.json -> DSL -> Actions -> Resolve"""
import json
from pathlib import Path

# 导入所有需要的模块
from app.tools.scene_from_edl import parse_edl_to_scenes
from app.models.schemas import EditingDSL, ScenesJSON, DSLValidator
from app.executor.actions import (
    create_timeline,
    append_scene,
    add_music,
    export_mp4
)
from app.executor.runner import run_actions

print("=" * 70)
print("AutoCut Director 完整工作流示例")
print("=" * 70)

# ============================================================================
# Step 1: 解析 EDL -> scenes.json
# ============================================================================
print("\n[Step 1] 解析 EDL -> scenes.json")
print("-" * 70)

scenes_dict = parse_edl_to_scenes(
    edl_path="examples/test.edl",
    fps=30,
    primary_clip_path="D:/Footage/input.mp4"
)

print(f"✓ 解析成功，生成 {len(scenes_dict['scenes'])} 个场景")
for scene in scenes_dict['scenes']:
    print(f"  {scene['scene_id']}: {scene['start_tc']} -> {scene['end_tc']}")

# 保存 scenes.json
scenes_path = Path("output_scenes.json")
with open(scenes_path, "w", encoding="utf-8") as f:
    json.dump(scenes_dict, f, indent=2, ensure_ascii=False)
print(f"✓ 已保存: {scenes_path}")

# ============================================================================
# Step 2: 创建 editing_dsl.json（模拟 AI 生成）
# ============================================================================
print("\n[Step 2] 创建 editing_dsl.json（模拟 AI 生成）")
print("-" * 70)

dsl_dict = {
    "meta": {
        "schema": "editing_dsl.v1",
        "target": "douyin",
        "aspect": "9:16"
    },
    "editing_plan": {
        "timeline": [
            {
                "order": 1,
                "scene_id": "S0001",
                "trim_frames": [10, 100],
                "purpose": "hook",
                "overlay_text": "开场"
            },
            {
                "order": 2,
                "scene_id": "S0002",
                "trim_frames": [130, 220],
                "purpose": "content",
                "overlay_text": "内容"
            }
        ],
        "subtitles": {
            "mode": "from_transcript"
        },
        "music": {
            "track_path": "D:/Music/bgm.mp3",
            "volume_db": -18
        }
    },
    "export": {
        "resolution": "1080x1920",
        "format": "mp4"
    }
}

# 保存 DSL
dsl_path = Path("output_dsl.json")
with open(dsl_path, "w", encoding="utf-8") as f:
    json.dump(dsl_dict, f, indent=2, ensure_ascii=False)
print(f"✓ 已保存: {dsl_path}")

# ============================================================================
# Step 3: 硬规则验证（防 AI 幻觉）
# ============================================================================
print("\n[Step 3] 硬规则验证（防 AI 幻觉）")
print("-" * 70)

scenes = ScenesJSON(**scenes_dict)
dsl = EditingDSL(**dsl_dict)

is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)

if is_valid:
    print("✓ 验证通过！DSL 可以安全执行")
else:
    print("✗ 验证失败！发现以下问题：")
    for error in errors:
        print(f"  - {error}")
    exit(1)

# ============================================================================
# Step 4: DSL -> Actions 转换
# ============================================================================
print("\n[Step 4] DSL -> Actions 转换")
print("-" * 70)

# 构建 scene_id -> Scene 映射
scene_map = {scene.scene_id: scene for scene in scenes.scenes}

actions = []

# 1. 创建时间线
width, height = map(int, dsl.export.resolution.split('x'))
actions.append(create_timeline(
    name=f"AutoCut_{dsl.meta.target}",
    fps=scenes.meta.fps,
    resolution={"width": width, "height": height}
))

# 2. 添加场景片段
sorted_timeline = sorted(dsl.editing_plan.timeline, key=lambda x: x.order)
for item in sorted_timeline:
    scene = scene_map[item.scene_id]
    trim_start, trim_end = item.trim_frames
    
    actions.append(append_scene(
        scene_id=item.scene_id,
        in_frame=trim_start,
        out_frame=trim_end,
        source=scenes.media.primary_clip_path
    ))

# 3. 添加背景音乐
actions.append(add_music(
    path=dsl.editing_plan.music.track_path,
    volume_db=dsl.editing_plan.music.volume_db
))

# 4. 导出
actions.append(export_mp4(
    path=f"output/autocut_{dsl.meta.target}.{dsl.export.format}",
    resolution=dsl.export.resolution
))

print(f"✓ 生成了 {len(actions)} 个动作:")
for i, action in enumerate(actions, 1):
    print(f"  {i}. {action}")

# ============================================================================
# Step 5: 执行动作队列（需要 Resolve 运行）
# ============================================================================
print("\n[Step 5] 执行动作队列")
print("-" * 70)
print("⚠ 跳过实际执行（需要 DaVinci Resolve 运行）")
print("\n如果要执行，请：")
print("1. 启动 DaVinci Resolve")
print("2. 打开一个项目")
print("3. 取消注释下面的代码：")
print()
print("# trace = run_actions(actions, trace_path='output_trace.json')")
print("# print(f'✓ 执行完成，trace 已保存')")

# 取消注释以实际执行：
# try:
#     trace = run_actions(actions, trace_path="output_trace.json")
#     print(f"✓ 执行完成，共 {len(trace)} 个动作")
#     
#     # 显示 trace
#     for entry in trace:
#         status = "✓" if entry["ok"] else "✗"
#         print(f"  {status} {entry['action']}: {entry['took_ms']}ms")
#     
#     print(f"✓ Trace 已保存: output_trace.json")
# except Exception as e:
#     print(f"✗ 执行失败: {e}")

# ============================================================================
# 清理
# ============================================================================
print("\n[清理]")
print("-" * 70)
scenes_path.unlink()
dsl_path.unlink()
print("✓ 已删除临时文件")

print("\n" + "=" * 70)
print("✓ 完整工作流演示完成！")
print("=" * 70)
print("\n工作流总结:")
print("1. EDL 解析 -> scenes.json")
print("2. AI 生成 -> editing_dsl.json")
print("3. 硬规则验证 -> 防止 AI 幻觉")
print("4. DSL 转换 -> Action 队列")
print("5. Runner 执行 -> DaVinci Resolve")
print("\n所有组件已就绪，可以投入使用！")
