"""
媒体素材 Ingest 工具 - 预处理素材文件

功能：
1. 从视频提取音频（ffmpeg）
2. 提示用户在 Resolve 中做场景切点检测
3. 统一管理 job 目录
"""
import subprocess
from pathlib import Path
from typing import Optional, Dict
import shutil


class MediaIngest:
    """媒体素材 Ingest 管理器"""
    
    def __init__(self, job_dir: str = "jobs"):
        """
        初始化 Ingest 管理器
        
        Args:
            job_dir: job 根目录
        """
        self.job_dir = Path(job_dir)
        self.job_dir.mkdir(exist_ok=True)
    
    def create_job(self, job_id: str) -> Path:
        """
        创建新的 job 目录
        
        Args:
            job_id: job 唯一标识
        
        Returns:
            job 目录路径
        """
        job_path = self.job_dir / job_id
        job_path.mkdir(exist_ok=True)
        
        # 创建子目录
        (job_path / "input").mkdir(exist_ok=True)
        (job_path / "output").mkdir(exist_ok=True)
        (job_path / "temp").mkdir(exist_ok=True)
        
        return job_path
    
    def extract_audio(
        self, 
        video_path: str, 
        output_path: Optional[str] = None,
        format: str = "wav",
        sample_rate: int = 16000
    ) -> str:
        """
        从视频提取音频（使用 ffmpeg）
        
        Args:
            video_path: 输入视频路径
            output_path: 输出音频路径（可选）
            format: 音频格式（wav/mp3/aac）
            sample_rate: 采样率（Hz）
        
        Returns:
            输出音频文件路径
        
        Raises:
            RuntimeError: ffmpeg 执行失败
        """
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 自动生成输出路径
        if output_path is None:
            output_path = video_path.with_suffix(f".{format}")
        
        output_path = Path(output_path)
        
        # 构建 ffmpeg 命令
        cmd = [
            "ffmpeg",
            "-i", str(video_path),
            "-vn",  # 不处理视频
            "-acodec", "pcm_s16le" if format == "wav" else "libmp3lame",
            "-ar", str(sample_rate),
            "-ac", "1",  # 单声道
            "-y",  # 覆盖已存在文件
            str(output_path)
        ]
        
        print(f"🎵 提取音频: {video_path.name} → {output_path.name}")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            if output_path.exists():
                file_size = output_path.stat().st_size / (1024 * 1024)
                print(f"✅ 音频提取成功: {output_path} ({file_size:.2f} MB)")
                return str(output_path)
            else:
                raise RuntimeError("音频文件未生成")
                
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"ffmpeg 执行失败: {e.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                "ffmpeg 未安装。请安装 ffmpeg:\n"
                "  Windows: choco install ffmpeg\n"
                "  或下载: https://ffmpeg.org/download.html"
            )
    
    def prompt_scene_detection(self, video_path: str) -> Dict[str, str]:
        """
        提示用户在 Resolve 中做场景切点检测
        
        Args:
            video_path: 视频文件路径
        
        Returns:
            提示信息字典
        """
        print("\n" + "=" * 70)
        print("📹 场景切点检测 - 需要在 DaVinci Resolve 中操作")
        print("=" * 70)
        
        print(f"\n视频文件: {video_path}")
        
        print("\n请按以下步骤操作：")
        print("\n1️⃣  在 DaVinci Resolve 中打开项目")
        print("2️⃣  导入视频文件到媒体池")
        print("3️⃣  右键视频 → Scene Cut Detection（场景切点检测）")
        print("4️⃣  调整检测参数（建议使用默认值）")
        print("5️⃣  点击 'Detect Scenes' 开始检测")
        print("6️⃣  检测完成后，将视频拖到时间线")
        print("7️⃣  导出 EDL: File → Export → Timeline → EDL")
        print("     或导出 XML: File → Export → Timeline → Final Cut Pro XML")
        
        print("\n💡 提示:")
        print("   - EDL 格式更简单，推荐使用")
        print("   - 导出时选择 'CMX 3600' 格式")
        print("   - 保存到 job 目录的 input 文件夹")
        
        return {
            "video_path": video_path,
            "instructions": "请在 Resolve 中完成场景切点检测并导出 EDL/XML",
            "export_formats": ["EDL (CMX 3600)", "Final Cut Pro XML"],
            "recommended": "EDL"
        }
    
    def wait_for_edl(self, job_path: Path, timeout: int = 300) -> Optional[Path]:
        """
        等待用户导出 EDL/XML 文件
        
        Args:
            job_path: job 目录路径
            timeout: 超时时间（秒）
        
        Returns:
            EDL/XML 文件路径，如果超时则返回 None
        """
        import time
        
        input_dir = job_path / "input"
        
        print(f"\n⏳ 等待 EDL/XML 文件...")
        print(f"   请将导出的文件保存到: {input_dir}")
        print(f"   (超时时间: {timeout} 秒)")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # 检查 EDL 文件
            edl_files = list(input_dir.glob("*.edl"))
            if edl_files:
                print(f"\n✅ 发现 EDL 文件: {edl_files[0].name}")
                return edl_files[0]
            
            # 检查 XML 文件
            xml_files = list(input_dir.glob("*.xml"))
            if xml_files:
                print(f"\n✅ 发现 XML 文件: {xml_files[0].name}")
                return xml_files[0]
            
            time.sleep(2)
        
        print(f"\n⏰ 超时: 未检测到 EDL/XML 文件")
        return None
    
    def ingest_video(
        self, 
        video_path: str, 
        job_id: str,
        extract_audio: bool = True,
        wait_for_scene_detection: bool = False
    ) -> Dict[str, str]:
        """
        完整的视频 Ingest 流程
        
        Args:
            video_path: 输入视频路径
            job_id: job 唯一标识
            extract_audio: 是否提取音频
            wait_for_scene_detection: 是否等待场景切点检测
        
        Returns:
            Ingest 结果字典 {
                "job_id": "...",
                "job_path": "...",
                "video_path": "...",
                "audio_path": "...",
                "edl_path": "..." (可选)
            }
        """
        print("\n" + "🎬" * 35)
        print("媒体素材 Ingest - 预处理开始")
        print("🎬" * 35)
        
        # 创建 job 目录
        job_path = self.create_job(job_id)
        print(f"\n📁 Job 目录: {job_path}")
        
        # 复制视频到 job 目录
        video_src = Path(video_path)
        video_dst = job_path / "input" / video_src.name
        
        if not video_dst.exists():
            print(f"\n📹 复制视频文件...")
            shutil.copy2(video_src, video_dst)
            print(f"✅ 已复制: {video_dst}")
        else:
            print(f"\n📹 视频文件已存在: {video_dst}")
        
        result = {
            "job_id": job_id,
            "job_path": str(job_path),
            "video_path": str(video_dst)
        }
        
        # 提取音频
        if extract_audio:
            audio_path = job_path / "temp" / f"{video_src.stem}.wav"
            try:
                audio_output = self.extract_audio(
                    str(video_dst),
                    str(audio_path)
                )
                result["audio_path"] = audio_output
            except Exception as e:
                print(f"⚠️  音频提取失败: {e}")
                result["audio_path"] = None
        
        # 场景切点检测提示
        scene_info = self.prompt_scene_detection(str(video_dst))
        result["scene_detection_info"] = scene_info
        
        # 等待 EDL/XML
        if wait_for_scene_detection:
            edl_path = self.wait_for_edl(job_path)
            if edl_path:
                result["edl_path"] = str(edl_path)
            else:
                result["edl_path"] = None
                print("\n⚠️  未检测到 EDL/XML 文件，请手动导出后继续")
        else:
            print("\n💡 提示: 完成场景切点检测后，请将 EDL/XML 保存到:")
            print(f"   {job_path / 'input'}")
            result["edl_path"] = None
        
        print("\n" + "=" * 70)
        print("✅ Ingest 完成")
        print("=" * 70)
        
        return result


def ingest_video_simple(video_path: str, job_id: str) -> Dict[str, str]:
    """
    简化的 Ingest 函数（便捷接口）
    
    Args:
        video_path: 视频文件路径
        job_id: job 标识
    
    Returns:
        Ingest 结果
    """
    ingest = MediaIngest()
    return ingest.ingest_video(video_path, job_id, extract_audio=True)


# 命令行工具
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("用法: python media_ingest.py <video_path> <job_id>")
        print("示例: python media_ingest.py input.mp4 job_001")
        sys.exit(1)
    
    video_path = sys.argv[1]
    job_id = sys.argv[2]
    
    result = ingest_video_simple(video_path, job_id)
    
    print("\n📊 Ingest 结果:")
    for key, value in result.items():
        print(f"   {key}: {value}")
