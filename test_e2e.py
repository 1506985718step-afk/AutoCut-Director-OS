"""端到端测试：EDL -> scenes.json -> DSL 验证"""
import json
from pathlib import Path
from app.tools.scene_from_edl import parse_edl_to_scenes
from app.models.schemas import EditingDSL, ScenesJSON, DSLValidator

print("=" * 70)
print("AutoCut Director 端到端测试")
print("=" * 70)

# Step 1: 解析 EDL
print("\n[Step 1] 解析 EDL -> scenes.json")
print("-" * 70)

scenes_dict = parse_edl_to_scenes(
    edl_path="examples/test.edl",
    fps=30,
    primary_clip_path="D:/Footage/input.mp4"
)

print(f"✓ 解析成功，生成 {len(scenes_dict['scenes'])} 个场景")
for scene in scenes_dict['scenes']:
    print(f"  {scene['scene_id']}: {scene['start_tc']} -> {scene['end_tc']} "
          f"({scene['end_frame'] - scene['start_frame']} 帧)")

# 保存 scenes.json
scenes_path = Path("test_output_scenes.json")
with open(scenes_path, "w", encoding="utf-8") as f:
    json.dump(scenes_dict, f, indent=2, ensure_ascii=False)
print(f"✓ 已保存: {scenes_path}")

# Step 2: 创建 DSL（模拟 AI 生成）
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
dsl_path = Path("test_output_dsl.json")
with open(dsl_path, "w", encoding="utf-8") as f:
    json.dump(dsl_dict, f, indent=2, ensure_ascii=False)
print(f"✓ 已保存: {dsl_path}")

# Step 3: 硬规则验证
print("\n[Step 3] 硬规则验证（防 AI 幻觉）")
print("-" * 70)

scenes = ScenesJSON(**scenes_dict)
dsl = EditingDSL(**dsl_dict)

is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)

if is_valid:
    print("✓ 验证通过！DSL 可以安全执行")
    print(f"  - 场景数量: {len(scenes.scenes)}")
    print(f"  - Timeline 项: {len(dsl.editing_plan.timeline)}")
    print(f"  - 目标平台: {dsl.meta.target}")
    print(f"  - 画幅比例: {dsl.meta.aspect}")
else:
    print("✗ 验证失败！发现以下问题：")
    for error in errors:
        print(f"  - {error}")

# Step 4: 模拟 AI 幻觉场景
print("\n[Step 4] 测试 AI 幻觉检测")
print("-" * 70)

# 创建一个有问题的 DSL
bad_dsl_dict = json.loads(json.dumps(dsl_dict))
bad_dsl_dict["editing_plan"]["timeline"].append({
    "order": 3,
    "scene_id": "S9999",  # 不存在的场景
    "trim_frames": [0, 100],
    "purpose": "fake",
    "overlay_text": "AI 幻觉"
})

bad_dsl = EditingDSL(**bad_dsl_dict)
is_valid, errors = DSLValidator.validate_dsl_against_scenes(bad_dsl, scenes)

if not is_valid:
    print("✓ 成功检测到 AI 幻觉！")
    for error in errors:
        print(f"  - {error}")
else:
    print("✗ 未能检测到 AI 幻觉（不应该发生）")

# 清理
print("\n[清理]")
print("-" * 70)
scenes_path.unlink()
dsl_path.unlink()
print("✓ 已删除测试文件")

print("\n" + "=" * 70)
print("✓ 端到端测试完成！")
print("=" * 70)
