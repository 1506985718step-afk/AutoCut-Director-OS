"""
AutoCut Director - 快速启动脚本

最简单的使用方式，适合快速测试和演示
"""
import asyncio
from pathlib import Path
from datetime import datetime
from run_pipeline import Pipeline
from app.tools.media_ingest import MediaIngest


async def quick_start():
    """快速启动流水线"""
    
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║          🎬 AutoCut Director - 快速启动                          ║
║                                                                  ║
║          AI 驱动的自动视频剪辑系统                                ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    # 获取用户输入
    print("请提供以下信息（或按 Enter 使用默认值）:\n")
    
    # 视频文件路径
    default_video = "D:/Footage/input.mp4"
    video_path = input(f"视频文件路径 [{default_video}]: ").strip()
    if not video_path:
        video_path = default_video
    
    # 检查文件是否存在
    if not Path(video_path).exists():
        print(f"\n⚠️  警告: 文件不存在: {video_path}")
        print("   将继续执行，但可能失败")
        confirm = input("\n是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            print("已取消")
            return False
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 阶段 0: Ingest - 素材预处理
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n" + "=" * 70)
    print("0️⃣  Ingest - 素材预处理")
    print("=" * 70)
    
    # 创建 job
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ingest = MediaIngest(job_dir="jobs")
    
    print(f"\n📁 创建 Job: {job_id}")
    
    # Ingest 视频
    ingest_result = ingest.ingest_video(
        video_path=video_path,
        job_id=job_id,
        extract_audio=True,
        wait_for_scene_detection=False
    )
    
    job_path = Path(ingest_result["job_path"])
    video_path = ingest_result["video_path"]
    audio_path = ingest_result.get("audio_path")
    
    # 等待用户提供 EDL
    print("\n" + "=" * 70)
    print("⏸️  等待 EDL/XML 文件")
    print("=" * 70)
    print("\n请完成以下操作后继续:")
    print("  1. 在 DaVinci Resolve 中完成场景切点检测")
    print("  2. 导出 EDL 或 XML 文件")
    print(f"  3. 将文件保存到: {job_path / 'input'}")
    
    input("\n按 Enter 继续...")
    
    # 查找 EDL 文件
    edl_files = list((job_path / "input").glob("*.edl"))
    xml_files = list((job_path / "input").glob("*.xml"))
    
    if edl_files:
        edl_path = edl_files[0]
        print(f"\n✅ 发现 EDL 文件: {edl_path.name}")
    elif xml_files:
        edl_path = xml_files[0]
        print(f"\n✅ 发现 XML 文件: {edl_path.name}")
    else:
        print("\n❌ 错误: 未找到 EDL/XML 文件")
        print(f"   请确保文件已保存到: {job_path / 'input'}")
        return False
    
    # 输出路径
    output_path = job_path / "output" / "final.mp4"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 剪辑风格
    print("\n选择剪辑风格:")
    print("  1. 抖音爆款（节奏快、文字多、强调关键词）")
    print("  2. B站知识区（节奏适中、字幕完整、强调知识点）")
    print("  3. YouTube Vlog（自然流畅、保留情感、适度剪辑）")
    print("  4. 快手热门（接地气、情感强、节奏紧凑）")
    print("  5. 自定义")
    
    style_choice = input("\n请选择 [1]: ").strip()
    if not style_choice:
        style_choice = "1"
    
    style_map = {
        "1": "抖音爆款风格：节奏快、文字多、强调关键词",
        "2": "B站知识区风格：节奏适中、字幕完整、强调知识点",
        "3": "YouTube Vlog 风格：自然流畅、保留情感、适度剪辑",
        "4": "快手热门风格：接地气、情感强、节奏紧凑"
    }
    
    if style_choice == "5":
        style = input("请输入自定义风格描述: ").strip()
    else:
        style = style_map.get(style_choice, style_map["1"])
    
    print(f"\n✅ 已选择: {style}")
    
    # 确认配置
    print("\n" + "=" * 70)
    print("配置确认:")
    print("=" * 70)
    print(f"  Job ID: {job_id}")
    print(f"  Job 目录: {job_path}")
    print(f"  EDL 文件: {edl_path}")
    print(f"  视频文件: {video_path}")
    print(f"  音频文件: {audio_path}")
    print(f"  输出文件: {output_path}")
    print(f"  剪辑风格: {style}")
    print("=" * 70)
    
    confirm = input("\n开始执行？(y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消")
        return False
    
    # 配置流水线
    config = {
        "job_id": job_id,
        "edl_path": str(edl_path),
        "audio_path": audio_path if audio_path else video_path,
        "primary_clip_path": video_path,
        "fps": 30,
        "language": "zh",
        "whisper_model": "base",
        "style": style,
        "output_path": str(output_path),
        "output_dir": str(job_path / "output")
    }
    
    # 运行流水线
    pipeline = Pipeline(config)
    success = await pipeline.run()
    
    if success:
        print("\n" + "🎉" * 35)
        print("\n恭喜！视频剪辑完成！")
        print("\n下一步:")
        print("  1. 在 DaVinci Resolve 中查看时间线")
        print("  2. 调整字幕样式（如需要）")
        print("  3. 渲染导出最终视频")
        print("\n" + "🎉" * 35)
    
    return success


if __name__ == "__main__":
    try:
        asyncio.run(quick_start())
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
