"""
BGM 素材库管理器 - 本地音乐素材管理
"""
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class BGMMetadata:
    """BGM 元数据"""
    id: str
    path: str
    bpm: int
    mood: str
    energy: str  # low, medium, high
    usage: List[str]  # story, teaching, vlog, product, etc.
    copyright: str  # royalty_free, licensed, custom
    duration_sec: Optional[float] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BGMMetadata':
        """从字典创建"""
        return cls(**data)


class BGMLibrary:
    """
    BGM 素材库管理器
    
    功能：
    1. 扫描本地 BGM 目录
    2. 生成/加载元数据
    3. 根据条件搜索 BGM
    4. 为 LLM 提供素材列表
    """
    
    def __init__(self, library_root: str = "bgm_library"):
        """
        初始化 BGM 库
        
        Args:
            library_root: BGM 库根目录
        """
        self.library_root = Path(library_root)
        self.metadata_cache: Dict[str, BGMMetadata] = {}
        
        # 确保目录存在
        self.library_root.mkdir(parents=True, exist_ok=True)
    
    def scan_library(self, auto_generate_metadata: bool = True) -> List[BGMMetadata]:
        """
        扫描 BGM 库，加载所有元数据
        
        Args:
            auto_generate_metadata: 如果没有 metadata.json，是否自动生成
        
        Returns:
            BGM 元数据列表
        """
        self.metadata_cache.clear()
        
        # 支持的音频格式
        audio_extensions = {'.mp3', '.wav', '.m4a', '.aac', '.flac'}
        
        # 遍历所有子目录
        for audio_file in self.library_root.rglob('*'):
            if audio_file.suffix.lower() not in audio_extensions:
                continue
            
            # 查找对应的 metadata.json
            metadata_file = audio_file.with_suffix('.json')
            
            if metadata_file.exists():
                # 加载现有元数据
                try:
                    metadata = self._load_metadata(metadata_file)
                    self.metadata_cache[metadata.id] = metadata
                except Exception as e:
                    print(f"⚠️ 加载元数据失败: {metadata_file}, {e}")
            
            elif auto_generate_metadata:
                # 自动生成元数据
                try:
                    metadata = self._generate_metadata(audio_file)
                    self._save_metadata(metadata, metadata_file)
                    self.metadata_cache[metadata.id] = metadata
                    print(f"✓ 自动生成元数据: {metadata_file}")
                except Exception as e:
                    print(f"⚠️ 生成元数据失败: {audio_file}, {e}")
        
        print(f"\n✓ 扫描完成，共 {len(self.metadata_cache)} 首 BGM")
        return list(self.metadata_cache.values())
    
    def _load_metadata(self, metadata_file: Path) -> BGMMetadata:
        """加载元数据文件"""
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return BGMMetadata.from_dict(data)
    
    def _save_metadata(self, metadata: BGMMetadata, metadata_file: Path):
        """保存元数据文件"""
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata.to_dict(), f, indent=2, ensure_ascii=False)
    
    def _generate_metadata(self, audio_file: Path) -> BGMMetadata:
        """
        自动生成元数据（基于文件名和目录结构）
        
        文件名格式建议: {mood}_{bpm}bpm.mp3
        例如: calm_090bpm.mp3, emo_120bpm.mp3
        """
        # 从目录名推断 mood
        mood = audio_file.parent.name
        if mood == self.library_root.name:
            mood = "general"
        
        # 从文件名提取信息
        filename = audio_file.stem
        parts = filename.split('_')
        
        # 尝试提取 BPM
        bpm = 120  # 默认值
        for part in parts:
            if 'bpm' in part.lower():
                try:
                    bpm = int(part.lower().replace('bpm', ''))
                except:
                    pass
        
        # 根据 BPM 推断 energy
        if bpm < 100:
            energy = "low"
        elif bpm < 130:
            energy = "medium"
        else:
            energy = "high"
        
        # 生成 ID
        bgm_id = f"{mood}_{bpm:03d}_{audio_file.stem[:10]}"
        
        # 相对路径（相对于当前工作目录）
        try:
            relative_path = str(audio_file.relative_to(Path.cwd()))
        except ValueError:
            # 如果无法计算相对路径，使用绝对路径
            relative_path = str(audio_file.absolute())
        
        # 根据 mood 推断 usage
        usage_map = {
            "calm": ["teaching", "meditation", "background"],
            "emotional": ["story", "drama", "touching"],
            "fast": ["action", "sports", "energetic"],
            "suspense": ["thriller", "mystery", "tension"],
            "happy": ["vlog", "celebration", "upbeat"],
            "sad": ["drama", "emotional", "reflective"]
        }
        usage = usage_map.get(mood, ["general"])
        
        return BGMMetadata(
            id=bgm_id,
            path=relative_path,
            bpm=bpm,
            mood=mood,
            energy=energy,
            usage=usage,
            copyright="royalty_free",  # 默认免版权
            tags=[mood, energy, f"{bpm}bpm"]
        )
    
    def search(
        self,
        mood: Optional[str] = None,
        energy: Optional[str] = None,
        bpm_range: Optional[tuple] = None,
        usage: Optional[str] = None
    ) -> List[BGMMetadata]:
        """
        搜索 BGM
        
        Args:
            mood: 情绪（calm, emotional, fast, suspense, etc.）
            energy: 能量级别（low, medium, high）
            bpm_range: BPM 范围，例如 (90, 120)
            usage: 用途（story, teaching, vlog, etc.）
        
        Returns:
            匹配的 BGM 列表
        """
        results = list(self.metadata_cache.values())
        
        if mood:
            results = [bgm for bgm in results if bgm.mood == mood]
        
        if energy:
            results = [bgm for bgm in results if bgm.energy == energy]
        
        if bpm_range:
            min_bpm, max_bpm = bpm_range
            results = [bgm for bgm in results if min_bpm <= bgm.bpm <= max_bpm]
        
        if usage:
            results = [bgm for bgm in results if usage in bgm.usage]
        
        return results
    
    def get_by_id(self, bgm_id: str) -> Optional[BGMMetadata]:
        """根据 ID 获取 BGM"""
        return self.metadata_cache.get(bgm_id)
    
    def get_all(self) -> List[BGMMetadata]:
        """获取所有 BGM"""
        return list(self.metadata_cache.values())
    
    def export_for_llm(self) -> List[dict]:
        """
        导出为 LLM 友好的格式
        
        Returns:
            简化的 BGM 列表，供 LLM 选择
        """
        return [
            {
                "id": bgm.id,
                "mood": bgm.mood,
                "bpm": bgm.bpm,
                "energy": bgm.energy,
                "usage": bgm.usage,
                "tags": bgm.tags or []
            }
            for bgm in self.metadata_cache.values()
        ]
    
    def create_sample_library(self):
        """
        创建示例 BGM 库结构（用于测试）
        
        生成目录结构和示例 metadata.json
        """
        # 定义示例结构
        sample_structure = {
            "calm": [
                {"filename": "calm_090bpm.mp3", "bpm": 90},
                {"filename": "calm_100bpm.mp3", "bpm": 100},
            ],
            "emotional": [
                {"filename": "emo_120bpm.mp3", "bpm": 120},
            ],
            "fast": [
                {"filename": "fast_140bpm.mp3", "bpm": 140},
            ],
            "suspense": [
                {"filename": "sus_110bpm.mp3", "bpm": 110},
            ]
        }
        
        for mood, files in sample_structure.items():
            mood_dir = self.library_root / mood
            mood_dir.mkdir(parents=True, exist_ok=True)
            
            for file_info in files:
                filename = file_info["filename"]
                bpm = file_info["bpm"]
                
                # 创建占位音频文件（空文件）
                audio_file = mood_dir / filename
                if not audio_file.exists():
                    audio_file.touch()
                
                # 生成元数据
                metadata = self._generate_metadata_for_sample(
                    audio_file, mood, bpm
                )
                
                # 保存元数据
                metadata_file = audio_file.with_suffix('.json')
                self._save_metadata(metadata, metadata_file)
                
                print(f"✓ 创建示例: {audio_file}")
        
        print(f"\n✓ 示例 BGM 库创建完成: {self.library_root}")
        print("⚠️  注意: 音频文件为空占位符，请替换为实际音频文件")
    
    def _generate_metadata_for_sample(
        self, 
        audio_file: Path, 
        mood: str, 
        bpm: int
    ) -> BGMMetadata:
        """为示例生成元数据"""
        # 根据 BPM 推断 energy
        if bpm < 100:
            energy = "low"
        elif bpm < 130:
            energy = "medium"
        else:
            energy = "high"
        
        # 生成 ID
        bgm_id = f"{mood}_{bpm:03d}_01"
        
        # 相对路径（相对于当前工作目录）
        try:
            relative_path = str(audio_file.relative_to(Path.cwd()))
        except ValueError:
            # 如果无法计算相对路径，使用绝对路径
            relative_path = str(audio_file.absolute())
        
        # 根据 mood 推断 usage
        usage_map = {
            "calm": ["teaching", "meditation", "background"],
            "emotional": ["story", "drama", "touching"],
            "fast": ["action", "sports", "energetic"],
            "suspense": ["thriller", "mystery", "tension"]
        }
        usage = usage_map.get(mood, ["general"])
        
        return BGMMetadata(
            id=bgm_id,
            path=relative_path,
            bpm=bpm,
            mood=mood,
            energy=energy,
            usage=usage,
            copyright="royalty_free",
            tags=[mood, energy, f"{bpm}bpm"]
        )


# 便捷函数
def create_bgm_library(library_root: str = "bgm_library") -> BGMLibrary:
    """
    创建 BGM 库实例
    
    Args:
        library_root: BGM 库根目录
    
    Returns:
        BGMLibrary 实例
    """
    library = BGMLibrary(library_root)
    library.scan_library()
    return library


def search_bgm(
    mood: Optional[str] = None,
    energy: Optional[str] = None,
    usage: Optional[str] = None,
    library_root: str = "bgm_library"
) -> List[BGMMetadata]:
    """
    便捷搜索函数
    
    Args:
        mood: 情绪
        energy: 能量级别
        usage: 用途
        library_root: BGM 库根目录
    
    Returns:
        匹配的 BGM 列表
    """
    library = create_bgm_library(library_root)
    return library.search(mood=mood, energy=energy, usage=usage)
