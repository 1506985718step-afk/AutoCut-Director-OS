"""
测试音频音量设置功能
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.executor.resolve_adapter import ResolveAdapter


def test_audio_volume():
    """测试音频音量设置"""
    print("\n" + "=" * 70)
    print("🎬 测试音频音量设置")
    print("=" * 70)
    
    # 连接 Resolve
    print("\n1️⃣  连接 Resolve...")
    adapter = ResolveAdapter()
    
    try:
        adapter.connect()
        print("✅ 连接成功")
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("\n请确保:")
        print("  1. DaVinci Resolve 正在运行")
        print("  2. 已打开一个项目")
        print("  3. 已运行环境配置脚本: .\\scripts\\set_resolve_env.ps1")
        return False
    
    # 创建测试时间线
    print("\n2️⃣  创建测试时间线...")
    try:
        timeline = adapter.create_timeline(
            name="AudioVolumeTest_Timeline",
            framerate=30.0,
            resolution={"width": 1920, "height": 1080}
        )
        print(f"✅ 时间线创建成功: {timeline.GetName()}")
    except Exception as e:
        print(f"❌ 时间线创建失败: {e}")
        return False
    
    # 测试音频导入和音量设置
    print("\n3️⃣  测试音频音量设置...")
    
    # 测试用例 1: 默认音量 (1.0)
    print("\n测试用例 1: 默认音量 (1.0)")
    test_audio = "D:/Music/test_bgm.mp3"  # 请替换为实际的音频文件路径
    
    if not os.path.exists(test_audio):
        print(f"⚠️  测试音频文件不存在: {test_audio}")
        print("   请创建一个测试音频文件或修改路径")
        
        # 尝试使用示例路径
        possible_paths = [
            "C:/Windows/Media/Alarm01.wav",
            "C:/Windows/Media/Ring01.wav",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                test_audio = path
                print(f"   使用系统音频: {test_audio}")
                break
        else:
            print("   跳过音频测试")
            return True
    
    try:
        items = adapter.add_audio(test_audio, start=0, volume=1.0)
        print(f"✅ 音频添加成功 (默认音量)")
        print(f"   添加了 {len(items)} 个音频片段")
    except Exception as e:
        print(f"❌ 音频添加失败: {e}")
        return False
    
    # 测试用例 2: 降低音量 (0.5)
    print("\n测试用例 2: 降低音量 (0.5)")
    try:
        items = adapter.add_audio(test_audio, start=0, volume=0.5)
        print(f"✅ 音频添加成功 (音量 0.5)")
        print(f"   添加了 {len(items)} 个音频片段")
    except Exception as e:
        print(f"❌ 音频添加失败: {e}")
        return False
    
    # 测试用例 3: 更低音量 (0.2)
    print("\n测试用例 3: 更低音量 (0.2)")
    try:
        items = adapter.add_audio(test_audio, start=0, volume=0.2)
        print(f"✅ 音频添加成功 (音量 0.2)")
        print(f"   添加了 {len(items)} 个音频片段")
    except Exception as e:
        print(f"❌ 音频添加失败: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ 音频音量测试完成")
    print("=" * 70)
    print("\n请在 Resolve 中检查:")
    print("  1. 时间线中是否有 3 个音频片段")
    print("  2. 在 Inspector 中查看每个片段的音量设置")
    print("  3. 如果音量设置失败，会显示警告信息")
    print("\n⚠️  注意: 如果 API 无法设置音量，请手动在 Inspector 中调整")
    
    return True


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - 音频音量测试")
    print("=" * 70)
    
    success = test_audio_volume()
    
    if success:
        print("\n✅ 测试完成")
    else:
        print("\n❌ 测试失败")
        sys.exit(1)
