"""
测试视觉分析器
"""
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.visual_analyzer import VisualAnalyzer
from app.models.schemas import ScenesJSON


def test_visual_analysis():
    """测试视觉分析功能"""
    print("\n" + "=" * 70)
    print("测试视觉分析器")
    print("=" * 70)
    
    # 1. 检查测试文件
    video_path = "test_video.mp4"
    scenes_path = "examples/scenes.v1.json"
    
    if not Path(video_path).exists():
        # 尝试在 jobs 目录中查找
        jobs_dir = Path("jobs")
        if jobs_dir.exists():
            video_files = list(jobs_dir.glob("*/input/*.mp4"))
            if video_files:
                video_path = str(video_files[0])
                print(f"✓ 使用测试视频: {video_path}")
            else:
                print("❌ 没有找到测试视频文件")
                print("\n提示：")
                print("  1. 创建一个 test_video.mp4 文件")
                print("  2. 或在 jobs/*/input/ 目录中放置视频文件")
                return False
        else:
            print("❌ 没有找到测试视频文件")
            return False
    
    if not Path(scenes_path).exists():
        print(f"❌ 场景文件不存在: {scenes_path}")
        return False
    
    # 2. 加载 scenes.json
    print(f"\n[1/3] 加载场景数据...")
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    print(f"  ✓ 加载了 {len(scenes_data.scenes)} 个场景")
    
    # 3. 初始化分析器
    print(f"\n[2/3] 初始化视觉分析器...")
    try:
        analyzer = VisualAnalyzer()
        print(f"  ✓ 使用模型: {analyzer.vision_model}")
    except ValueError as e:
        print(f"  ❌ 初始化失败: {e}")
        print("\n提示：请在 .env 文件中配置 OPENAI_API_KEY")
        return False
    
    # 4. 分析视觉（限制 3 个场景用于测试）
    print(f"\n[3/3] 开始视觉分析（限制 3 个场景）...")
    try:
        updated_scenes = analyzer.analyze_scene_visuals(
            scenes_data,
            video_path,
            max_scenes=3
        )
        
        # 5. 显示结果
        print("\n" + "=" * 70)
        print("分析结果")
        print("=" * 70)
        
        for scene in updated_scenes.scenes:
            if scene.visual:
                print(f"\n{scene.scene_id}:")
                print(f"  描述: {scene.visual.summary}")
                print(f"  景别: {scene.visual.shot_type}")
                print(f"  主体: {', '.join(scene.visual.subjects)}")
                print(f"  动作: {scene.visual.action}")
                print(f"  情绪: {scene.visual.mood}")
                print(f"  光线: {scene.visual.lighting}")
                print(f"  质量: {scene.visual.quality_score}/10")
        
        # 6. 保存结果
        output_path = "examples/scenes_with_visual.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(updated_scenes.model_dump(), f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 结果已保存到: {output_path}")
        return True
        
    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visual_enhanced_dsl():
    """测试使用视觉信息生成 DSL"""
    print("\n" + "=" * 70)
    print("测试视觉增强的 DSL 生成")
    print("=" * 70)
    
    # 检查是否有视觉分析结果
    scenes_path = "examples/scenes_with_visual.json"
    
    if not Path(scenes_path).exists():
        print("⚠️ 请先运行视觉分析测试")
        return False
    
    # 加载数据
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    # 检查是否有视觉数据
    has_visual = any(scene.visual for scene in scenes_data.scenes)
    
    if not has_visual:
        print("⚠️ 场景数据中没有视觉信息")
        return False
    
    print(f"✓ 加载了 {len(scenes_data.scenes)} 个场景")
    
    visual_count = sum(1 for scene in scenes_data.scenes if scene.visual)
    print(f"✓ 其中 {visual_count} 个场景有视觉分析")
    
    # 显示视觉信息统计
    print("\n视觉信息统计:")
    
    shot_types = {}
    moods = {}
    quality_scores = []
    
    for scene in scenes_data.scenes:
        if scene.visual:
            # 统计景别
            shot_type = scene.visual.shot_type
            shot_types[shot_type] = shot_types.get(shot_type, 0) + 1
            
            # 统计情绪
            mood = scene.visual.mood
            if mood:
                moods[mood] = moods.get(mood, 0) + 1
            
            # 收集质量分数
            quality_scores.append(scene.visual.quality_score)
    
    print(f"\n  景别分布:")
    for shot_type, count in shot_types.items():
        print(f"    - {shot_type}: {count}")
    
    print(f"\n  情绪分布:")
    for mood, count in moods.items():
        print(f"    - {mood}: {count}")
    
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        print(f"\n  平均质量: {avg_quality:.1f}/10")
        print(f"  最高质量: {max(quality_scores)}/10")
        print(f"  最低质量: {min(quality_scores)}/10")
    
    print("\n✅ 视觉数据已准备好，可以用于 DSL 生成")
    print("\n提示：现在 LLM Director 可以根据视觉信息智能选择镜头了！")
    
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("AutoCut Director - 视觉分析测试套件")
    print("=" * 70)
    
    results = {
        "视觉分析": False,
        "DSL 增强": False
    }
    
    # 测试 1: 视觉分析
    results["视觉分析"] = test_visual_analysis()
    
    # 测试 2: 视觉增强的 DSL
    if results["视觉分析"]:
        results["DSL 增强"] = test_visual_enhanced_dsl()
    
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
        print("\n下一步：")
        print("  1. 使用 test_llm_director.py 测试视觉增强的 DSL 生成")
        print("  2. 观察 AI 导演如何根据画面内容选择镜头")
    elif passed > 0:
        print("\n⚠️ 部分测试通过")
    else:
        print("\n❌ 所有测试失败")
        print("\n故障排除:")
        print("  1. 确保 .env 中配置了 OPENAI_API_KEY")
        print("  2. 确保有测试视频文件")
        print("  3. 确保 FFmpeg 已安装")


if __name__ == "__main__":
    main()
