"""时间码工具 - TC <-> Frame 转换"""
from typing import Union


class Timecode:
    """时间码处理类"""
    
    def __init__(self, fps: float = 25.0):
        self.fps = fps
    
    def tc_to_frames(self, timecode: str) -> int:
        """
        时间码转帧数 (HH:MM:SS:FF)
        
        Args:
            timecode: 时间码字符串，格式 "01:23:45:12"
            
        Returns:
            帧数
        """
        parts = timecode.split(":")
        if len(parts) != 4:
            raise ValueError(f"无效的时间码格式: {timecode}")
        
        hours, minutes, seconds, frames = map(int, parts)
        
        total_frames = (
            hours * 3600 * self.fps +
            minutes * 60 * self.fps +
            seconds * self.fps +
            frames
        )
        
        return int(total_frames)
    
    def frames_to_tc(self, frames: int) -> str:
        """
        帧数转时间码
        
        Args:
            frames: 帧数
            
        Returns:
            时间码字符串 "HH:MM:SS:FF"
        """
        total_seconds = frames / self.fps
        
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frame = int(frames % self.fps)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frame:02d}"
    
    def tc_to_seconds(self, timecode: str) -> float:
        """时间码转秒"""
        frames = self.tc_to_frames(timecode)
        return frames / self.fps
    
    def seconds_to_tc(self, seconds: float) -> str:
        """秒转时间码"""
        frames = int(seconds * self.fps)
        return self.frames_to_tc(frames)
    
    def seconds_to_frames(self, seconds: float) -> int:
        """秒转帧数"""
        return int(seconds * self.fps)
    
    def frames_to_seconds(self, frames: int) -> float:
        """帧数转秒"""
        return frames / self.fps


# 便捷函数
def tc_to_frames(timecode: str, fps: float = 25.0) -> int:
    """时间码转帧数"""
    return Timecode(fps).tc_to_frames(timecode)


def frames_to_tc(frames: int, fps: float = 25.0) -> str:
    """帧数转时间码"""
    return Timecode(fps).frames_to_tc(frames)


def tc_to_seconds(timecode: str, fps: float = 25.0) -> float:
    """时间码转秒"""
    return Timecode(fps).tc_to_seconds(timecode)


def seconds_to_tc(seconds: float, fps: float = 25.0) -> str:
    """秒转时间码"""
    return Timecode(fps).seconds_to_tc(seconds)
