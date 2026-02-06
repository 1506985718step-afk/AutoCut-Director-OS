"""
UI 意图 → DSL 的翻译层

这个模块负责将用户的 UI 操作翻译成 DSL 结构和 LLM Prompt。
所有映射关系都在配置文件中，不写死在代码里。
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class UITranslator:
    """UI 意图 → DSL 的翻译层"""
    
    def __init__(self, mapping_file: str = "config/ui_dsl_mapping.json"):
        """
        初始化翻译器
        
        Args:
            mapping_file: 映射配置文件路径
        """
        mapping_path = Path(mapping_file)
        if not mapping_path.exists():
            raise FileNotFoundError(f"映射配置文件不存在: {mapping_file}")
        
        with open(mapping_path, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
    
    def translate_platform(self, ui_platform: str) -> Dict[str, Any]:
        """
        平台选择 → DSL meta
        
        Args:
            ui_platform: UI 平台选择 (douyin/bilibili/youtube/kuaishou)
        
        Returns:
            DSL meta 字段
        
        Example:
            >>> translator.translate_platform("douyin")
            {
                "target_platform": "douyin",
                "aspect_ratio": "9:16",
                "resolution": "1080x1920",
                "max_duration": 60
            }
        """
        if ui_platform not in self.mapping["platform_mapping"]:
            raise ValueError(f"未知平台: {ui_platform}")
        
        return self.mapping["platform_mapping"][ui_platform]
    
    def translate_style(self, ui_style: str) -> str:
        """
        风格选择 → LLM prompt
        
        Args:
            ui_style: UI 风格选择 (teaching/emotional/viral/vlog)
        
        Returns:
            LLM prompt 字符串
        
        Example:
            >>> translator.translate_style("viral")
            "抖音爆款风格：节奏快、文字多、强调关键词..."
        """
        if ui_style not in self.mapping["style_prompts"]:
            raise ValueError(f"未知风格: {ui_style}")
        
        return self.mapping["style_prompts"][ui_style]
    
    def translate_pace(self, ui_pace: str) -> Dict[str, Any]:
        """
        节奏选择 → DSL + LLM prompt
        
        Args:
            ui_pace: UI 节奏选择 (slow/medium/fast)
        
        Returns:
            包含 DSL 值和 LLM prompt 的字典
        
        Example:
            >>> translator.translate_pace("fast")
            {
                "dsl_value": "fast",
                "llm_prompt": "激进剪辑，只保留核心内容...",
                "trim_aggressiveness": 0.9
            }
        """
        if ui_pace not in self.mapping["pace_mapping"]:
            raise ValueError(f"未知节奏: {ui_pace}")
        
        return self.mapping["pace_mapping"][ui_pace]
    
    def translate_subtitle_density(self, ui_density: str) -> Dict[str, Any]:
        """
        字幕密度 → DSL subtitles
        
        Args:
            ui_density: UI 字幕密度 (minimal/standard/dense)
        
        Returns:
            DSL subtitles 配置
        """
        if ui_density not in self.mapping["subtitle_density_mapping"]:
            raise ValueError(f"未知字幕密度: {ui_density}")
        
        return self.mapping["subtitle_density_mapping"][ui_density]
    
    def translate_music_preference(self, ui_music: str) -> Dict[str, Any]:
        """
        音乐偏好 → DSL music
        
        Args:
            ui_music: UI 音乐偏好 (none/emotional/suspense/upbeat/calm)
        
        Returns:
            DSL music 配置
        """
        if ui_music not in self.mapping["music_preference_mapping"]:
            raise ValueError(f"未知音乐偏好: {ui_music}")
        
        return self.mapping["music_preference_mapping"][ui_music]
    
    def translate_adjustment(
        self, 
        adjustment_type: str, 
        adjustment_value: str
    ) -> str:
        """
        用户调整 → LLM prompt 追加
        
        Args:
            adjustment_type: 调整类型 (pace/hook/music/subtitle)
            adjustment_value: 调整值 (faster/slower/stronger/softer/change/remove/more/less)
        
        Returns:
            LLM prompt 追加字符串
        
        Example:
            >>> translator.translate_adjustment("pace", "faster")
            "用户反馈：节奏太慢，请加快剪辑节奏..."
        """
        key = f"{adjustment_type}_{adjustment_value}"
        
        if key not in self.mapping["adjustment_prompts"]:
            return ""  # 如果没有映射，返回空字符串
        
        return self.mapping["adjustment_prompts"][key]
    
    def build_initial_prompt(
        self,
        platform: str,
        style: str,
        pace: str,
        subtitle_density: str,
        music_preference: str
    ) -> str:
        """
        构建初始 LLM prompt
        
        Args:
            platform: 平台选择
            style: 风格选择
            pace: 节奏选择
            subtitle_density: 字幕密度
            music_preference: 音乐偏好
        
        Returns:
            完整的 LLM prompt
        """
        platform_info = self.translate_platform(platform)
        style_prompt = self.translate_style(style)
        pace_info = self.translate_pace(pace)
        subtitle_info = self.translate_subtitle_density(subtitle_density)
        music_info = self.translate_music_preference(music_preference)
        
        prompt = f"""
{style_prompt}

