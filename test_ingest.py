"""
测试 Ingest 功能
"""
from pathlib import Path
from app.tools.media_ingest import MediaIngest, ingest_video_simple


def test_ingest_basic():
    """测试基本 Ingest 功能"""
    print("\n" + "=" * 70)
    print("测试 Ingest - 基本功能")
    print("=" * 70)
    
    # 创建测试视频路径（假设）
    test_video = "D:/Footage/test_input.mp4"
    
    if not Path(test_video).exists():
        print(f"\n⚠️  测试视频不存在: {test_video}")
        print("   请提供实际的视频文件路径进行测试")
        return
    
    # 执行 Ingest
    result = ingest_video_simple(test_video, "test_job_001")
    
    print("\n✅ Ingest 测试完成")
    print("\n结果:")
    for key, value in result.items():
        if key != "scene_detection_info":
            print(f"  {key}: {value}")


def test_ingest_with_manager():
    """测试使用 MediaIngest 管理器"""
    print("\n" + "=" * 70)
    print("测试 Ingest - 使用管理器")
    print("=" * 70)
    
    ingest = MediaIngest(job_dir="jobs")
    
    # 创建 job
    job_path = ingest.create_job("test_job_002")
    print(f"\n✅ Job 目录创建: {job_path}")
    
    # 检查子目录
    assert (job_path / "input").exists()
    assert (job_path / "output").exists()
    assert (job_path / "temp").exists()
    
    print("✅ 子目录结构正确")


def test_audio_extraction():
    """测试音频提取"""
    print("\n" + "=" * 70)
    print("测试 Ingest - 音频提取")
    print("=" * 70)
    
    test_video = "D:/Footage/test_input.mp4"
    
    if not Path(test_video).exists():
        print(f"\n⚠️  测试视频不存在: {test_video}")
        print("   跳过音频提取测试")
        return
    
    ingest = MediaIngest()
    
    try:
        # 提取音频
        audio_path = ingest.extract_audio(
            test_video,
            output_path="jobs/test_audio.wav",
            format="wav",
            sample_rate=16000
        )
        
        print(f"\n✅ 音频提取成功: {audio_path}")
        
        # 检查文件
        if Path(audio_path).exists():
            file_size = Path(audio_path).stat().st_size / (1024 * 1024)
            print(f"   文件大小: {file_size:.2f} MB")
        
    except Exception as e:
        print(f"\n❌ 音频提取失败: {e}")


def test_scene_detection_prompt():
    """测试场景切点检测提示"""
    print("\n" + "=" * 70)
    print("测试 Ingest - 场景切点检测提示")
    print("=" * 70)
    
    ingest = MediaIngest()
    
    info = ingest.prompt_scene_detection("D:/Footage/test_input.mp4")
    
    print("\n✅ 场景切点检测提示生成")
    print(f"\n推荐格式: {info['recommended']}")
    print(f"支持格式: {', '.join(info['export_formats'])}")


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - Ingest 功能测试\n")
    
    # 运行测试
    try:
        test_ingest_with_manager()
        test_scene_detection_prompt()
        test_audio_extraction()
        test_ingest_basic()
        
        print("\n" + "=" * 70)
        print("✅ 所有测试完成")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
