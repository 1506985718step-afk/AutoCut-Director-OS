"""Stage A (MVP): EDL -> scenes.json 解析器（脚手架版本）"""
import re
from pathlib import Path

# 时间码正则：匹配 HH:MM:SS:FF 格式
TC_RE = re.compile(r"(\d{2}:\d{2}:\d{2}:\d{2})")


def tc_to_frames(tc: str, fps: int) -> int:
    """
    时间码转帧数
    
    Args:
        tc: 时间码字符串 "HH:MM:SS:FF"
        fps: 帧率
        
    Returns:
        帧数
    """
    hh, mm, ss, ff = [int(x) for x in tc.split(":")]
    return ((hh * 3600 + mm * 60 + ss) * fps) + ff


def parse_edl_to_scenes(edl_path: str, fps: int, primary_clip_path: str) -> dict:
    """
    解析 EDL 文件为 scenes.json (MVP v1 协议)
    
    EDL 格式示例:
    001  AX  V  C  01:00:00:00 01:00:05:00 00:00:00:00 00:00:05:00
    
    我们使用 record in/out (第3、4个时间码) 作为 timeline 切点依据
    
    Args:
        edl_path: EDL 文件路径
        fps: 帧率
        primary_clip_path: 主素材路径
        
    Returns:
        scenes.json 格式的字典 (符合 scenes.v1 协议)
    """
    text = Path(edl_path).read_text(encoding="utf-8", errors="ignore").splitlines()
    scenes = []
    scene_idx = 1
    
    # EDL 每行常见格式包含 source in/out / record in/out
    # 我们用 record in/out 当 timeline 切点依据
    for line in text:
        tcs = TC_RE.findall(line)
        
        # 需要至少 4 个时间码：source_in, source_out, record_in, record_out
        if len(tcs) >= 4:
            rec_in, rec_out = tcs[2], tcs[3]
            start_f = tc_to_frames(rec_in, fps)
            end_f = tc_to_frames(rec_out, fps)
            
            scenes.append({
                "scene_id": f"S{scene_idx:04d}",
                "start_tc": rec_in,
                "end_tc": rec_out,
                "start_frame": start_f,
                "end_frame": end_f
            })
            scene_idx += 1
    
    return {
        "meta": {
            "schema": "scenes.v1",
            "fps": fps,
            "source": "davinci/edl"
        },
        "media": {
            "primary_clip_path": primary_clip_path
        },
        "scenes": scenes
    }
