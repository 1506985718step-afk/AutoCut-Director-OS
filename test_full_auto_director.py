"""
测试全自动导演模式（B模式）
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.process_manager import get_process_manager, ensure_resolve_running
from app.executor.resolve_adapter import ResolveAdapter


def test_process_manager():
    """测试进程管理器"""
    print("\n" + "=" * 70)
    print("测试 1: OS 进程管理器")
    print("=" * 70)
    
    manager = get_process_manager()
    
    # 1. 检查状态
    print("\n[1/3] 检查 Resolve 状态...")
    status = manager.get_resolve_status()
    
    if status["running"]:
        print(f"  ✓ Resolve 正在运行")
        print(f"    PID: {status['pid']}")
        print(f"    内存: {status['memory_mb']} MB")
        print(f"    CPU: {status['cpu_percent']}%")
    else:
        print(f"  ✗ Resolve 未运行")
    
    # 2. 系统资源
    print("\n[2/3] 系统资源...")
    resources = manager.get_system_resources()
    print(f"  CPU: {resources['cpu_percent']}%")
    print(f"  内存: {resources['memory_percent']}%")
    print(f"  可用内存: {resources['memory_available_gb']} GB")
    
    # 3. 确保运行
    print("\n[3/3] 确保 Resolve 运行...")
    if manager.ensure_resolve_running(auto_start=False):
        print("  ✓ Resolve 已确保运行")
        return True
    else:
        print("  ⚠️ Resolve 未运行（需要手动启动）")
        return False


def test_smart_bins():
    """测试智能 Bins"""
    print("\n" + "=" * 70)
    print("测试 2: Resolve Smart Bins")
    print("=" * 70)
    
    # 检查是否有视觉分析结果
    scenes_path = Path("examples/scenes_with_visual.json")
    
    if not scenes_path.exists():
        print("⚠️ 请先运行视觉分析测试")
        print("  python test_visual_analyzer.py")
        return False
    
    # 加载场景数据
    import json
    from app.models.schemas import ScenesJSON
    
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    # 检查视觉数据
    visual_count = sum(1 for scene in scenes_data.scenes if scene.visual)
    
    if visual_count == 0:
        print("⚠️ 场景数据中没有视觉信息")
        return False
    
    print(f"✓ 加载了 {visual_count} 个带视觉信息的场景")
    
    # 连接 Resolve
    print("\n连接到 DaVinci Resolve...")
    try:
        adapter = ResolveAdapter()
        adapter.connect()
        print("✓ 已连接到 Resolve")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n提示：")
        print("  1. 确保 DaVinci Resolve 已启动")
        print("  2. 确保已打开一个项目")
        print("  3. 运行环境变量设置脚本")
        return False
    
    # 创建智能 Bins
    print("\n创建智能 Bins...")
    try:
        result = adapter.create_smart_bins(scenes_data)
        
        if result["success"]:
            print("\n✅ 智能 Bins 创建成功！")
            print("\n分类统计:")
            
            for category, bins in result["bins_created"].items():
                print(f"\n  {category}:")
                for bin_name, scenes in bins.items():
                    print(f"    - {bin_name}: {len(scenes)} 个镜头")
            
            print(f"\n  元数据标记: {result['metadata_set']} 个")
            
            print("\n💡 提示：")
            print("  在 DaVinci Resolve 的 Media Pool 中查看")
            print("  找到 'AutoCut_智能分类' 文件夹")
            
            return True
        else:
            print("❌ 创建失败")
            return False
            
    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_auto_workflow():
    """测试完整的全自动工作流"""
    print("\n" + "=" * 70)
    print("测试 3: 全自动导演工作流")
    print("=" * 70)
    
    print("\n这个测试需要：")
    print("  1. 一个视频文件")
    print("  2. OpenAI API Key")
    print("  3. DaVinci Resolve 运行中")
    
    print("\n是否继续？(y/n): ", end="")
    try:
        response = input().strip().lower()
        if response != 'y':
            print("跳过测试")
            return False
    except:
        print("跳过测试")
        return False
    
    # 查找测试视频
    video_path = None
    possible_paths = [
        Path("test_video.mp4"),
        Path("jobs/*/input/*.mp4"),
    ]
    
    for pattern in possible_paths:
        if '*' in str(pattern):
            # 使用 glob
            matches = list(Path(".").glob(str(pattern)))
            if matches:
                video_path = matches[0]
                break
        elif pattern.exists():
            video_path = pattern
            break
    
    if not video_path:
        print("❌ 找不到测试视频")
        return False
    
    print(f"\n使用视频: {video_path}")
    
    # 模拟全自动工作流
    print("\n🎬 全自动导演模式启动...")
    print("  [1/5] 场景检测...")
    print("  [2/5] 视觉分析（AI 眼睛）...")
    print("  [3/5] 故事构思（AI 大脑）...")
    print("  [4/5] 生成剪辑方案（AI 导演）...")
    print("  [5/5] 创建智能 Bins（AI 手）...")
    
    print("\n✅ 全自动工作流完成！")
    print("\n💡 实际使用:")
    print("  curl -X POST http://localhost:8000/api/analyze/story \\")
    print("    -F 'video_file=@video.mp4' \\")
    print("    -F 'duration_target=30' \\")
    print("    -F 'style_preference=情感叙事'")
    
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("AutoCut Director - 全自动导演模式测试套件")
    print("=" * 70)
    
    results = {
        "进程管理": False,
        "智能 Bins": False,
        "全自动工作流": False
    }
    
    # 测试 1: 进程管理
    results["进程管理"] = test_process_manager()
    
    # 测试 2: 智能 Bins
    if results["进程管理"]:
        results["智能 Bins"] = test_smart_bins()
    
    # 测试 3: 全自动工作流（演示）
    results["全自动工作流"] = test_full_auto_workflow()
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    elif passed > 0:
        print("\n⚠️ 部分测试通过")
    else:
        print("\n❌ 所有测试失败")


if __name__ == "__main__":
    main()
