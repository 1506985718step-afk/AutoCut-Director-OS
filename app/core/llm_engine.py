"""LLM DSL 生成引擎 - 让 AI 真正成为剪辑导演"""
import json
from openai import OpenAI
from ..config import settings
from ..models.schemas import ScenesJSON, TranscriptJSON


class LLMDirector:
    """AI 剪辑导演 - 根据素材生成剪辑脚本"""
    
    def __init__(self):
        """初始化 LLM 客户端"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured in .env")
        
        # 支持自定义 base_url（如 Azure OpenAI）
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
        
        self.client = OpenAI(**client_kwargs)
        self.model = settings.OPENAI_MODEL
    
    def generate_editing_dsl(
        self, 
        scenes: ScenesJSON, 
        transcript: TranscriptJSON, 
        style_prompt: str,
        bgm_library: list = None
    ) -> dict:
        """
        将场景和字幕喂给 AI，生成剪辑 DSL
        
        Args:
            scenes: 视觉素材（场景切分）
            transcript: 听觉素材（语音转录）
            style_prompt: 风格要求（如"抖音爆款风格"）
            bgm_library: BGM 素材库列表（可选）
        
        Returns:
            dict: editing_dsl.v1.json 格式的剪辑指令
        
        Raises:
            ValueError: AI 生成了无效的 JSON
        """
        system_prompt = self._build_system_prompt(bgm_library)
        user_content = self._build_user_content(scenes, transcript, style_prompt, bgm_library)
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format={"type": "json_object"},
            temperature=0.7  # 适度创造性
        )
        
        try:
            dsl = json.loads(response.choices[0].message.content)
            return dsl
        except json.JSONDecodeError as e:
            raise ValueError(f"AI 生成了无效的 JSON: {e}")
    
    def _build_system_prompt(self, bgm_library: list = None) -> str:
        """构建系统提示词 - 增强视觉理解能力"""
        bgm_section = ""
        if bgm_library:
            bgm_section = f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BGM 素材库（可选）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
你可以从以下 BGM 库中选择合适的背景音乐：

{json.dumps(bgm_library, indent=2, ensure_ascii=False)}

选择 BGM 时考虑：
1. **mood**: 情绪是否匹配视频内容（calm, emotional, fast, suspense）
2. **bpm**: 节奏是否匹配剪辑节奏（90-140）
3. **energy**: 能量级别是否合适（low, medium, high）
4. **usage**: 用途是否匹配（story, teaching, vlog, product）

在 music 字段中填入选中的 BGM ID：
{{
  "music": {{
    "bgm_id": "calm_090_01",  // 从 BGM 库中选择
    "volume_db": -18          // 音量（dB），建议 -18 到 -24
  }}
}}

如果没有合适的 BGM，可以留空：
{{
  "music": {{
    "bgm_id": "",
    "volume_db": -18
  }}
}}
"""
        
        return f"""你是一名专业的短视频剪辑导演。你的任务是根据提供的【视觉素材】和【听觉素材】，生成一个符合 'editing_dsl.v1' 格式的 JSON 剪辑指令。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 核心能力升级：你现在拥有"视觉理解"能力！
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Scenes 数据中包含了 `visual` 字段（景别、内容描述、情绪、主体）。
请充分利用这些信息来匹配剪辑逻辑，而不仅仅依赖时间顺序或随机选择。

剪辑逻辑指南：

1. **画面匹配内容**
   - 当语音提到具体物体（如"咖啡"、"手机"）时，优先搜索 `subjects` 或 `summary` 包含该物体的 Scene
   - 例如：语音说"打开手机" → 选择 subjects 包含 "手机" 的镜头

2. **情绪流控制**
   - 根据语音的情绪（transcript），选择 `mood` 匹配的画面
   - 例如：激昂的语音 → 配 action 强烈、mood 积极的画面
   - 平静的讲解 → 配 mood 平静、lighting 柔和的画面

3. **景别组接（蒙太奇原则）**
   - 避免同景别跳接（Jump Cut）
   - 尝试 "全景 → 中景 → 特写" 的递进
   - 或 "特写 → 全景" 的对比

4. **Hook 设计（前 3 秒）**
   - 开场必须使用 `quality_score` 最高的镜头
   - 且 `visual.summary` 最具吸引力
   - 优先选择 shot_type 为 "特写" 或 "近景" 的冲击力画面

5. **质量优先**
   - 优先使用 `quality_score` >= 7 的镜头
   - 避免使用 lighting 为 "过曝" 或 "暗调" 的低质量画面

核心要求：
1. 挑选最精彩的语句作为 Hook（开头钩子），吸引观众停留
2. 删除废话、停顿、重复内容，保持节奏紧凑
3. 每 3-5 秒必须有画面切换或文字强调，保持视觉刺激
4. overlay_text 必须简短有力（5-8 字），突出关键信息
5. **充分利用 visual 标签进行智能镜头选择**
6. 严格遵守 JSON 格式，不要输出任何多余文字

JSON 格式规范：
{{
  "meta": {{
    "schema": "editing_dsl.v1",
    "target": "douyin",  // 目标平台
    "aspect": "9:16"     // 竖屏
  }},
  "editing_plan": {{
    "timeline": [
      {{
        "order": 1,
        "scene_id": "S0001",           // 必须来自 scenes 中的 scene_id
        "trim_frames": [10, 90],       // 必须在场景的 [start_frame, end_frame] 范围内
        "purpose": "hook",             // hook/body/cta
        "overlay_text": "第一步就错了"  // 5-8 字，可选
      }}
    ],
    "subtitles": {{
      "mode": "from_transcript",  // 从 transcript 生成字幕
      "style": "bold_yellow"      // 字幕样式
    }},
    "music": {{
      "bgm_id": "",               // BGM ID（从 BGM 库中选择，可选）
      "volume_db": -18            // 音量（dB）
    }}
  }},
  "export": {{
    "resolution": "1080x1920",
    "format": "mp4"
  }}
}}

硬规则（必须遵守）：
- scene_id 必须存在于 scenes 中
- trim_frames 必须在场景的 [start_frame, end_frame] 范围内
- trim_frames[0] < trim_frames[1]
- overlay_text 不超过 10 个字

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
铁律 1: 不允许"未提供素材库却要求素材调用"
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- 如果没有提供 B-roll 素材库，broll 字段必须为空数组 []
- 不要幻想或假设存在的素材
- 如果需要 B-roll 但没有素材，在 assumptions 中说明

示例（正确）:
{{
  "timeline": [
    {{
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": [10, 90],
      "broll": []  // ✅ 没有素材库，必须为空
    }}
  ],
  "assumptions": [
    "建议添加产品特写 B-roll 增强视觉效果"
  ]
}}

示例（错误）:
{{
  "timeline": [
    {{
      "order": 1,
      "scene_id": "S0001",
      "trim_frames": [10, 90],
      "broll": ["product_closeup.mp4"]  // ❌ 素材库中不存在
    }}
  ]
}}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
铁律 2: 坐标体系统一 - 内部只用 frame
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- trim_frames 必须使用整数帧号 [in_frame, out_frame]
- 不要使用 timecode 格式（如 "00:00:01:15"）
- scenes.json 中已提供 fps，用于内部换算
- timecode 仅用于对外展示，不用于内部计算

示例（正确）:
{{
  "trim_frames": [30, 120]  // ✅ 整数帧号
}}

示例（错误）:
{{
  "trim_frames": ["00:00:01:00", "00:00:04:00"]  // ❌ 不要用 timecode
}}{bgm_section}"""
    
    def _build_user_content(
        self, 
        scenes: ScenesJSON, 
        transcript: TranscriptJSON, 
        style_prompt: str,
        bgm_library: list = None
    ) -> str:
        """构建用户输入内容"""
        scenes_json = json.dumps(scenes.model_dump(), ensure_ascii=False, indent=2)
        transcript_json = json.dumps(transcript.model_dump(), ensure_ascii=False, indent=2)
        
        content = f"""【视觉素材 (Scenes)】
{scenes_json}

【听觉素材 (Transcript)】
{transcript_json}

【风格要求】
{style_prompt}"""
        
        if bgm_library:
            content += f"""

【BGM 素材库】
{json.dumps(bgm_library, indent=2, ensure_ascii=False)}"""
        
        content += "\n\n请根据以上素材，生成符合 editing_dsl.v1 格式的剪辑指令 JSON。"
        
        return content


# 便捷函数
def generate_dsl_from_materials(
    scenes: ScenesJSON,
    transcript: TranscriptJSON,
    style: str = "抖音爆款风格：节奏快、文字多、强调关键词",
    bgm_library: list = None
) -> dict:
    """
    便捷函数：从素材生成 DSL
    
    Args:
        scenes: 场景数据
        transcript: 转录数据
        style: 风格描述
        bgm_library: BGM 素材库列表（可选）
    
    Returns:
        dict: editing_dsl.v1.json
    """
    director = LLMDirector()
    return director.generate_editing_dsl(scenes, transcript, style, bgm_library)
