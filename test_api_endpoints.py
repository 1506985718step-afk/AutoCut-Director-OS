"""
测试 API 端点
"""
import requests
import json

BASE_URL = "http://localhost:8787"


def test_health():
    """测试健康检查"""
    print("\n" + "=" * 70)
    print("🏥 测试健康检查")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_llm_style_presets():
    """测试获取风格预设"""
    print("\n" + "=" * 70)
    print("🎨 测试获取风格预设")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/llm/style-presets")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            presets = response.json()
            print(f"\n可用风格预设:")
            for preset in presets:
                print(f"  - {preset['name']}: {preset['description']}")
            return True
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_llm_generate_dsl():
    """测试生成 DSL"""
    print("\n" + "=" * 70)
    print("🤖 测试 LLM 生成 DSL")
    print("=" * 70)
    
    # 准备测试数据
    scenes_data = {
        "meta": {
            "schema": "scenes.v1",
            "fps": 30,
            "source": "test"
        },
        "media": {
            "primary_clip_path": "test.mp4"
        },
        "scenes": [
            {
                "scene_id": "S0001",
                "start_frame": 0,
                "end_frame": 120,
                "start_tc": "00:00:00:00",
                "end_tc": "00:00:04:00"
            },
            {
                "scene_id": "S0002",
                "start_frame": 120,
                "end_frame": 240,
                "start_tc": "00:00:04:00",
                "end_tc": "00:00:08:00"
            }
        ]
    }
    
    transcript_data = {
        "meta": {
            "schema": "transcript.v1",
            "language": "zh"
        },
        "segments": [
            {
                "start": 0.0,
                "end": 3.5,
                "text": "大家好，今天教大家一个超实用的技巧"
            },
            {
                "start": 3.5,
                "end": 7.0,
                "text": "90%的人都不知道这个方法"
            }
        ]
    }
    
    request_data = {
        "scenes": scenes_data,
        "transcript": transcript_data,
        "style_prompt": "抖音爆款风格：节奏快、文字多、强调关键词"
    }
    
    try:
        print("\n发送请求...")
        response = requests.post(
            f"{BASE_URL}/api/llm/generate-dsl",
            json=request_data,
            timeout=30
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ DSL 生成成功")
            print(f"\n生成的 DSL:")
            print(json.dumps(result.get("dsl", {}), indent=2, ensure_ascii=False))
            
            # 检查关键字段
            dsl = result.get("dsl", {})
            if "meta" in dsl and "editing_plan" in dsl:
                print(f"\n✅ DSL 结构正确")
                
                timeline = dsl.get("editing_plan", {}).get("timeline", [])
                print(f"✅ Timeline 包含 {len(timeline)} 个片段")
                
                return True
            else:
                print(f"\n❌ DSL 结构不完整")
                return False
        else:
            print(f"❌ 请求失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_bgm_library():
    """测试 BGM 库（如果有的话）"""
    print("\n" + "=" * 70)
    print("🎵 测试 BGM 库")
    print("=" * 70)
    
    # 检查 BGM 库是否存在
    import os
    if not os.path.exists("bgm_library"):
        print("⚠️  BGM 库不存在，跳过测试")
        return True
    
    # 扫描 BGM 库
    from app.tools.bgm_library import create_bgm_library
    
    try:
        library = create_bgm_library("bgm_library")
        bgm_list = library.get_all()
        
        print(f"✅ 找到 {len(bgm_list)} 首 BGM")
        for bgm in bgm_list[:3]:  # 只显示前3首
            print(f"  - {bgm.id}: {bgm.mood} | {bgm.bpm} BPM")
        
        return True
    except Exception as e:
        print(f"❌ BGM 库测试失败: {e}")
        return False


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - API 端点测试")
    print("=" * 70)
    
    results = []
    
    # 运行测试
    results.append(("健康检查", test_health()))
    results.append(("风格预设", test_llm_style_presets()))
    results.append(("LLM 生成 DSL", test_llm_generate_dsl()))
    results.append(("BGM 库", test_bgm_library()))
    
    # 显示结果
    print("\n" + "=" * 70)
    print("📊 测试结果")
    print("=" * 70)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n✅ 所有测试通过！")
        print("\n🎉 AutoCut Director 已准备就绪")
        print(f"\n访问 API 文档: http://localhost:8787/docs")
    else:
        print("\n⚠️  部分测试失败")
