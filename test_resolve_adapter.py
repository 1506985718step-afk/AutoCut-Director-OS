"""测试 Resolve Adapter 完整功能"""
import os
import sys

# 设置环境变量
if not os.environ.get("RESOLVE_SCRIPT_DIR"):
    os.environ["RESOLVE_SCRIPT_DIR"] = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"

from app.executor.resolve_adapter import ResolveAdapter

print("=" * 70)
print("DaVinci Resolve Adapter 测试")
print("=" * 70)

try:
    # 1. 连接
    print("\n[1] 连接到 Resolve...")
    adapter = ResolveAdapter()
    adapter.connect()
    print("✓ 连接成功")
    print(f"  - 项目: {adapter.project.GetName()}")
    
    # 2. 创建时间线
    print("\n[2] 创建测试时间线...")
    timeline = adapter.create_timeline(
        name="AutoCut_Test",
        framerate=30.0,
        resolution={"width": 1920, "height": 1080}
    )
    print(f"✓ 时间线创建成功: {timeline.GetName()}")
    print(f"  - 帧率: {timeline.GetSetting('timelineFrameRate')} fps")
    print(f"  - 分辨率: {timeline.GetSetting('timelineResolutionWidth')}x{timeline.GetSetting('timelineResolutionHeight')}")
    
    # 3. 测试媒体导入（需要实际媒体文件）
    print("\n[3] 测试媒体导入...")
    print("⚠ 跳过（需要实际媒体文件）")
    # test_media = "D:/Footage/test.mp4"
    # if os.path.exists(test_media):
    #     adapter.append_clip(test_media, start=0, end=5, track=1)
    #     print(f"✓ 片段添加成功")
    
    # 4. 测试音频导入
    print("\n[4] 测试音频导入...")
    print("⚠ 跳过（需要实际音频文件）")
    # test_audio = "D:/Music/bgm.mp3"
    # if os.path.exists(test_audio):
    #     adapter.add_audio(test_audio, start=0, volume=0.5)
    #     print(f"✓ 音频添加成功")
    
    # 5. 测试 SRT 导入
    print("\n[5] 测试 SRT 导入...")
    print("⚠ 跳过（需要实际 SRT 文件）")
    # test_srt = "D:/Subtitles/test.srt"
    # if os.path.exists(test_srt):
    #     adapter.import_srt(test_srt, track=2)
    #     print(f"✓ 字幕导入成功")
    
    # 6. 测试导出
    print("\n[6] 测试导出设置...")
    print("⚠ 跳过（避免实际渲染）")
    # adapter.export("output/test.mp4", preset="H.264", quality="high")
    # print(f"✓ 导出任务已添加")
    
    print("\n" + "=" * 70)
    print("✓ Adapter 基础功能测试通过！")
    print("=" * 70)
    print("\n提示:")
    print("- 要测试完整功能，需要准备实际的媒体文件")
    print("- 取消注释相应代码块并提供文件路径")
    print("- 时间线已创建，可以在 Resolve 中查看")
    
except RuntimeError as e:
    print(f"\n✗ 测试失败: {e}")
    print("\n请确保:")
    print("1. DaVinci Resolve 正在运行")
    print("2. 已打开一个项目")
    print("3. RESOLVE_SCRIPT_DIR 环境变量已设置")
    sys.exit(1)
    
except Exception as e:
    print(f"\n✗ 未知错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
