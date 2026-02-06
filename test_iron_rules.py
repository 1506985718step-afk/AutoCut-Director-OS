"""
测试两条铁律的验证逻辑
"""
import json
from app.models.schemas import DSLValidator


def test_iron_rule_1_violation():
    """测试铁律 1: 未提供素材库却要求素材调用"""
    print("\n" + "=" * 70)
    print("测试铁律 1 - 违反情况")
    print("=" * 70)
    
    scenes_data = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120
            }
        ]
    }
    
    dsl_data = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": [10, 90],
                    "broll": ["product.mp4", "user_scene.mp4"]  # ❌ 没有素材库
                }
            ],
            "subtitles": {
                "mode": "from_transcript"
            }
        }
    }
    
    # 验证（没有提供素材库）
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl_data, 
        scenes_data, 
        broll_library=None
    )
    
    print("\n验证结果:")
    if errors:
        print("❌ 验证失败（符合预期）:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("⚠️  验证通过（不符合预期）")
    
    assert len(errors) > 0, "应该检测到铁律 1 违反"
    assert any("铁律 1" in err for err in errors), "错误信息应包含'铁律 1'"
    
    print("\n✅ 铁律 1 验证逻辑正确")


def test_iron_rule_1_pass():
    """测试铁律 1: 正确使用（broll 为空）"""
    print("\n" + "=" * 70)
    print("测试铁律 1 - 正确情况")
    print("=" * 70)
    
    scenes_data = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120
            }
        ]
    }
    
    dsl_data = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": [10, 90],
                    "broll": []  # ✅ 没有素材库，broll 为空
                }
            ],
            "subtitles": {
                "mode": "from_transcript"
            }
        }
    }
    
    # 验证
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl_data, 
        scenes_data, 
        broll_library=None
    )
    
    print("\n验证结果:")
    if errors:
        print("❌ 验证失败:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("✅ 验证通过（符合预期）")
    
    assert len(errors) == 0, "不应该有错误"
    
    print("\n✅ 铁律 1 正确使用通过")


def test_iron_rule_1_with_library():
    """测试铁律 1: 提供了素材库"""
    print("\n" + "=" * 70)
    print("测试铁律 1 - 有素材库")
    print("=" * 70)
    
    scenes_data = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120
            }
        ]
    }
    
    dsl_data = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": [10, 90],
                    "broll": ["product.mp4"]  # ✅ 素材库中存在
                }
            ],
            "subtitles": {
                "mode": "from_transcript"
            }
        }
    }
    
    # 提供素材库
    broll_library = ["product.mp4", "user_scene.mp4"]
    
    # 验证
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl_data, 
        scenes_data, 
        broll_library=broll_library
    )
    
    print("\n验证结果:")
    if errors:
        print("❌ 验证失败:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("✅ 验证通过（符合预期）")
    
    assert len(errors) == 0, "不应该有错误"
    
    print("\n✅ 铁律 1 有素材库通过")


def test_iron_rule_2_violation():
    """测试铁律 2: 使用了 timecode 而不是 frame"""
    print("\n" + "=" * 70)
    print("测试铁律 2 - 违反情况")
    print("=" * 70)
    
    scenes_data = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120
            }
        ]
    }
    
    dsl_data = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": ["00:00:01:00", "00:00:04:00"]  # ❌ 使用了 timecode
                }
            ],
            "subtitles": {
                "mode": "from_transcript"
            }
        }
    }
    
    # 验证
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl_data, 
        scenes_data
    )
    
    print("\n验证结果:")
    if errors:
        print("❌ 验证失败（符合预期）:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("⚠️  验证通过（不符合预期）")
    
    assert len(errors) > 0, "应该检测到铁律 2 违反"
    # Schema 验证会先捕获类型错误
    assert any("integer" in err.lower() or "铁律 2" in err for err in errors), "错误信息应包含类型错误或'铁律 2'"
    
    print("\n✅ 铁律 2 验证逻辑正确")


def test_iron_rule_2_pass():
    """测试铁律 2: 正确使用 frame"""
    print("\n" + "=" * 70)
    print("测试铁律 2 - 正确情况")
    print("=" * 70)
    
    scenes_data = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120
            }
        ]
    }
    
    dsl_data = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": [30, 120]  # ✅ 使用整数帧号
                }
            ],
            "subtitles": {
                "mode": "from_transcript"
            }
        }
    }
    
    # 验证
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl_data, 
        scenes_data
    )
    
    print("\n验证结果:")
    if errors:
        print("❌ 验证失败:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("✅ 验证通过（符合预期）")
    
    assert len(errors) == 0, "不应该有错误"
    
    print("\n✅ 铁律 2 正确使用通过")


def test_scenes_fps_required():
    """测试 scenes.json 必须包含 fps"""
    print("\n" + "=" * 70)
    print("测试 scenes.json 必须包含 fps")
    print("=" * 70)
    
    # 没有 fps
    scenes_data_no_fps = {
        "meta": {"schema": "scenes.v1"},
        "scenes": []
    }
    
    result = DSLValidator.validate_scenes_has_fps(scenes_data_no_fps)
    print(f"\n没有 fps: {result}")
    assert not result, "应该返回 False"
    
    # 有 fps
    scenes_data_with_fps = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": []
    }
    
    result = DSLValidator.validate_scenes_has_fps(scenes_data_with_fps)
    print(f"有 fps: {result}")
    assert result, "应该返回 True"
    
    print("\n✅ fps 验证逻辑正确")


