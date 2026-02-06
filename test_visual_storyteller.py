"""
测试视觉叙事引擎 (Visual Storyteller)
"""
import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.visual_storyteller import VisualStoryteller, create_story_from_visuals
from app.models.schemas import ScenesJSON


def test_visual_storyteller():
    """测试视觉叙事引擎"""
    print("\n" + "=" * 70)
    print("测试视觉叙事引擎 (Visual Storyteller)")
    print("=" * 70)
    
    # 1. 检查测试文件
    scenes_path = "examples/scenes_with_visual.json"
    
    if not Path(scenes_path).exists():
        print(f"❌ 场景文件不存在: {scenes_path}")
        print("\n提示：请先运行视觉分析测试")
        print("  python test_visual_analyzer.py")
        return False
    
    # 2. 加载场景数据
    print(f"\n[1/5] 加载场景数据...")
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    # 检查视觉数据
    visual_count = sum(1 for scene in scenes_data.scenes if scene.visual)
    
    if visual_count == 0:
        print("❌ 场景数据中没有视觉信息")
        return False
    
    print(f"  ✓ 加载了 {len(scenes_data.scenes)} 个场景")
    print(f"  ✓ 其中 {visual_count} 个场景有视觉数据")
    
    # 3. 初始化 Visual Storyteller
    print(f"\n[2/5] 初始化 Visual Storyteller...")
    try:
        storyteller = VisualStoryteller()
        print(f"  ✓ 使用模型: {storyteller.model}")
    except ValueError as e:
        print(f"  ❌ 初始化失败: {e}")
        print("\n提示：请在 .env 文件中配置 OPENAI_API_KEY")
        return False
    
    # 4. 生成故事（无脚本模式）
    print(f"\n[3/5] AI 构思故事...")
    try:
        story_result = storyteller.generate_story_from_visuals(
            scenes_data,
            duration_target=30,
            style_preference=None  # 让 AI 自由发挥
        )
        
        # 5. 显示结果
        print("\n" + "=" * 70)
        print("故事构思结果")
        print("=" * 70)
        
        print(f"\n📖 主题: {story_result['theme']}")
        print(f"🎬 剪辑逻辑: {story_result['logic']}")
        print(f"🎨 叙事风格: {story_result['narrative_style']}")
        print(f"🎵 音乐建议: {story_result['suggested_bgm_mood']}")
        
        # 显示聚类结果
        print(f"\n📊 素材聚类:")
        for group_name, scene_ids in story_result['clustering']['groups'].items():
            print(f"  - {group_name}: {len(scene_ids)} 个镜头")
        
        # 显示备选主题
        if story_result.get('alternative_themes'):
            print(f"\n💡 备选主题:")
            for i, alt in enumerate(story_result['alternative_themes'], 1):
                print(f"  {i}. {alt.get('theme', 'N/A')}")
                print(f"     理由: {alt.get('reason', 'N/A')}")
        
        # 显示生成的文案
        print(f"\n📝 生成的文案 ({len(story_result['generated_transcript'].segments)} 段):")
        for i, segment in enumerate(story_result['generated_transcript'].segments, 1):
            print(f"  {i}. [{segment.start:.1f}s - {segment.end:.1f}s] {segment.text}")
        
        # 6. 保存结果
        output_path = "examples/story_result.json"
        
        # 转换 TranscriptJSON 为字典
        story_output = {
            "theme": story_result['theme'],
            "logic": story_result['logic'],
            "narrative_style": story_result['narrative_style'],
            "suggested_bgm_mood": story_result['suggested_bgm_mood'],
            "clustering": story_result['clustering'],
            "alternative_themes": story_result.get('alternative_themes', []),
            "generated_transcript": story_result['generated_transcript'].model_dump()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(story_output, f, indent=2, ensure_ascii=False)
        
        print(f"\n✅ 结果已保存到: {output_path}")
        
        # 7. 保存 transcript.json
        transcript_path = "examples/transcript_generated.json"
        with open(transcript_path, 'w', encoding='utf-8') as f:
            json.dump(
                story_result['generated_transcript'].model_dump(),
                f,
                indent=2,
                ensure_ascii=False
            )
        
        print(f"✅ 文案已保存到: {transcript_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 故事生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_generate_dsl_from_story():
    """测试从故事生成 DSL"""
    print("\n" + "=" * 70)
    print("测试从故事生成 DSL")
    print("=" * 70)
    
    # 检查是否有故事结果
    story_path = "examples/story_result.json"
    scenes_path = "examples/scenes_with_visual.json"
    
    if not Path(story_path).exists():
        print("⚠️ 请先运行故事生成测试")
        return False
    
    if not Path(scenes_path).exists():
        print("⚠️ 场景文件不存在")
        return False
    
    # 加载数据
    with open(story_path, 'r', encoding='utf-8') as f:
        story_result = json.load(f)
    
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    # 重建 TranscriptJSON
    from app.models.schemas import TranscriptJSON
    story_result['generated_transcript'] = TranscriptJSON(
        **story_result['generated_transcript']
    )
    
    print(f"✓ 加载故事: {story_result['theme']}")
    
    # 生成 DSL
    print("\n生成 editing_dsl.json...")
    try:
        storyteller = VisualStoryteller()
        dsl = storyteller.generate_dsl_from_story(
            scenes_data,
            story_result,
            platform="douyin"
        )
        
        # 保存 DSL
        dsl_path = "examples/editing_dsl_from_story.json"
        with open(dsl_path, 'w', encoding='utf-8') as f:
            json.dump(dsl, f, indent=2, ensure_ascii=False)
        
        print(f"✅ DSL 已保存到: {dsl_path}")
        
        # 显示 DSL 摘要
        timeline = dsl.get('editing_plan', {}).get('timeline', [])
        print(f"\n📋 DSL 摘要:")
        print(f"  - 时间线片段: {len(timeline)}")
        print(f"  - 目标平台: {dsl.get('meta', {}).get('target', 'N/A')}")
        print(f"  - 分辨率: {dsl.get('export', {}).get('resolution', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ DSL 生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_different_styles():
    """测试不同风格的故事生成"""
    print("\n" + "=" * 70)
    print("测试不同风格的故事生成")
    print("=" * 70)
    
    scenes_path = "examples/scenes_with_visual.json"
    
    if not Path(scenes_path).exists():
        print("⚠️ 场景文件不存在")
        return False
    
    # 加载场景数据
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    # 测试不同风格
    styles = [
        "高燃踩点",
        "情感叙事",
        "氛围感"
    ]
    
    storyteller = VisualStoryteller()
    
    for style in styles:
        print(f"\n{'=' * 70}")
        print(f"风格: {style}")
        print('=' * 70)
        
        try:
            story_result = storyteller.generate_story_from_visuals(
                scenes_data,
                duration_target=30,
                style_preference=style
            )
            
            print(f"  主题: {story_result['theme']}")
            print(f"  风格: {story_result['narrative_style']}")
            print(f"  音乐: {story_result['suggested_bgm_mood']}")
            
            # 显示第一句文案
            if story_result['generated_transcript'].segments:
                first_line = story_result['generated_transcript'].segments[0].text
                print(f"  开场: {first_line}")
            
        except Exception as e:
            print(f"  ❌ 失败: {e}")
    
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("AutoCut Director - Visual Storyteller 测试套件")
    print("=" * 70)
    
    results = {
        "故事生成": False,
        "DSL 生成": False,
        "多风格测试": False
    }
    
    # 测试 1: 故事生成
    results["故事生成"] = test_visual_storyteller()
    
    # 测试 2: DSL 生成
    if results["故事生成"]:
        results["DSL 生成"] = test_generate_dsl_from_story()
    
    # 测试 3: 多风格测试（可选）
    # results["多风格测试"] = test_different_styles()
    
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
        print("  1. 查看生成的故事: examples/story_result.json")
        print("  2. 查看生成的文案: examples/transcript_generated.json")
        print("  3. 查看生成的 DSL: examples/editing_dsl_from_story.json")
        print("  4. 使用 test_different_styles() 测试不同风格")
    elif passed > 0:
        print("\n⚠️ 部分测试通过")
    else:
        print("\n❌ 所有测试失败")
        print("\n故障排除:")
        print("  1. 确保 .env 中配置了 OPENAI_API_KEY")
        print("  2. 确保已运行视觉分析: python test_visual_analyzer.py")
        print("  3. 确保有 scenes_with_visual.json 文件")


if __name__ == "__main__":
    main()
