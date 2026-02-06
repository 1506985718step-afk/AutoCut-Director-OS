"""
测试 Ollama 本地视觉模型

测试内容：
1. Ollama 服务连接
2. 模型可用性检查
3. 单张图片分析
4. 批量场景分析
5. 性能对比
"""
import sys
import time
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.visual_analyzer_local import LocalVisualAnalyzer
from app.models.schemas import ScenesJSON, Scene, ScenesMeta, ScenesMedia


def test_ollama_connection():
    """测试 1: Ollama 服务连接"""
    print("\n" + "=" * 70)
    print("测试 1: Ollama 服务连接")
    print("=" * 70)
    
    try:
        analyzer = LocalVisualAnalyzer(model="moondream")
        print("✅ Ollama 服务连接成功")
        print(f"   模型: {analyzer.model}")
        print(f"   地址: {analyzer.ollama_host}")
        return True
    except Exception as e:
        print(f"❌ Ollama 服务连接失败: {e}")
        print("\n请确保:")
        print("  1. Ollama 已安装: https://ollama.com/download")
        print("  2. Ollama 服务正在运行")
        print("  3. 模型已下载: ollama pull moondream")
        return False


def test_model_availability():
    """测试 2: 模型可用性检查"""
    print("\n" + "=" * 70)
    print("测试 2: 模型可用性检查")
    print("=" * 70)
    
    import requests
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            models = response.json().get("models", [])
            print(f"✅ 已安装 {len(models)} 个模型:")
            
            for model in models:
                name = model.get("name", "")
                size = model.get("size", 0) / (1024**3)  # 转换为 GB
                print(f"   - {name} ({size:.1f} GB)")
            
            # 检查推荐模型
            has_moondream = any("moondream" in m.get("name", "") for m in models)
            has_llava = any("llava-phi3" in m.get("name", "") for m in models)
            
            if has_moondream:
                print("\n✅ Moondream 已安装（推荐）")
            else:
                print("\n⚠️  Moondream 未安装，建议运行: ollama pull moondream")
            
            if has_llava:
                print("✅ LLaVA-Phi3 已安装（备选）")
            else:
                print("⚠️  LLaVA-Phi3 未安装，可选运行: ollama pull llava-phi3")
            
            return True
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 检查模型失败: {e}")
        return False


