"""测试 Resolve 最小连接骨架"""
import os
import sys

# 设置环境变量（如果未设置）
if not os.environ.get("RESOLVE_SCRIPT_DIR"):
    os.environ["RESOLVE_SCRIPT_DIR"] = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"

from app.executor.resolve_adapter import connect_resolve

print("=" * 60)
print("DaVinci Resolve 最小连接测试")
print("=" * 60)

try:
    print("\n[1] 连接到 Resolve...")
    resolve, project = connect_resolve()
    print(f"✓ 连接成功")
    
    print("\n[2] 获取项目信息...")
    project_name = project.GetName()
    print(f"✓ 当前项目: {project_name}")
    
    print("\n[3] 获取时间线信息...")
    timeline_count = project.GetTimelineCount()
    print(f"✓ 时间线数量: {timeline_count}")
    
    current_timeline = project.GetCurrentTimeline()
    if current_timeline:
        timeline_name = current_timeline.GetName()
        print(f"✓ 当前时间线: {timeline_name}")
        
        # 获取时间线属性
        fps = current_timeline.GetSetting("timelineFrameRate")
        width = current_timeline.GetSetting("timelineResolutionWidth")
        height = current_timeline.GetSetting("timelineResolutionHeight")
        
        print(f"\n[4] 时间线属性:")
        print(f"  - 帧率: {fps} fps")
        print(f"  - 分辨率: {width}x{height}")
    else:
        print("⚠ 没有活动的时间线")
    
    print("\n[5] 获取媒体池信息...")
    media_pool = project.GetMediaPool()
    root_folder = media_pool.GetRootFolder()
    print(f"✓ 媒体池根目录: {root_folder.GetName()}")
    
    print("\n" + "=" * 60)
    print("✓ 所有测试通过！Resolve 连接正常")
    print("=" * 60)
    
except RuntimeError as e:
    print(f"\n✗ 连接失败: {e}")
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
