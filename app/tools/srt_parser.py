"""SRT 字幕解析器"""
import re


def parse_srt_to_transcript(srt_path: str) -> dict:
    """
    解析 SRT 字幕文件为 transcript.json
    
    SRT 格式:
    1
    00:00:00,500 --> 00:00:02,000
    Hello world
    
    Args:
        srt_path: SRT 文件路径
        
    Returns:
        transcript.json 格式
    """
    with open(srt_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 分割字幕块
    blocks = re.split(r'\n\n+', content.strip())
    
    segments = []
    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue
        
        # 解析时间码
        timecode_line = lines[1]
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', timecode_line)
        
        if match:
            start_h, start_m, start_s, start_ms = map(int, match.groups()[:4])
            end_h, end_m, end_s, end_ms = map(int, match.groups()[4:])
            
            start = start_h * 3600 + start_m * 60 + start_s + start_ms / 1000
            end = end_h * 3600 + end_m * 60 + end_s + end_ms / 1000
            
            # 文本内容
            text = '\n'.join(lines[2:])
            
            segments.append({
                "start": start,
                "end": end,
                "text": text
            })
    
    return {
        "segments": segments,
        "source": srt_path,
        "format": "SRT"
    }
