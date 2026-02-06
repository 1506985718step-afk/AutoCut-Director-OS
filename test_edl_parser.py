"""测试 EDL 解析器"""
import json
from app.tools.scene_from_edl import parse_edl_to_scenes

# 创建测试 EDL 文件
test_edl = """TITLE: Test Timeline

001  AX  V  C  01:00:00:00 01:00:04:00 00:00:00:00 00:00:04:00
002  AX  V  C  01:00:04:00 01:00:08:00 00:00:04:00 00:00:08:00
003  AX  V  C  01:00:08:00 01:00:12:00 00:00:08:00 00:00:12:00
"""

# 保存测试文件
with open("test.edl", "w") as f:
    f.write(test_edl)

# 解析
result = parse_edl_to_scenes(
    edl_path="test.edl",
    fps=30,
    primary_clip_path="D:/Footage/input.mp4"
)

# 打印结果
print(json.dumps(result, indent=2, ensure_ascii=False))

# 验证
print("\n=== 验证 ===")
print(f"场景数量: {len(result['scenes'])}")
print(f"FPS: {result['meta']['fps']}")
print(f"Schema: {result['meta']['schema']}")

for scene in result['scenes']:
    print(f"\n{scene['scene_id']}:")
    print(f"  时间码: {scene['start_tc']} -> {scene['end_tc']}")
    print(f"  帧范围: {scene['start_frame']} -> {scene['end_frame']}")
    print(f"  时长: {(scene['end_frame'] - scene['start_frame']) / 30:.2f}s")

# 清理
import os
os.remove("test.edl")
