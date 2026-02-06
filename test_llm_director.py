"""测试 LLM Director - AI 生成剪辑脚本"""
import json
from pathlib import Path
from app.core.llm_engine import LLMDirector, generate_dsl_from_materials
from app.models.schemas import ScenesJSON, TranscriptJSON, DSLValidator


def test_llm_director():
    """测试 LLM 生成 DSL"""
    print("=" * 60)
    print("测试 LLM Director - AI 生成剪辑脚本")
    print("=" * 60)
    
    # 1. 加载示例素材
    print("\n1. 加载示例素材...")
    scenes_path = Path("examples/scenes.v1.json")
    transcript_path = Path("examples/transcript.v1.json")
    
    scenes_data = json.loads(scenes_path.read_text(encoding="utf-8"))
    transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
    
    scenes = ScenesJSON(**scenes_data)
    transcript = TranscriptJSON(**transcript_data)
    
    print(f"✓ 加载了 {len(scenes.scenes)} 个场景")
    print(f"✓ 加载了 {len(transcript.segments)} 个字幕段")
    
    # 2. 调用 LLM 生成 DSL
    print("\n2. 调用 LLM 生成剪辑脚本...")
    print("   (这需要配置 OPENAI_API_KEY)")
    
    try:
        director = LLMDirector()
        
        style_prompt = """
抖音爆款风格：
- 节奏快，每 3-5 秒切换画面
- 开头必须有强烈的 Hook（钩子）
- 删除所有废话和停顿
- 文字叠加要简短有力（5-8 字）
- 突出关键词和数字
"""
        
        dsl = director.generate_editing_dsl(scenes, transcript, style_prompt)
        
        print("✓ AI 生成成功！")
        print("\n生成的 DSL 预览：")
        print(json.dumps(dsl, ensure_ascii=False, indent=2)[:500] + "...")
        
        # 3. 验证生成的 DSL
        print("\n3. 验证 DSL 硬规则...")
        errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
        
        if errors:
            print("✗ 验证失败（AI 幻觉检测）：")
            for err in errors:
                print(f"  - {err}")
        else:
            print("✓ 验证通过！AI 没有幻觉")
        
        # 4. 保存生成的 DSL
        output_path = Path("examples/editing_dsl.ai_generated.json")
        output_path.write_text(
            json.dumps(dsl, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"\n✓ DSL 已保存到: {output_path}")
        
    except ValueError as e:
        print(f"✗ 错误: {e}")
        print("\n请确保在 .env 中配置了 OPENAI_API_KEY")
        print("示例：")
        print("  OPENAI_API_KEY=sk-...")
        print("  OPENAI_MODEL=gpt-4o")
        return False
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    return True


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 60)
    print("测试便捷函数 - generate_dsl_from_materials()")
    print("=" * 60)
    
    # 加载素材
    scenes_path = Path("examples/scenes.v1.json")
    transcript_path = Path("examples/transcript.v1.json")
    
    scenes_data = json.loads(scenes_path.read_text(encoding="utf-8"))
    transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
    
    scenes = ScenesJSON(**scenes_data)
    transcript = TranscriptJSON(**transcript_data)
    
    try:
        # 使用便捷函数
        dsl = generate_dsl_from_materials(
            scenes=scenes,
            transcript=transcript,
            style="B站风格：节奏适中、字幕完整、强调知识点"
        )
        
        print("✓ 便捷函数调用成功！")
        print(f"\n生成的 timeline 包含 {len(dsl['editing_plan']['timeline'])} 个片段")
        
        return True
        
    except ValueError as e:
        print(f"✗ 错误: {e}")
        return False


if __name__ == "__main__":
    # 测试 1: LLM Director
    success1 = test_llm_director()
    
    # 测试 2: 便捷函数
    if success1:
        test_convenience_function()
    
    print("\n提示：")
    print("- 如果测试失败，请检查 .env 中的 OPENAI_API_KEY")
    print("- 推荐使用 gpt-4o 模型（长窗口，JSON 模式支持好）")
    print("- 也可以使用 Azure OpenAI，配置 OPENAI_BASE_URL")
