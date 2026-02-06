"""
视觉分析器 - 给 AutoCut Director 装上眼睛

功能：
1. 截取每个场景的关键帧
2. 调用 GPT-4o Vision API 分析画面内容（云端）
3. 为 scenes.json 添加视觉元数据

注意：推荐使用 visual_analyzer_local.py（本地模型，零成本）
"""
import base64
import json
import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from openai import OpenAI

from ..config import settings
from ..models.schemas import ScenesJSON, VisualMetadata


class VisualAnalyzer:
    """视觉分析器 - 让 AI 导演能"看懂"画面"""
    
    def __init__(self):
        """初始化：复用配置中的 API Key"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not configured in .env")
        
        client_kwargs = {"api_key": settings.OPENAI_API_KEY}
        if settings.OPENAI_BASE_URL:
            client_kwargs["base_url"] = settings.OPENAI_BASE_URL
        
        self.client = OpenAI(**client_kwargs)
        
        # 强制使用支持视觉的模型
        self.vision_model = "gpt-4o"
    
    def _extract_frame_base64(self, video_path: str, time_sec: float) -> Optional[str]:
        """
        使用 FFmpeg 截取指定时间点的帧，返回 base64 字符串
        
        Args:
            video_path: 视频文件路径
            time_sec: 时间点（秒）
        
        Returns:
            base64 编码的图片字符串，失败返回 None
        """
        # 使用临时文件
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            temp_img = tmp.name
        
        try:
            cmd = [
                "ffmpeg",
                "-ss", str(time_sec),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",  # 高质量 JPG
                "-y",
                temp_img
            ]
            
            # 执行截帧（静默模式）
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            
            if not os.path.exists(temp_img):
                raise RuntimeError("Frame extraction failed: image not created")
            
            # 读取并编码
            with open(temp_img, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        
        except subprocess.TimeoutExpired:
            print(f"  ⚠️ 截帧超时 ({time_sec}s)")
            return None
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️ 截帧失败 ({time_sec}s): FFmpeg error")
            return None
        except Exception as e:
            print(f"  ⚠️ 截帧失败 ({time_sec}s): {e}")
            return None
        finally:
            # 清理临时文件
            if os.path.exists(temp_img):
                try:
                    os.remove(temp_img)
                except:
                    pass
    
    def analyze_scene_visuals(
        self,
        scenes_data: ScenesJSON,
        video_path: str,
        max_scenes: Optional[int] = None
    ) -> ScenesJSON:
        """
        批量分析场景的视觉内容
        
        Args:
            scenes_data: 场景数据对象
            video_path: 视频文件路径
            max_scenes: 限制分析数量（调试用），None 为全部分析
        
        Returns:
            更新后的场景数据（包含 visual 字段）
        """
        print(f"\n👁️  开始视觉分析: {len(scenes_data.scenes)} 个场景")
        
        if not Path(video_path).exists():
            print(f"  ❌ 视频文件不存在: {video_path}")
            return scenes_data
        
        count = 0
        for scene in scenes_data.scenes:
            if max_scenes and count >= max_scenes:
                print(f"\n  ⏸️  已达到限制 ({max_scenes} 个场景)，停止分析")
                break
            
            # 1. 如果已有视觉数据，跳过
            if scene.visual:
                print(f"  ⏭️  {scene.scene_id} 已有视觉数据，跳过")
                continue
            
            # 2. 计算中间时刻
            mid_frame = (scene.start_frame + scene.end_frame) // 2
            mid_sec = mid_frame / scenes_data.meta.fps
            
            # 3. 截取代表帧
            print(f"  > 分析 {scene.scene_id} (T={mid_sec:.1f}s)...", end="", flush=True)
            img_b64 = self._extract_frame_base64(video_path, mid_sec)
            
            if not img_b64:
                print(" ❌ 截帧失败")
                continue
            
            # 4. 调用 GPT-4o 识图
            try:
                scene.visual = self._call_vision_api(img_b64)
                print(f" ✅ [{scene.visual.shot_type}] {scene.visual.summary}")
                count += 1
            except Exception as e:
                print(f" ❌ API 错误: {e}")
        
        print(f"\n✅ 视觉分析完成: {count}/{len(scenes_data.scenes)} 个场景")
        return scenes_data
    
    def _call_vision_api(self, img_b64: str) -> VisualMetadata:
        """
        调用 Vision 模型分析图片
        
        Args:
            img_b64: base64 编码的图片
        
        Returns:
            视觉元数据
        
        Raises:
            ValueError: API 返回无效数据
        """
        system_prompt = """你是一个专业的视频素材分析师。请分析这张视频截图，提取关键视觉信息。

请以 JSON 格式返回，包含以下字段：
- summary: 画面内容的一句话描述（中文，15字以内）
- shot_type: 景别（特写/近景/中景/全景/远景）
- subjects: 画面中的主要物体或人物（列表，如 ["人物", "手机"]）
- action: 主体的动作或状态（如 "说话"、"跑步"、"静止"）
- mood: 画面传达的情绪（如 "开心"、"紧张"、"平静"、"科技感"）
- lighting: 光线情况（如 "自然光"、"室内"、"暗调"、"过曝"）
- quality_score: 画面质量评分 1-10（考虑清晰度、构图、美感）

示例输出：
{
  "summary": "年轻人在咖啡厅使用笔记本电脑",
  "shot_type": "中景",
  "subjects": ["人物", "笔记本电脑", "咖啡杯"],
  "action": "工作",
  "mood": "专注",
  "lighting": "自然光",
  "quality_score": 8
}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_b64}",
                                    "detail": "low"  # 使用 low 降低成本
                                }
                            }
                        ]
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            data = json.loads(content)
            
            return VisualMetadata(**data)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse vision response: {e}")
        except Exception as e:
            raise ValueError(f"Vision API error: {e}")


# 便捷函数
def analyze_scenes_with_vision(
    scenes_data: ScenesJSON,
    video_path: str,
    max_scenes: Optional[int] = None
) -> ScenesJSON:
    """
    便捷函数：为场景数据添加视觉分析
    
    Args:
        scenes_data: 场景数据
        video_path: 视频文件路径
        max_scenes: 限制分析数量（可选）
    
    Returns:
        更新后的场景数据
    """
    analyzer = VisualAnalyzer()
    return analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes)


# 独立测试入口
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    # 用法: python -m app.tools.visual_analyzer video.mp4 scenes.json
    if len(sys.argv) < 3:
        print("用法: python -m app.tools.visual_analyzer <video.mp4> <scenes.json>")
        sys.exit(1)
    
    video_path = sys.argv[1]
    scenes_path = sys.argv[2]
    
    if not Path(video_path).exists():
        print(f"❌ 视频文件不存在: {video_path}")
        sys.exit(1)
    
    if not Path(scenes_path).exists():
        print(f"❌ 场景文件不存在: {scenes_path}")
        sys.exit(1)
    
    # 加载 scenes.json
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_dict = json.load(f)
    
    scenes_data = ScenesJSON(**scenes_dict)
    
    # 分析视觉
    analyzer = VisualAnalyzer()
    updated_scenes = analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes=5)
    
    # 保存结果
    output_path = scenes_path.replace('.json', '_with_visual.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_scenes.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存到: {output_path}")
