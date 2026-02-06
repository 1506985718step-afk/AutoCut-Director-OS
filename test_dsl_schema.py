"""
测试 DSL Schema 验证
"""
import json
from pathlib import Path
from app.models.dsl_validator import DSLValidator


def test_valid_dsl():
    """测试有效的 DSL"""
    print("\n" + "=" * 70)
    print("测试: 有效的 DSL")
    print("=" * 70)
    
    dsl = {
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
                    "trim_frames": [10, 90],
                    "purpose": "hook",
                    "overlay_text": "第一步就错了",
                    "broll": []
                }
            ],
            "subtitles": {
                "mode": "from_transcript",
                "style": "bold_yellow"
            },
            "music": {
                "track_path": "",
                "volume_db": -18
            }
        },
        "export": {
            "resolution": "1080x1920",
            "format": "mp4"
        }
    }
    
    errors = DSLValidator.validate_schema(dsl)
    
    if errors:
        print("❌ 验证失败:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ 验证通过")
        return True


def test_invalid_dsl_missing_required():
    """测试缺少必需字段的 DSL"""
    print("\n" + "=" * 70)
    print("测试: 缺少必需字段")
    print("=" * 70)
    
    dsl = {
        "meta": {
            "schema": "editing_dsl.v1"
            # 缺少 target
        },
        "editing_plan": {
            "timeline": [],
            "subtitles": {}
        }
    }
    
    errors = DSLValidator.validate_schema(dsl)
    
    if errors:
        print("✅ 正确检测到错误:")
        for err in errors:
            print(f"  - {err}")
        return True
    else:
        print("❌ 应该检测到错误但没有")
        return False


def test_invalid_dsl_wrong_type():
    """测试类型错误的 DSL"""
    print("\n" + "=" * 70)
    print("测试: 类型错误")
    print("=" * 70)
    
    dsl = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": "1",  # 应该是 integer
                    "scene_id": "S0001",
                    "trim_frames": [10, 90]
                }
            ],
            "subtitles": {}
        }
    }
    
    errors = DSLValidator.validate_schema(dsl)
    
    if errors:
        print("✅ 正确检测到错误:")
        for err in errors:
            print(f"  - {err}")
        return True
    else:
        print("❌ 应该检测到错误但没有")
        return False


def test_iron_rule_1_violation():
    """测试铁律 1 违反"""
    print("\n" + "=" * 70)
    print("测试: 铁律 1 违反（有 broll 但无素材库）")
    print("=" * 70)
    
    dsl = {
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
                    "broll": ["product.mp4"]  # 有 broll
                }
            ],
            "subtitles": {}
        }
    }
    
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
    
    # 没有提供素材库
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl, scenes_data, broll_library=None
    )
    
    if errors and any("铁律 1" in err for err in errors):
        print("✅ 正确检测到铁律 1 违反:")
        for err in errors:
            print(f"  - {err}")
        return True
    else:
        print("❌ 应该检测到铁律 1 违反")
        return False


def test_iron_rule_2_violation():
    """测试铁律 2 违反"""
    print("\n" + "=" * 70)
    print("测试: 铁律 2 违反（使用 timecode）")
    print("=" * 70)
    
    # 注意：JSON Schema 会先验证类型，所以这个测试会在 Schema 层面失败
    # 这实际上是好的，因为它在更早的阶段就捕获了错误
    
    dsl = {
        "meta": {
            "schema": "editing_dsl.v1",
            "target": "douyin"
        },
        "editing_plan": {
            "timeline": [
                {
                    "order": 1,
                    "scene_id": "S0001",
                    "trim_frames": ["00:00:01:00", "00:00:04:00"]  # 使用 timecode（字符串）
                }
            ],
            "subtitles": {}
        }
    }
    
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
    
    errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
    
    # JSON Schema 会先检测到类型错误（字符串 vs 整数）
    # 这实际上也是铁律 2 的一部分（只用整数帧号）
    if errors and (any("铁律 2" in err for err in errors) or any("not of type 'integer'" in err for err in errors)):
        print("✅ 正确检测到铁律 2 违反（通过 Schema 类型检查）:")
        for err in errors:
            print(f"  - {err}")
        return True
    else:
        print("❌ 应该检测到铁律 2 违反")
        print(f"实际错误: {errors}")
        return False


def test_complete_validation():
    """测试完整验证流程"""
    print("\n" + "=" * 70)
    print("测试: 完整验证流程")
    print("=" * 70)
    
    dsl = {
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
                    "trim_frames": [10, 90],
                    "purpose": "hook",
                    "broll": []
                },
                {
                    "order": 2,
                    "scene_id": "S0002",
                    "trim_frames": [130, 220],
                    "purpose": "content",
                    "broll": []
                }
            ],
            "subtitles": {
                "mode": "from_transcript",
                "style": "bold_yellow"
            }
        },
        "export": {
            "resolution": "1080x1920",
            "format": "mp4"
        }
    }
    
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
    
    errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
    
    if errors:
        print("❌ 验证失败:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ 验证通过")
        return True


def test_example_files():
    """测试示例文件"""
    print("\n" + "=" * 70)
    print("测试: 示例文件验证")
    print("=" * 70)
    
    # 测试 minimal_dsl.v1.json
    dsl_path = Path("examples/minimal_dsl.v1.json")
    scenes_path = Path("examples/scenes.v1.json")
    
    if not dsl_path.exists():
        print(f"⚠️  文件不存在: {dsl_path}")
        return False
    
    if not scenes_path.exists():
        print(f"⚠️  文件不存在: {scenes_path}")
        return False
    
    with open(dsl_path, 'r', encoding='utf-8') as f:
        dsl = json.load(f)
    
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_data = json.load(f)
    
    errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
    
    if errors:
        print("❌ 示例文件验证失败:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("✅ 示例文件验证通过")
        return True


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - DSL Schema 验证测试\n")
    
    tests = [
        ("有效的 DSL", test_valid_dsl),
        ("缺少必需字段", test_invalid_dsl_missing_required),
        ("类型错误", test_invalid_dsl_wrong_type),
        ("铁律 1 违反", test_iron_rule_1_violation),
        ("铁律 2 违反", test_iron_rule_2_violation),
        ("完整验证", test_complete_validation),
        ("示例文件", test_example_files)
    ]
    
    results = {}
    
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ 测试 '{name}' 出错: {e}")
            import traceback
            traceback.print_exc()
            results[name] = False
    
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    
    for name, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    else:
        print("\n⚠️  部分测试失败")
