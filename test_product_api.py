"""
测试产品级 API
"""
import requests
import time
import json
from pathlib import Path


BASE_URL = "http://localhost:8787"


def test_create_project():
    """测试创建项目"""
    print("\n=== 测试创建项目 ===")
    
    # 准备测试视频（使用一个小的测试文件）
    test_video = Path("test_video.mp4")
    
    if not test_video.exists():
        print("⚠️ 测试视频不存在，跳过测试")
        print("提示：创建一个名为 test_video.mp4 的测试视频文件")
        return None
    
    # 创建项目
    with open(test_video, 'rb') as f:
        files = {'video': f}
        data = {
            'platform': 'douyin',
            'style': 'viral',
            'pace': 'fast',
            'subtitle_density': 'standard',
            'music_preference': 'emotional'
        }
        
        response = requests.post(
            f"{BASE_URL}/api/projects/create",
            files=files,
            data=data
        )
    
    print(f"状态码: {response.status_code}")
    result = response.json()
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("✅ 创建项目成功")
        return result['project_id']
    else:
        print("❌ 创建项目失败")
        return None


def test_get_project_status(project_id):
    """测试获取项目状态"""
    print(f"\n=== 测试获取项目状态 ===")
    print(f"项目 ID: {project_id}")
    
    # 轮询状态
    max_attempts = 30
    for i in range(max_attempts):
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}/status")
        
        if response.status_code != 200:
            print(f"❌ 获取状态失败: {response.status_code}")
            break
        
        status = response.json()
        print(f"\n[{i+1}/{max_attempts}] 进度: {status.get('progress', 0)}%")
        print(f"状态: {status.get('status')}")
        print(f"当前步骤: {status.get('current_step')}")
        
        if status.get('status') == 'completed':
            print("✅ 项目处理完成")
            return True
        elif status.get('status') == 'error':
            print(f"❌ 项目处理失败: {status.get('error')}")
            return False
        
        time.sleep(2)
    
    print("⚠️ 超时，项目仍在处理中")
    return False


def test_get_project(project_id):
    """测试获取项目详情"""
    print(f"\n=== 测试获取项目详情 ===")
    
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}")
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        project = response.json()
        print(f"项目详情:")
        print(f"  - 版本: {project.get('version')}")
        print(f"  - 状态: {project.get('status')}")
        print(f"  - 创建时间: {project.get('created_at')}")
        
        if 'summary' in project:
            print(f"  - 摘要:")
            for key, value in project['summary'].items():
                print(f"    - {key}: {value}")
        
        print("✅ 获取项目详情成功")
        return True
    else:
        print("❌ 获取项目详情失败")
        return False


def test_adjust_project(project_id):
    """测试调整项目"""
    print(f"\n=== 测试调整项目 ===")
    
    adjustments = {
        'pace': 'faster',
        'hook': 'stronger',
        'music': 'keep',
        'subtitle': 'keep'
    }
    
    response = requests.post(
        f"{BASE_URL}/api/projects/{project_id}/adjust",
        json={'adjustments': adjustments}
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"新版本: {result.get('new_version')}")
        print("✅ 调整项目成功")
        return result.get('new_version')
    else:
        print(f"❌ 调整项目失败: {response.json()}")
        return None


def test_get_versions(project_id):
    """测试获取版本列表"""
    print(f"\n=== 测试获取版本列表 ===")
    
    response = requests.get(f"{BASE_URL}/api/projects/{project_id}/versions")
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"总版本数: {result.get('total_versions')}")
        
        for version in result.get('versions', []):
            print(f"\n版本 {version.get('version')}:")
            print(f"  - 状态: {version.get('status')}")
            print(f"  - 创建时间: {version.get('created_at')}")
            if version.get('user_adjustments'):
                print(f"  - 调整: {version.get('user_adjustments')}")
        
        print("✅ 获取版本列表成功")
        return True
    else:
        print("❌ 获取版本列表失败")
        return False


def test_create_export(project_id):
    """测试创建导出"""
    print(f"\n=== 测试创建导出 ===")
    
    response = requests.post(
        f"{BASE_URL}/api/exports/",
        json={
            'project_id': project_id,
            'quality': '1080p'
        }
    )
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        export_id = result.get('export_id')
        print(f"导出 ID: {export_id}")
        print("✅ 创建导出成功")
        return export_id
    else:
        print(f"❌ 创建导出失败: {response.json()}")
        return None


def test_ui_translator():
    """测试 UI 翻译器"""
    print("\n=== 测试 UI 翻译器 ===")
    
    try:
        from app.core.ui_translator import get_translator
        
        translator = get_translator()
        
        # 测试平台翻译
        print("\n1. 测试平台翻译:")
        platform_meta = translator.translate_platform("douyin")
        print(f"  抖音 → {platform_meta}")
        
        # 测试风格翻译
        print("\n2. 测试风格翻译:")
        style_prompt = translator.translate_style("viral")
        print(f"  爆款 → {style_prompt[:50]}...")
        
        # 测试节奏翻译
        print("\n3. 测试节奏翻译:")
        pace_info = translator.translate_pace("fast")
        print(f"  快 → {pace_info}")
        
        # 测试构建初始 prompt
        print("\n4. 测试构建初始 prompt:")
        prompt = translator.build_initial_prompt(
            platform="douyin",
            style="viral",
            pace="fast",
            subtitle_density="standard",
            music_preference="emotional"
        )
        print(f"  Prompt 长度: {len(prompt)} 字符")
        print(f"  前 100 字符: {prompt[:100]}...")
        
        # 测试调整 prompt
        print("\n5. 测试调整 prompt:")
        adjustments = {"pace": "faster", "hook": "stronger"}
        new_prompt = translator.build_adjustment_prompt(prompt, adjustments)
        print(f"  调整后 Prompt 长度: {len(new_prompt)} 字符")
        
        print("\n✅ UI 翻译器测试通过")
        return True
        
    except Exception as e:
        print(f"❌ UI 翻译器测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试流程"""
    print("=" * 60)
    print("AutoCut Director - 产品级 API 测试")
    print("=" * 60)
    
    # 测试 UI 翻译器
    test_ui_translator()
    
    # 测试创建项目
    project_id = test_create_project()
    
    if not project_id:
        print("\n⚠️ 无法继续测试，因为项目创建失败")
        return
    
    # 测试获取项目状态
    completed = test_get_project_status(project_id)
    
    # 测试获取项目详情
    test_get_project(project_id)
    
    # 如果项目完成，测试调整
    if completed:
        new_version = test_adjust_project(project_id)
        
        if new_version:
            # 等待调整完成
            time.sleep(5)
            
            # 测试获取版本列表
            test_get_versions(project_id)
        
        # 测试导出
        export_id = test_create_export(project_id)
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