def test_single_image_analysis():
    """测试 3: 单张图片分析"""
    print("\n" + "=" * 70)
    print("测试 3: 单张图片分析")
    print("=" * 70)
    
    # 创建测试场景
    test_scene = Scene(
        scene_id="S0001",
        start_frame=0,
        end_frame=90,
        start_tc="00:00:00:00",
        end_tc="00:00:03:00"
    )
    
    scenes_data = ScenesJSON(
        meta=ScenesMeta(fps=30.0, source="test"),
        media=ScenesMedia(primary_clip_path="test_video.mp4"),
        scenes=[test_scene]
    )
    
    # 检查测试视频
    test_video = Path("jobs/proj_20260205_150732/input/杨昊昆.mp4")
    if not test_video.exists():
        print(f"⚠️  测试视频不存在: {test_video}")
        print("   跳过此测试")
        return False
    
    try:
        analyzer = LocalVisualAnalyzer(model="moondream")
        
        print(f"   测试视频: {test_video}")
        print("   开始分析...")
        
        start_time = time.time()
        updated_scenes = analyzer.analyze_scene_visuals(
            scenes_data,
            str(test_video),
            max_scenes=1
        )
        elapsed = time.time() - start_time
        
        if updated_scenes.scenes[0].visual:
            visual = updated_scenes.scenes[0].visual
            print(f"\n✅ 分析成功 (耗时: {elapsed:.2f}秒)")
            print(f"   摘要: {visual.summary}")
            print(f"   景别: {visual.shot_type}")
            print(f"   主体: {', '.join(visual.subjects)}")
            print(f"   动作: {visual.action}")
            print(f"   情绪: {visual.mood}")
            print(f"   光线: {visual.lighting}")
            print(f"   质量: {visual.quality_score}/10")
            return True
        else:
            print("❌ 分析失败：未生成视觉数据")
            return False
    
    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_batch_analysis():
    """测试 4: 批量场景分析"""
    print("\n" + "=" * 70)
    print("测试 4: 批量场景分析")
    print("=" * 70)
    
    # 检查测试数据
    test_video = Path("jobs/proj_20260205_150732/input/杨昊昆.mp4")
    test_scenes = Path("jobs/proj_20260205_150732/temp/scenes.json")
    
    if not test_video.exists() or not test_scenes.exists():
        print(f"⚠️  测试数据不存在")
        print("   跳过此测试")
        return False
    
    try:
        # 加载场景数据
        with open(test_scenes, 'r', encoding='utf-8') as f:
            scenes_dict = json.load(f)
        
        scenes_data = ScenesJSON(**scenes_dict)
        total_scenes = len(scenes_data.scenes)
        
        print(f"   场景数量: {total_scenes}")
        print(f"   测试数量: 5 个场景")
        
        analyzer = LocalVisualAnalyzer(model="moondream")
        
        start_time = time.time()
        updated_scenes = analyzer.analyze_scene_visuals(
            scenes_data,
            str(test_video),
            max_scenes=5
        )
        elapsed = time.time() - start_time
        
        analyzed_count = sum(1 for s in updated_scenes.scenes if s.visual)
        avg_time = elapsed / analyzed_count if analyzed_count > 0 else 0
        
        print(f"\n✅ 批量分析完成")
        print(f"   总耗时: {elapsed:.2f}秒")
        print(f"   平均耗时: {avg_time:.2f}秒/场景")
        print(f"   分析数量: {analyzed_count}/5")
        
        # 显示质量分布
        quality_scores = [s.visual.quality_score for s in updated_scenes.scenes if s.visual]
        if quality_scores:
            avg_quality = sum(quality_scores) / len(quality_scores)
            print(f"   平均质量: {avg_quality:.1f}/10")
        
        return True
    
    except Exception as e:
        print(f"❌ 批量分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_performance_comparison():
    """测试 5: 性能对比"""
    print("\n" + "=" * 70)
    print("测试 5: 性能对比（Moondream vs LLaVA-Phi3）")
    print("=" * 70)
    
    test_video = Path("jobs/proj_20260205_150732/input/杨昊昆.mp4")
    test_scenes = Path("jobs/proj_20260205_150732/temp/scenes.json")
    
    if not test_video.exists() or not test_scenes.exists():
        print(f"⚠️  测试数据不存在")
        print("   跳过此测试")
        return False
    
    # 加载场景数据
    with open(test_scenes, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    results = {}
    
    # 测试 Moondream
    try:
        print("\n[1/2] 测试 Moondream...")
        analyzer = LocalVisualAnalyzer(model="moondream")
        
        start_time = time.time()
        updated_scenes = analyzer.analyze_scene_visuals(
            scenes_data,
            str(test_video),
            max_scenes=3
        )
        elapsed = time.time() - start_time
        
        analyzed = sum(1 for s in updated_scenes.scenes if s.visual)
        quality_scores = [s.visual.quality_score for s in updated_scenes.scenes if s.visual]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        results["moondream"] = {
            "time": elapsed,
            "avg_time": elapsed / analyzed if analyzed > 0 else 0,
            "quality": avg_quality
        }
        
        print(f"   ✅ 完成: {elapsed:.2f}秒, 质量: {avg_quality:.1f}/10")
    
    except Exception as e:
        print(f"   ❌ 失败: {e}")
        results["moondream"] = None
    
    # 测试 LLaVA-Phi3（如果已安装）
    try:
        print("\n[2/2] 测试 LLaVA-Phi3...")
        analyzer = LocalVisualAnalyzer(model="llava-phi3")
        
        start_time = time.time()
        updated_scenes = analyzer.analyze_scene_visuals(
            scenes_data,
            str(test_video),
            max_scenes=3
        )
        elapsed = time.time() - start_time
        
        analyzed = sum(1 for s in updated_scenes.scenes if s.visual)
        quality_scores = [s.visual.quality_score for s in updated_scenes.scenes if s.visual]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        results["llava-phi3"] = {
            "time": elapsed,
            "avg_time": elapsed / analyzed if analyzed > 0 else 0,
            "quality": avg_quality
        }
        
        print(f"   ✅ 完成: {elapsed:.2f}秒, 质量: {avg_quality:.1f}/10")
    
    except Exception as e:
        print(f"   ⚠️  LLaVA-Phi3 未安装或失败: {e}")
        results["llava-phi3"] = None
    
    # 显示对比
    print("\n" + "-" * 70)
    print("性能对比结果:")
    print("-" * 70)
    
    if results.get("moondream"):
        m = results["moondream"]
        print(f"Moondream:    {m['avg_time']:.2f}秒/场景, 质量: {m['quality']:.1f}/10")
    
    if results.get("llava-phi3"):
        l = results["llava-phi3"]
        print(f"LLaVA-Phi3:   {l['avg_time']:.2f}秒/场景, 质量: {l['quality']:.1f}/10")
    
    if results.get("moondream") and results.get("llava-phi3"):
        speedup = results["llava-phi3"]["avg_time"] / results["moondream"]["avg_time"]
        print(f"\nMoondream 速度提升: {speedup:.1f}x")
    
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("Ollama 本地视觉模型测试")
    print("=" * 70)
    
    tests = [
        ("Ollama 服务连接", test_ollama_connection),
        ("模型可用性检查", test_model_availability),
        ("单张图片分析", test_single_image_analysis),
        ("批量场景分析", test_batch_analysis),
        ("性能对比", test_performance_comparison),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except KeyboardInterrupt:
            print("\n\n⚠️  测试被用户中断")
            break
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！Ollama 本地视觉模型已就绪。")
    elif passed > 0:
        print("\n⚠️  部分测试通过，请检查失败的测试。")
    else:
        print("\n❌ 所有测试失败，请检查 Ollama 安装和配置。")
        print("\n参考文档: OLLAMA_SETUP_GUIDE.md")


if __name__ == "__main__":
    main()
