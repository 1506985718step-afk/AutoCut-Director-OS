"""Stage A': FCPXML -> scenes.json 解析器（后续增强）"""
import xml.etree.ElementTree as ET
from pathlib import Path


def parse_xml_to_scenes(xml_path: str) -> dict:
    """
    解析 Final Cut Pro XML 为 scenes.json
    
    支持 FCPXML 1.8+ 格式
    
    Args:
        xml_path: FCPXML 文件路径
        
    Returns:
        scenes.json 格式的字典
    """
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    scenes = []
    scene_id = 1
    
    # 获取帧率
    fps = 25.0
    sequence = root.find(".//sequence")
    if sequence is not None:
        rate = sequence.find(".//rate")
        if rate is not None:
            timebase = rate.find("timebase")
            if timebase is not None:
                fps = float(timebase.text)
    
    # 查找所有 clip 元素
    for clip in root.iter("clip"):
        try:
            # 获取时间信息
            start = float(clip.get("start", 0))
            duration = float(clip.get("duration", 0))
            offset = float(clip.get("offset", 0))
            
            name = clip.get("name", f"Scene {scene_id}")
            
            # 转换为秒（如果是帧数）
            if start > 1000:  # 可能是帧数
                start = start / fps
                duration = duration / fps
            
            scenes.append({
                "id": scene_id,
                "name": name,
                "start": start,
                "end": start + duration,
                "duration": duration,
                "offset": offset,
                "type": "clip"
            })
            scene_id += 1
            
        except (ValueError, TypeError):
            continue
    
    return {
        "scenes": scenes,
        "total_scenes": len(scenes),
        "fps": fps,
        "source": xml_path,
        "format": "FCPXML"
    }
