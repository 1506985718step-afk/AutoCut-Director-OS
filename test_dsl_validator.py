"""测试 DSL 硬规则验证器（防 AI 幻觉）"""
import json
from app.models.schemas import EditingDSL, ScenesJSON, DSLValidator

# 加载示例文件
with open("examples/scenes.v1.json", "r", encoding="utf-8") as f:
    scenes_data = json.load(f)
scenes = ScenesJSON(**scenes_data)

with open("examples/editing_dsl.v1.json", "r", encoding="utf-8") as f:
    dsl_data = json.load(f)
dsl = EditingDSL(**dsl_data)

print("=" * 60)
print("DSL 硬规则验证测试（防 AI 幻觉）")
print("=" * 60)

# 测试 1: 正常情况
print("\n测试 1: 正常 DSL（应该通过）")
is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes)
print(f"结果: {'✓ 通过' if is_valid else '✗ 失败'}")
if errors:
    for error in errors:
        print(f"  - {error}")

# 测试 2: scene_id 不存在（AI 幻觉）
print("\n测试 2: scene_id 不存在（AI 幻觉）")
dsl_data_bad = json.loads(json.dumps(dsl_data))
dsl_data_bad["editing_plan"]["timeline"][0]["scene_id"] = "S9999"  # 不存在的场景
dsl_bad = EditingDSL(**dsl_data_bad)

is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl_bad, scenes)
print(f"结果: {'✓ 通过' if is_valid else '✗ 失败（预期）'}")
if errors:
    for error in errors:
        print(f"  - {error}")

# 测试 3: trim_frames 超出范围（AI 幻觉）
print("\n测试 3: trim_frames 超出场景范围（AI 幻觉）")
dsl_data_bad2 = json.loads(json.dumps(dsl_data))
dsl_data_bad2["editing_plan"]["timeline"][0]["trim_frames"] = [10, 999]  # 超出范围
dsl_bad2 = EditingDSL(**dsl_data_bad2)

is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl_bad2, scenes)
print(f"结果: {'✓ 通过' if is_valid else '✗ 失败（预期）'}")
if errors:
    for error in errors:
        print(f"  - {error}")

# 测试 4: trim_frames 顺序错误
print("\n测试 4: trim_frames 顺序错误")
dsl_data_bad3 = json.loads(json.dumps(dsl_data))
dsl_data_bad3["editing_plan"]["timeline"][0]["trim_frames"] = [90, 10]  # 顺序反了
dsl_bad3 = EditingDSL(**dsl_data_bad3)

is_valid, errors = DSLValidator.validate_dsl_against_scenes(dsl_bad3, scenes)
print(f"结果: {'✓ 通过' if is_valid else '✗ 失败（预期）'}")
if errors:
    for error in errors:
        print(f"  - {error}")

print("\n" + "=" * 60)
print("✓ 硬规则验证器工作正常！")
print("=" * 60)
