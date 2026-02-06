"""测试 DaVinci Resolve 连接"""
import sys

print("=" * 60)
print("DaVinci Resolve Connection Test")
print("=" * 60)

# 1. 检查 PYTHONPATH
print("\n1. Checking PYTHONPATH...")
for i, path in enumerate(sys.path[:5]):
    print(f"   [{i}] {path}")

# 2. 尝试导入 DaVinciResolveScript
print("\n2. Importing DaVinciResolveScript...")
try:
    import DaVinciResolveScript as dvr_script
    print("   ✓ Module imported successfully")
except ImportError as e:
    print(f"   ✗ Import failed: {e}")
    print("\n   Note: This is normal if DaVinci Resolve is not running.")
    print("   Please start DaVinci Resolve and try again.")
    sys.exit(1)

# 3. 尝试连接到 Resolve
print("\n3. Connecting to DaVinci Resolve...")
try:
    resolve = dvr_script.scriptapp("Resolve")
    
    if not resolve:
        print("   ✗ Connection failed")
        print("\n   Troubleshooting:")
        print("   - Make sure DaVinci Resolve is running")
        print("   - Open a project in Resolve")
        print("   - Check Resolve settings:")
        print("     Preferences > System > General > 'External scripting using'")
        sys.exit(1)
    
    print("   ✓ Connected to DaVinci Resolve")
    
    # 4. 获取项目信息
    print("\n4. Getting project information...")
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    
    if project:
        print(f"   ✓ Current project: {project.GetName()}")
        
        # 获取时间线信息
        timeline_count = project.GetTimelineCount()
        print(f"   ✓ Timeline count: {timeline_count}")
        
        current_timeline = project.GetCurrentTimeline()
        if current_timeline:
            print(f"   ✓ Current timeline: {current_timeline.GetName()}")
        else:
            print("   ⚠ No active timeline")
    else:
        print("   ⚠ No project is open")
        print("   Please open a project in DaVinci Resolve")
    
    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