def test_frame_timecode_conversion():
    """测试 frame 和 timecode 转换"""
    print("\n" + "=" * 70)
    print("测试 frame ↔ timecode 转换")
    print("=" * 70)
    
    fps = 30
    
    # Frame → Timecode
    test_cases = [
        (0, "00:00:00:00"),
        (30, "00:00:01:00"),
        (120, "00:00:04:00"),
        (1800, "00:01:00:00"),
        (108000, "01:00:00:00")
    ]
    
    print("\nFrame → Timecode:")
    for frame, expected_tc in test_cases:
        tc = DSLValidator.frames_to_timecode(frame, fps)
        print(f"  {frame:6d} 帧 → {tc} (期望: {expected_tc})")
        assert tc == expected_tc, f"转换错误: {tc} != {expected_tc}"
    
    # Timecode → Frame
    print("\nTimecode → Frame:")
    for expected_frame, tc in test_cases:
        frame = DSLValidator.timecode_to_frames(tc, fps)
        print(f"  {tc} → {frame:6d} 帧 (期望: {expected_frame})")
        assert frame == expected_frame, f"转换错误: {frame} != {expected_frame}"
    
    print("\n✅ 转换逻辑正确")


def test_complete_validation():
    """测试完整验证流程"""
    print("\n" + "=" * 70)
    print("测试完整验证流程")
    print("=" * 70)
    
    scenes_data = {
        "meta": {"schema": "scenes.v1", "fps": 30},
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120
            },
            {
                "scene_id": "S0002",
                "start_frame": 120,
                "end_frame": 240
            }
        ]
    }
    
    dsl_data = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": [10, 90],
                    "broll": []
                },
                {
                    "order": 2,
                    "scene_id": "S0002",
                    "trim_frames": [130, 220],
                    "broll": []
                }
            ],
            "subtitles": {
                "mode": "from_transcript"
            }
        }
    }
    
    # 验证
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl_data, 
        scenes_data
    )
    
    print("\n验证结果:")
    if errors:
        print("❌ 验证失败:")
        for err in errors:
            print(f"  - {err}")
    else:
        print("✅ 验证通过")
    
    assert len(errors) == 0, "不应该有错误"
    
    print("\n✅ 完整验证通过")


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - 两条铁律测试\n")
    
    try:
        # 铁律 1 测试
        test_iron_rule_1_violation()
        test_iron_rule_1_pass()
        test_iron_rule_1_with_library()
        
        # 铁律 2 测试
        test_iron_rule_2_violation()
        test_iron_rule_2_pass()
        test_scenes_fps_required()
        test_frame_timecode_conversion()
        
        # 完整验证
        test_complete_validation()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试通过")
        print("=" * 70)
        print("\n两条铁律验证逻辑正确！")
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
