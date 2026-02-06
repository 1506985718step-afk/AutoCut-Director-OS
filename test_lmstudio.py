"""
测试 LM Studio 集成

使用前确保：
1. LM Studio 已启动
2. 已加载视觉模型（推荐 LLaVA）
3. 本地服务器已启动（默认端口 1234）
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.visual_analyzer_lmstudio import LMStudioVisualAnalyzer
from app.core.runtime_profile import get_runtime_profile
from app.core.execution_policy import get_execution_policy


def test_lmstudio_connection():
    """测试 LM Studio 连接"""
    print("=" * 60)
    print("测试 1: LM Studio 连接")
    print("=" * 60)
    
    analyzer = LMStudioVisualAnalyzer()
    
    if analyzer.is_available():
        print("✓ LM Studio 可用")
        
        model = analyzer.get_loaded_model()
        if model:
            print(f"✓ 当前加载的模型: {model}")
        else:
            print("⚠️  无法获取模型信息")
    else:
        print("✗ LM Studio 不可用")
        print("\n请确保：")
        print("1. LM Studio 已启动")
        print("2. 已加载视觉模型（如 LLaVA）")
        print("3. 本地服务器已启动（默认端口 1234）")
        return False
    
    return True


def test_runtime_profile():
    """测试运行时配置检测"""
    print("\n" + "=" * 60)
    print("测试 2: 运行时配置检测")
    print("=" * 60)
    
    profile = get_runtime_profile(force_reload=True)
    
    print(f"\n{profile.get_explanation()}")
    
    if profile.ai_runtime.lmstudio:
        print(f"\n✓ 检测到 LM Studio")
        print(f"  当前模型: {profile.ai_runtime.lmstudio_model}")
    else:
        print(f"\n⚠️  未检测到 LM Studio")
    
    return profile


def test_execution_policy():
    """测试执行策略"""
    print("\n" + "=" * 60)
    print("测试 3: 执行策略")
    print("=" * 60)
    
    policy = get_execution_policy(force_reload=True)
    
    print(f"\n策略说明: {policy.explanation}")
    print(f"\n视觉分析配置:")
    print(f"  Provider: {policy.vision.provider}")
    print(f"  Backend: {policy.vision.local_backend}")
    print(f"  Model: {policy.vision.model}")
    print(f"  Device: {policy.vision.device}")
    print(f"  Max Scenes: {policy.vision.max_scenes}")
    
    return policy


def test_image_analysis():
    """测试图片分析"""
    print("\n" + "=" * 60)
    print("测试 4: 图片分析")
    print("=" * 60)
    
    # 检查是否有测试图片
    test_images = [
        "test_output/frame_0001.jpg",
        "examples/test_frame.jpg",
    ]
    
    test_image = None
    for img in test_images:
        if Path(img).exists():
            test_image = img
            break
    
    if not test_image:
        print("⚠️  未找到测试图片，跳过此测试")
        print("提示：可以手动放置一张图片到 test_output/frame_0001.jpg")
        return
    
    print(f"使用测试图片: {test_image}")
    
    analyzer = LMStudioVisualAnalyzer()
    
    try:
        description = analyzer.analyze_image(
            test_image,
            prompt="Describe this image briefly."
        )
        
        print(f"\n✓ 分析成功:")
        print(f"  {description}")
    
    except Exception as e:
        print(f"\n✗ 分析失败: {e}")


def test_factory_integration():
    """测试工厂模式集成"""
    print("\n" + "=" * 60)
    print("测试 5: 工厂模式集成")
    print("=" * 60)
    
    from app.tools.visual_analyzer_factory import get_visual_analyzer
    
    # 测试自动选择
    print("\n测试自动选择（使用执行策略）:")
    analyzer = get_visual_analyzer(use_policy=True)
    print(f"  分析器类型: {type(analyzer).__name__}")
    
    # 测试强制使用本地
    print("\n测试强制使用本地:")
    analyzer = get_visual_analyzer(force_local=True, use_policy=False)
    print(f"  分析器类型: {type(analyzer).__name__}")


def main():
    """主测试流程"""
    print("\n🧪 LM Studio 集成测试\n")
    
    # 测试 1: 连接
    if not test_lmstudio_connection():
        print("\n❌ LM Studio 连接失败，终止测试")
        return
    
    # 测试 2: 运行时配置
    profile = test_runtime_profile()
    
    # 测试 3: 执行策略
    policy = test_execution_policy()
    
    # 测试 4: 图片分析
    test_image_analysis()
    
    # 测试 5: 工厂集成
    test_factory_integration()
    
    print("\n" + "=" * 60)
    print("✓ 所有测试完成")
    print("=" * 60)
    
    # 总结
    print("\n📊 集成状态:")
    if profile.ai_runtime.lmstudio:
        print("  ✓ LM Studio 已集成")
        print(f"  ✓ 当前模型: {profile.ai_runtime.lmstudio_model}")
        print(f"  ✓ 执行策略: {policy.explanation}")
    else:
        print("  ⚠️  LM Studio 未检测到")
        print("  提示：启动 LM Studio 并加载视觉模型后重新测试")


if __name__ == "__main__":
    main()
