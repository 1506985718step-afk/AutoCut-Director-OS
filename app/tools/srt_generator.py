"""SRT 字幕生成工具 - 从 transcript 或 DSL 生成 SRT 文件"""
from pathlib import Path
from typing import List, Dict


def seconds_to_srt_time(seconds: float) -> str:
    """
    将秒数转换为 SRT 时间格式
    
    格式: HH:MM:SS,mmm
    例如: 00:00:01,500
    
    Args:
        seconds: 秒数（可以是小数）
    
    Returns:
        SRT 时间格式字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def generate_srt_entry(index: int, text: str, start_sec: float, end_sec: float) -> str:
    """
    生成单个 SRT 字幕条目
    
    格式：
    1
    00:00:01,000 --> 00:00:03,000
    字幕内容
    
    Args:
        index: 字幕序号（从 1 开始）
        text: 字幕文本
        start_sec: 开始时间（秒）
        end_sec: 结束时间（秒）
    
    Returns:
        SRT 条目字符串
    """
    start_time = seconds_to_srt_time(start_sec)
    end_time = seconds_to_srt_time(end_sec)
    
    return f"{index}\n{start_time} --> {end_time}\n{text}\n\n"


def transcript_to_srt(transcript_segments: List[Dict], output_path: str) -> str:
    """
    将 transcript.json 转换为 SRT 文件
    
    Args:
        transcript_segments: transcript.json 中的 segments 列表
        output_path: 输出 SRT 文件路径
    
    Returns:
        输出文件路径
    
    Example:
        >>> segments = [
        ...     {"start": 0.0, "end": 2.8, "text": "90%的人第一步就弹错了"},
        ...     {"start": 2.8, "end": 5.5, "text": "今天教你正确方法"}
        ... ]
        >>> transcript_to_srt(segments, "output.srt")
    """
    srt_content = ""
    
    for i, segment in enumerate(transcript_segments, start=1):
        srt_content += generate_srt_entry(
            index=i,
            text=segment["text"],
            start_sec=segment["start"],
            end_sec=segment["end"]
        )
    
    # 写入文件
    Path(output_path).write_text(srt_content, encoding='utf-8')
    
    print(f"✓ SRT 文件已生成: {output_path}")
    print(f"  共 {len(transcript_segments)} 段字幕")
    
    return output_path


def overlay_text_to_srt(text_items: List[Dict], fps: float, output_path: str) -> str:
    """
    将 DSL 中的 overlay_text 转换为 SRT 文件
    
    Args:
        text_items: 文字叠加列表，格式：[
            {
                "content": "第一步就错了",
                "start_frame": 30,
                "duration_frames": 60
            },
            ...
        ]
        fps: 帧率
        output_path: 输出 SRT 文件路径
    
    Returns:
        输出文件路径
    
    Example:
        >>> text_items = [
        ...     {"content": "第一步就错了", "start_frame": 30, "duration_frames": 60},
        ...     {"content": "90%的人都不知道", "start_frame": 120, "duration_frames": 90}
        ... ]
        >>> overlay_text_to_srt(text_items, fps=30, output_path="overlay.srt")
    """
    srt_content = ""
    
    for i, item in enumerate(text_items, start=1):
        start_sec = item['start_frame'] / fps
        duration_sec = item['duration_frames'] / fps
        end_sec = start_sec + duration_sec
        
        srt_content += generate_srt_entry(
            index=i,
            text=item['content'],
            start_sec=start_sec,
            end_sec=end_sec
        )
    
    # 写入文件
    Path(output_path).write_text(srt_content, encoding='utf-8')
    
    print(f"✓ SRT 文件已生成: {output_path}")
    print(f"  共 {len(text_items)} 个文字叠加")
    
    return output_path


def dsl_to_srt_files(dsl: Dict, fps: float, output_dir: str = ".") -> Dict[str, str]:
    """
    从 DSL 生成所有需要的 SRT 文件
    
    生成两个文件：
    1. subtitles.srt - 完整字幕（从 transcript）
    2. overlay.srt - 文字叠加（从 timeline 中的 overlay_text）
    
    Args:
        dsl: editing_dsl.v1.json 数据
        fps: 帧率
        output_dir: 输出目录
    
    Returns:
        生成的文件路径字典 {"subtitles": "...", "overlay": "..."}
    
    Example:
        >>> import json
        >>> dsl = json.load(open("editing_dsl.v1.json"))
        >>> files = dsl_to_srt_files(dsl, fps=30, output_dir="output")
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)
    
    result = {}
    
    # 1. 生成字幕 SRT（如果有 transcript）
    # 注意：DSL 中通常不包含完整的 transcript，需要单独传入
    # 这里只处理 overlay_text
    
    # 2. 生成文字叠加 SRT
    timeline = dsl.get("editing_plan", {}).get("timeline", [])
    text_items = []
    
    for item in timeline:
        if "overlay_text" in item and item["overlay_text"]:
            text_items.append({
                "content": item["overlay_text"],
                "start_frame": item["trim_frames"][0],
                "duration_frames": item["trim_frames"][1] - item["trim_frames"][0]
            })
    
    if text_items:
        overlay_path = str(output_dir / "overlay.srt")
        overlay_text_to_srt(text_items, fps, overlay_path)
        result["overlay"] = overlay_path
    
    return result


def merge_srt_files(srt_files: List[str], output_path: str) -> str:
    """
    合并多个 SRT 文件
    
    Args:
        srt_files: SRT 文件路径列表
        output_path: 输出文件路径
    
    Returns:
        输出文件路径
    """
    all_entries = []
    
    for srt_file in srt_files:
        content = Path(srt_file).read_text(encoding='utf-8')
        # 简单解析（假设格式正确）
        entries = content.strip().split('\n\n')
        all_entries.extend(entries)
    
    # 重新编号
    merged_content = ""
    for i, entry in enumerate(all_entries, start=1):
        lines = entry.split('\n')
        if len(lines) >= 3:
            # 替换序号
            lines[0] = str(i)
            merged_content += '\n'.join(lines) + '\n\n'
    
    Path(output_path).write_text(merged_content, encoding='utf-8')
    
    print(f"✓ 合并完成: {output_path}")
    print(f"  共 {len(all_entries)} 段字幕")
    
    return output_path


# 命令行工具
if __name__ == "__main__":
    import sys
    import json
    
    if len(sys.argv) < 3:
        print("用法:")
        print("  python srt_generator.py transcript <transcript.json> <output.srt>")
        print("  python srt_generator.py dsl <editing_dsl.json> <fps> <output_dir>")
        sys.exit(1)
    
    mode = sys.argv[1]
    
    if mode == "transcript":
        # 从 transcript 生成 SRT
        transcript_path = sys.argv[2]
        output_path = sys.argv[3]
        
        with open(transcript_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        transcript_to_srt(data["segments"], output_path)
    
    elif mode == "dsl":
        # 从 DSL 生成 SRT
        dsl_path = sys.argv[2]
        fps = float(sys.argv[3])
        output_dir = sys.argv[4] if len(sys.argv) > 4 else "."
        
        with open(dsl_path, 'r', encoding='utf-8') as f:
            dsl = json.load(f)
        
        files = dsl_to_srt_files(dsl, fps, output_dir)
        
        print("\n生成的文件:")
        for key, path in files.items():
            print(f"  {key}: {path}")
    
    else:
        print(f"未知模式: {mode}")
        sys.exit(1)
