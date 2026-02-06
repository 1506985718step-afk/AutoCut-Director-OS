"""
测试 Jobs API
"""
import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000"


def test_list_jobs():
    """测试列出所有 jobs"""
    print("\n" + "=" * 70)
    print("测试: GET /api/jobs/")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/jobs/")
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"总数: {data['total']}")
        print(f"\nJobs:")
        for job in data['jobs'][:5]:
            print(f"  - {job['job_id']}: {job['status']} ({job['progress']}%)")
    else:
        print(f"错误: {response.text}")


def test_get_job_status(job_id: str):
    """测试获取 job 状态"""
    print("\n" + "=" * 70)
    print(f"测试: GET /api/jobs/{job_id}")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}")
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nJob ID: {data['job_id']}")
        print(f"状态: {data['status']}")
        print(f"进度: {data['progress']}%")
        print(f"创建时间: {data['created_at']}")
        print(f"更新时间: {data['updated_at']}")
        
        # Artifacts
        print(f"\nArtifacts:")
        for category, files in data['artifacts'].items():
            print(f"  {category}: {len(files)} 个文件")
            for file in files[:3]:
                size_mb = file['size'] / (1024 * 1024)
                print(f"    - {file['name']} ({size_mb:.2f} MB)")
        
        # Trace 摘要
        if data['trace_summary']:
            trace = data['trace_summary']
            print(f"\nTrace 摘要:")
            print(f"  总动作: {trace['total_actions']}")
            print(f"  成功: {trace['successful']}")
            print(f"  失败: {trace['failed']}")
            print(f"  总耗时: {trace['total_time_ms']} ms")
    else:
        print(f"错误: {response.text}")


def test_get_job_artifacts(job_id: str):
    """测试获取 job artifacts"""
    print("\n" + "=" * 70)
    print(f"测试: GET /api/jobs/{job_id}/artifacts")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/artifacts")
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        for category, files in data.items():
            print(f"\n{category.upper()}: {len(files)} 个文件")
            for file in files:
                size_mb = file['size'] / (1024 * 1024)
                print(f"  - {file['name']}")
                print(f"    路径: {file['path']}")
                print(f"    大小: {size_mb:.2f} MB")
                print(f"    修改时间: {file['modified']}")
    else:
        print(f"错误: {response.text}")


def test_get_job_trace(job_id: str):
    """测试获取 job trace"""
    print("\n" + "=" * 70)
    print(f"测试: GET /api/jobs/{job_id}/trace")
    print("=" * 70)
    
    response = requests.get(f"{BASE_URL}/api/jobs/{job_id}/trace")
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n总动作: {data['total_actions']}")
        print(f"成功: {data['successful']}")
        print(f"失败: {data['failed']}")
        print(f"总耗时: {data['total_time_ms']} ms")
        
        print(f"\n动作列表:")
        for action in data['actions'][:5]:
            status = "✅" if action.get('ok') else "❌"
            print(f"  {status} {action['action']}: {action['detail']} ({action['took_ms']}ms)")
        
        if len(data['actions']) > 5:
            print(f"  ... 共 {len(data['actions'])} 个动作")
    else:
        print(f"错误: {response.text}")


def test_get_job_preview(job_id: str, quality: str = "480p"):
    """测试获取 job 预览"""
    print("\n" + "=" * 70)
    print(f"测试: GET /api/jobs/{job_id}/preview?quality={quality}")
    print("=" * 70)
    
    response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/preview",
        params={"quality": quality},
        stream=True
    )
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        # 保存预览文件
        output_file = f"test_preview_{quality}.mp4"
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = Path(output_file).stat().st_size / (1024 * 1024)
        print(f"\n✅ 预览视频已保存: {output_file}")
        print(f"   文件大小: {file_size:.2f} MB")
    else:
        print(f"错误: {response.text}")


def test_download_artifact(job_id: str, category: str, filename: str):
    """测试下载 artifact"""
    print("\n" + "=" * 70)
    print(f"测试: GET /api/jobs/{job_id}/download/{category}/{filename}")
    print("=" * 70)
    
    response = requests.get(
        f"{BASE_URL}/api/jobs/{job_id}/download/{category}/{filename}",
        stream=True
    )
    
    print(f"\n状态码: {response.status_code}")
    
    if response.status_code == 200:
        # 保存文件
        output_file = f"test_download_{filename}"
        
        with open(output_file, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        file_size = Path(output_file).stat().st_size / (1024 * 1024)
        print(f"\n✅ 文件已下载: {output_file}")
        print(f"   文件大小: {file_size:.2f} MB")
    else:
        print(f"错误: {response.text}")


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - Jobs API 测试\n")
    
    # 测试列出 jobs
    test_list_jobs()
    
    # 获取第一个 job_id 进行测试
    response = requests.get(f"{BASE_URL}/api/jobs/")
    if response.status_code == 200:
        jobs = response.json()['jobs']
        if jobs:
            job_id = jobs[0]['job_id']
            
            print(f"\n使用 Job ID: {job_id} 进行测试")
            
            # 测试各个端点
            test_get_job_status(job_id)
            test_get_job_artifacts(job_id)
            test_get_job_trace(job_id)
            
            # 测试预览（需要有输出视频）
            # test_get_job_preview(job_id, "480p")
            
            # 测试下载（需要指定实际文件）
            # test_download_artifact(job_id, "output", "scenes.json")
        else:
            print("\n⚠️  没有可用的 jobs 进行测试")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
