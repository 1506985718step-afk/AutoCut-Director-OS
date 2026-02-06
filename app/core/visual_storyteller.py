"""
视觉叙事引擎 (Visual Storyteller)

功能：在没有脚本的情况下，根据视觉素材自动构思故事线

工作流：
1. 聚类 (Clustering): 把素材按内容分组（人、景、物）
2. 构思 (Ideation): 根据素材组合，提出 3 个可能的剪辑主题
3. 编剧 (Scripting): 选定一个主题，生成旁白或字幕卡文案

输出：虚拟的 transcript.v1.json + editing_dsl.v1.json
"""
import json
from typing import List, Dict, Any, Optional
from collections import defaultdict

from openai import OpenAI

from ..config import settings
from ..models.schemas import (
    ScenesJSON, 
    Scene, 
    TranscriptJSON, 
    TranscriptSegment,
    TranscriptMeta
)


class VisualStoryteller:
    """无脚本模式的核心大脑 - 从视觉素材构思故事"""
    
    def __init__(self):
        """初始化 LLM 客户端"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured")
        
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
        
        self.client = OpenAI(**client_kwargs)
        self.model = "gpt-4o"  # 需要强推理能力
    
    def generate_story_from_visuals(
        self,
        scenes_data: ScenesJSON,
        duration_target: int = 30,
        style_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        核心入口：看片 -> 构思 -> 编剧
        
        Args:
            scenes_data: 包含 visual 信息的场景数据
            duration_target: 目标时长（秒）
            style_preference: 风格偏好（可选，如 "高燃踩点"、"情感叙事"）
        
        Returns:
            {
                "theme": "海边度假Vlog",
                "logic": "按时间顺序，从出发到日落",
                "narrative_style": "舒缓治愈",
                "generated_transcript": TranscriptJSON,
                "suggested_bgm_mood": "chill_hop",
                "clustering": {...},  # 素材聚类结果
                "alternative_themes": [...]  # 备选主题
            }
        """
        print("\n🎬 Visual Storyteller 启动...")
        
        # 1. 检查视觉数据
        visual_count = sum(1 for scene in scenes_data.scenes if scene.visual)
        if visual_count == 0:
            raise ValueError("场景数据中没有视觉信息，请先运行视觉分析")
        
        print(f"  ✓ 发现 {visual_count}/{len(scenes_data.scenes)} 个场景有视觉数据")
        
        # 2. 聚类分析
        print("\n[1/4] 聚类分析...")
        clustering = self._cluster_scenes(scenes_data)
        print(f"  ✓ 识别到 {len(clustering['groups'])} 个素材组")
        
        # 3. 提取视觉摘要
        print("\n[2/4] 提取视觉摘要...")
        visual_summary = self._summarize_visuals(scenes_data, clustering)
        
        # 4. 构思故事线（含备选方案）
        print("\n[3/4] AI 构思故事线...")
        story_plan = self._brainstorm_story(
            visual_summary,
            duration_target,
            style_preference
        )
        print(f"  ✓ 主题: {story_plan['theme']}")
        print(f"  ✓ 风格: {story_plan['narrative_style']}")
        
        # 5. 生成虚拟脚本
        print("\n[4/4] 生成虚拟脚本...")
        transcript = self._generate_virtual_transcript(
            story_plan,
            duration_target,
            scenes_data
        )
        print(f"  ✓ 生成了 {len(transcript.segments)} 段文案")
        
        print("\n✅ Visual Storyteller 完成！")
        
        return {
            "theme": story_plan["theme"],
            "logic": story_plan["logic"],
            "narrative_style": story_plan["narrative_style"],
            "generated_transcript": transcript,
            "suggested_bgm_mood": story_plan["bgm_mood"],
            "clustering": clustering,
            "alternative_themes": story_plan.get("alternatives", [])
        }
    
    def _cluster_scenes(self, scenes_data: ScenesJSON) -> Dict[str, Any]:
        """
        聚类分析：把素材按内容分组
        
        Returns:
            {
                "groups": {
                    "人物": ["S0001", "S0003"],
                    "风景": ["S0002", "S0005"],
                    "物品": ["S0004"]
                },
                "shot_types": {
                    "特写": 3,
                    "中景": 5,
                    "全景": 2
                },
                "moods": {
                    "开心": 4,
                    "平静": 6
                }
            }
        """
        groups = defaultdict(list)
        shot_types = defaultdict(int)
        moods = defaultdict(int)
        subjects_all = defaultdict(int)
        
        for scene in scenes_data.scenes:
            if not scene.visual:
                continue
            
            # 按主体分组
            if scene.visual.subjects:
                # 简单分类：人物、风景、物品
                has_person = any('人' in s for s in scene.visual.subjects)
                has_nature = any(
                    keyword in ' '.join(scene.visual.subjects)
                    for keyword in ['天空', '海', '山', '树', '花', '云', '日落', '风景']
                )
                
                if has_person:
                    groups["人物"].append(scene.scene_id)
                elif has_nature:
                    groups["风景"].append(scene.scene_id)
                else:
                    groups["物品"].append(scene.scene_id)
                
                # 统计所有主体
                for subject in scene.visual.subjects:
                    subjects_all[subject] += 1
            
            # 统计景别
            shot_types[scene.visual.shot_type] += 1
            
            # 统计情绪
            if scene.visual.mood:
                moods[scene.visual.mood] += 1
        
        return {
            "groups": dict(groups),
            "shot_types": dict(shot_types),
            "moods": dict(moods),
            "subjects": dict(sorted(
                subjects_all.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10])  # 前 10 个高频主体
        }
    
    def _summarize_visuals(
        self,
        scenes_data: ScenesJSON,
        clustering: Dict[str, Any]
    ) -> str:
        """
        将庞大的 Scene 对象简化为 AI 可读的文本摘要
        
        格式：
        [ID] [景别] 内容 (情绪) | 质量: X/10
        """
        summary_lines = []
        
        # 添加聚类摘要
        summary_lines.append("【素材聚类】")
        for group_name, scene_ids in clustering["groups"].items():
            summary_lines.append(f"  {group_name}: {len(scene_ids)} 个镜头")
        
        summary_lines.append("\n【高频主体】")
        for subject, count in list(clustering["subjects"].items())[:5]:
            summary_lines.append(f"  {subject}: {count} 次")
        
        summary_lines.append("\n【场景详情】")
        
        for scene in scenes_data.scenes:
            if not scene.visual:
                continue
            
            # 格式: [ID] [景别] 内容 (情绪) | 质量: X/10
            line = (
                f"[{scene.scene_id}] "
                f"[{scene.visual.shot_type}] "
                f"{scene.visual.summary} "
                f"(情绪: {scene.visual.mood}) | "
                f"质量: {scene.visual.quality_score}/10"
            )
            
            # 添加主体信息
            if scene.visual.subjects:
                line += f" | 主体: {', '.join(scene.visual.subjects[:3])}"
            
            summary_lines.append(line)
        
        return "\n".join(summary_lines)
    
    def _brainstorm_story(
        self,
        visual_summary: str,
        duration: int,
        style_preference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        调用 LLM 进行头脑风暴
        
        Returns:
            {
                "theme": "主题名称",
                "logic": "剪辑逻辑说明",
                "bgm_mood": "音乐风格建议",
                "narrative_style": "叙事风格",
                "alternatives": [...]  # 备选主题
            }
        """
        style_hint = ""
        if style_preference:
            style_hint = f"\n用户偏好风格：{style_preference}"
        
        system_prompt = f"""你是一名顶级短视频导演。现在的任务是：看着一堆素材，构思一个剪辑脚本。

目标时长：{duration} 秒{style_hint}

【现有素材清单】
{visual_summary}

请分析素材之间的关联，构思一个最合理的剪辑逻辑。

思考维度：
1. **内容连贯性**：素材之间有什么逻辑关系？（时间顺序、空间关系、因果关系）
2. **情绪曲线**：如何安排情绪起伏？（平静 -> 高潮 -> 收尾）
3. **视觉节奏**：景别如何组接？（全景 -> 中景 -> 特写）
4. **故事性**：能否构建一个简单的叙事弧？（开始 -> 发展 -> 结局）

可能的剪辑主题类型：
- **高燃踩点**：快节奏，强节奏感，适合运动、旅行、产品展示
- **情感叙事**：慢节奏，有故事线，适合 Vlog、纪录片
- **无厘头鬼畜**：快速切换，重复强调，适合搞笑、吐槽
- **氛围感**：慢镜头，情绪渲染，适合风景、美食
- **教学讲解**：逻辑清晰，分步骤，适合教程、测评

请返回 JSON 格式：
{{
  "theme": "主题名称（如：周末探店 / 海边日落 / 产品开箱）",
  "logic": "剪辑逻辑说明（如：先展示环境，再展示食物特写，最后人物评价）",
  "bgm_mood": "音乐风格建议（如：chill_hop / emotional / fast / suspense）",
  "narrative_style": "叙事风格（如：快节奏踩点 / 舒缓治愈 / 悬疑反转）",
  "alternatives": [
    {{"theme": "备选主题1", "reason": "为什么这个也可行"}},
    {{"theme": "备选主题2", "reason": "为什么这个也可行"}}
  ]
}}"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}],
            response_format={"type": "json_object"},
            temperature=0.8  # 提高创造性
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _generate_virtual_transcript(
        self,
        story_plan: Dict[str, Any],
        duration: int,
        scenes_data: ScenesJSON
    ) -> TranscriptJSON:
        """
        根据故事构思，生成配套的文案（可用于 TTS 或字幕卡）
        
        Args:
            story_plan: 故事构思
            duration: 目标时长
            scenes_data: 场景数据（用于参考时间点）
        
        Returns:
            TranscriptJSON 对象
        """
        # 计算场景时间分布
        fps = scenes_data.meta.fps
        scene_times = []
        for scene in scenes_data.scenes:
            if scene.visual:
                start_sec = scene.start_frame / fps
                end_sec = scene.end_frame / fps
                scene_times.append({
                    "scene_id": scene.scene_id,
                    "start": start_sec,
                    "end": end_sec,
                    "summary": scene.visual.summary
                })
        
        prompt = f"""基于主题 "{story_plan['theme']}" 和逻辑 "{story_plan['logic']}"，请创作一段短视频文案（Transcript）。

叙事风格：{story_plan['narrative_style']}
总时长约：{duration} 秒

【场景时间参考】
{json.dumps(scene_times[:10], indent=2, ensure_ascii=False)}

文案要求：
1. **分段合理**：分成 3-5 个句子，每句话 3-8 秒
2. **时间标注**：每句话标注预估时间范围（start, end）
3. **内容匹配**：文案要与画面内容呼应
4. **情绪递进**：遵循情绪曲线（开场吸引 -> 内容展开 -> 结尾升华）
5. **简洁有力**：每句话不超过 20 字

文案风格参考：
- 高燃踩点：短句、强调、重复（"这就是！"、"看到了吗！"）
- 情感叙事：舒缓、细腻、有画面感（"阳光洒在海面上..."）
- 无厘头鬼畜：夸张、反转、吐槽（"没想到吧！"、"这也太..."）
- 氛围感：诗意、留白、意境（"时间在这里变慢了..."）
- 教学讲解：清晰、分步骤（"第一步..."、"接下来..."）

请返回 JSON 格式：
{{
  "segments": [
    {{"start": 0.0, "end": 3.0, "text": "开场白..."}},
    {{"start": 3.0, "end": 8.0, "text": "内容展开..."}},
    {{"start": 8.0, "end": 12.0, "text": "继续深入..."}},
    {{"start": 12.0, "end": 15.0, "text": "结尾升华..."}}
  ]
}}

注意：
- start 和 end 必须是浮点数（秒）
- 时间不能重叠
- 总时长不超过 {duration} 秒
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        
        data = json.loads(response.choices[0].message.content)
        
        # 封装为标准 TranscriptJSON 对象
        return TranscriptJSON(
            meta=TranscriptMeta(
                schema_="transcript.v1",
                language="zh"
            ),
            segments=[TranscriptSegment(**seg) for seg in data["segments"]]
        )
    
    def generate_dsl_from_story(
        self,
        scenes_data: ScenesJSON,
        story_result: Dict[str, Any],
        platform: str = "douyin"
    ) -> Dict[str, Any]:
        """
        根据故事构思生成 editing_dsl.v1.json
        
        这是一个便捷方法，将 Visual Storyteller 的输出转换为 DSL
        
        Args:
            scenes_data: 场景数据
            story_result: generate_story_from_visuals 的返回结果
            platform: 目标平台
        
        Returns:
            editing_dsl.v1.json 格式的字典
        """
        from .llm_engine import LLMDirector
        
        # 使用 LLM Director 生成 DSL
        director = LLMDirector()
        
        # 构建风格提示
        style_prompt = f"""
主题：{story_result['theme']}
逻辑：{story_result['logic']}
风格：{story_result['narrative_style']}
音乐：{story_result['suggested_bgm_mood']}

这是一个无脚本模式的剪辑，文案是 AI 生成的。
请根据视觉素材和生成的文案，创作一个完整的剪辑方案。
"""
        
        # 生成 DSL
        dsl = director.generate_editing_dsl(
            scenes=scenes_data,
            transcript=story_result['generated_transcript'],
            style_prompt=style_prompt
        )
        
        return dsl


# 便捷函数
def create_story_from_visuals(
    scenes_data: ScenesJSON,
    duration_target: int = 30,
    style_preference: Optional[str] = None
) -> Dict[str, Any]:
    """
    便捷函数：从视觉素材创作故事
    
    Args:
        scenes_data: 包含视觉信息的场景数据
        duration_target: 目标时长（秒）
        style_preference: 风格偏好（可选）
    
    Returns:
        完整的故事构思结果
    """
    storyteller = VisualStoryteller()
    return storyteller.generate_story_from_visuals(
        scenes_data,
        duration_target,
        style_preference
    )