目标平台：{platform_info['target_platform']}
视频比例：{platform_info['aspect_ratio']}
最大时长：{platform_info['max_duration']}秒

剪辑节奏：{pace_info['llm_prompt']}

字幕要求：
- 密度：{subtitle_info['dsl_value']}
- 关键词高亮：{'是' if subtitle_info['highlight_keywords'] else '否'}
- 文字叠加：{'是' if subtitle_info['overlay_text'] else '否'}

音乐要求：
"""
        
        if music_info['enabled']:
            prompt += f"- 使用背景音乐\n- 情绪：{music_info['mood']}\n- 能量：{music_info['energy']}"
        else:
            prompt += "- 不使用背景音乐"
        
        return prompt.strip()
    
    def build_adjustment_prompt(
        self,
        original_prompt: str,
        adjustments: Dict[str, str]
    ) -> str:
        """
        构建调整后的 LLM prompt
        
        Args:
            original_prompt: 原始 prompt
            adjustments: 用户调整 {"pace": "faster", "hook": "stronger", ...}
        
        Returns:
            追加了调整说明的 prompt
        """
        adjustment_prompts = []
        
        for adj_type, adj_value in adjustments.items():
            if adj_value != "keep":  # 只处理有变化的调整
                adj_prompt = self.translate_adjustment(adj_type, adj_value)
                if adj_prompt:
                    adjustment_prompts.append(adj_prompt)
        
        if not adjustment_prompts:
            return original_prompt
        
        # 追加调整说明
        full_prompt = original_prompt + "\n\n--- 用户调整 ---\n"
        full_prompt += "\n".join(adjustment_prompts)
        
        return full_prompt
    
    def create_version_metadata(
        self,
        version: int,
        parent_version: Optional[int],
        adjustments: Optional[Dict[str, str]] = None,
        summary: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        创建版本元数据
        
        Args:
            version: 版本号
            parent_version: 父版本号
            adjustments: 用户调整
            summary: 剪辑摘要
        
        Returns:
            版本元数据
        """
        metadata = self.mapping["version_metadata_template"].copy()
        
        metadata["version"] = version
        metadata["parent_version"] = parent_version
        metadata["created_at"] = datetime.now().isoformat()
        
        if adjustments:
            metadata["user_adjustments"] = adjustments
        
        if summary:
            metadata["summary"] = summary
        
        return metadata
    
    def extract_summary_from_dsl(self, dsl: Dict[str, Any]) -> Dict[str, str]:
        """
        从 DSL 中提取摘要信息
        
        Args:
            dsl: DSL 对象
        
        Returns:
            摘要信息 {"hook": "...", "pace": "...", "music": "...", "duration": "..."}
        """
        summary = {
            "hook": "未知",
            "pace": "未知",
            "music": "无",
            "duration": "未知"
        }
        
        # 提取 Hook 信息
        if "editing_plan" in dsl and "timeline" in dsl["editing_plan"]:
            timeline = dsl["editing_plan"]["timeline"]
            if timeline:
                first_item = timeline[0]
                scene_id = first_item.get("scene_id", "unknown")
                summary["hook"] = f"场景 {scene_id}"
        
        # 提取节奏信息
        if "editing_plan" in dsl and "pace" in dsl["editing_plan"]:
            pace = dsl["editing_plan"]["pace"]
            pace_map = {"slow": "慢", "medium": "中", "fast": "快"}
            summary["pace"] = pace_map.get(pace, pace)
        
        # 提取音乐信息
        if "music" in dsl and dsl["music"]:
            music = dsl["music"][0]
            mood = music.get("mood", "未知")
            bpm = music.get("bpm", "未知")
            summary["music"] = f"{mood}（{bpm} BPM）"
        
        # 提取时长信息
        if "meta" in dsl and "estimated_duration" in dsl["meta"]:
            duration = dsl["meta"]["estimated_duration"]
            summary["duration"] = f"{duration}秒"
        
        return summary


# 单例模式
_translator_instance = None


def get_translator() -> UITranslator:
    """获取 UITranslator 单例"""
    global _translator_instance
    if _translator_instance is None:
        _translator_instance = UITranslator()
    return _translator_instance
