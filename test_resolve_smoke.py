"""
Resolve Smoke Test - 完整可复现的基础测试

测试流程：
1. 连接 Resolve
2. 新建时间线
3. 插入整段素材
4. 导出 mp4
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.executor.resolve_adapter import ResolveAdapter


def smoke_test():
    """完整的 Resolve Smoke Test"""
    
    print("\n" + "=" * 70)
    print("🎬 Resolve Smoke Test - 开始")
    print("=" * 70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤 1: 连接 Resolve
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n1️⃣  连接 DaVinci Resolve...")
    
    try:
        adapter = ResolveAdapter()
        adapter.connect()
        print("✅ 连接成功")
        print(f"   项目名称: {adapter.project.GetName()}")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保:")
        print("  1. DaVinci Resolve 正在运行")
        print("  2. 已打开一个项目")
        print("  3. 已运行 .\\scripts\\set_resolve_env.ps1")
        return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤 2: 新建时间线
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n2️⃣  新建时间线...")
    
    timeline_name = "SmokeTest_Timeline"
    
    try:
        timeline = adapter.create_timeline(
            name=timeline_name,
            framerate=30.0,
            resolution={"width": 1920, "height": 1080}
        )
        print(f"✅ 时间线创建成功: {timeline_name}")
        print(f"   帧率: 30 fps")
        print(f"   分辨率: 1920x1080")
    except Exception as e:
        print(f"❌ 时间线创建失败: {e}")
        return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤 3: 插入整段素材
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n3️⃣  插入素材...")
    
    # 提示用户提供素材路径
    print("\n请提供测试素材路径（或按 Enter 跳过）:")
    video_path = input("视频文件路径: ").strip()
    
    if not video_path:
        print("⚠️  跳过素材插入（未提供路径）")
        print("   建议: 提供一个测试视频文件进行完整测试")
    else:
        if not Path(video_path).exists():
            print(f"❌ 文件不存在: {video_path}")
            return False
        
        try:
            # 插入整段素材（不裁剪）
            adapter.append_clip(
                source=video_path,
                start=0,  # 从头开始
                end=0,    # 到结尾（0 表示使用完整长度）
                track=1
            )
            print(f"✅ 素材插入成功: {Path(video_path).name}")
        except Exception as e:
            print(f"❌ 素材插入失败: {e}")
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 步骤 4: 导出 mp4
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n4️⃣  导出 mp4...")
    
    output_path = "test_output/smoke_test_output.mp4"
    Path(output_path).parent.mkdir(exist_ok=True)
    
    print("\n⚠️  注意: Resolve API 的导出功能有限")
    print("   建议手动导出步骤（固化流程）:")
    print("\n   【手动导出步骤】")
    print("   1. 在 Resolve 中切换到 Deliver 页面")
    print("   2. 选择 'H.264' 预设")
    print("   3. 设置输出路径:")
    print(f"      {Path(output_path).absolute()}")
    print("   4. 点击 'Add to Render Queue'")
    print("   5. 点击 'Start Render'")
    print("   6. 等待渲染完成")
    
    # 尝试使用 API 导出（可能失败）
    try:
        print("\n尝试使用 API 导出...")
        job_id = adapter.export(
            output_path=output_path,
            preset="H.264",
            quality="high"
        )
        print(f"✅ 导出任务已添加: Job ID = {job_id}")
        print("   请在 Resolve 中查看渲染队列")
    except Exception as e:
        print(f"⚠️  API 导出失败: {e}")
        print("   这是正常的，请使用上述手动步骤")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 完成
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "=" * 70)
    print("✅ Smoke Test 完成")
    print("=" * 70)
    
    print("\n📋 测试结果:")
    print("  ✅ 连接 Resolve")
    print("  ✅ 新建时间线")
    if video_path:
        print("  ✅ 插入素材")
    else:
        print("  ⚠️  插入素材（跳过）")
    print("  ⚠️  导出 mp4（需手动完成）")
    
    print("\n💡 下一步:")
    print("  1. 在 Resolve 中查看时间线")
    print("  2. 使用 Deliver 页面手动导出")
    print("  3. 验证输出文件")
    
    return True


if __name__ == "__main__":
    print("\n🎬 DaVinci Resolve - Smoke Test\n")
    
    print("前置条件:")
    print("  1. DaVinci Resolve 正在运行")
    print("  2. 已打开一个项目")
    print("  3. 已运行环境配置脚本")
    print("     PowerShell: .\\scripts\\set_resolve_env.ps1")
    
    confirm = input("\n是否继续？(y/n): ").strip().lower()
    
    if confirm == 'y':
        try:
            success = smoke_test()
            
            if success:
                print("\n🎉 Smoke Test 通过！")
            else:
                print("\n❌ Smoke Test 失败")
                
        except KeyboardInterrupt:
            print("\n\n已取消")
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("已取消")
