"""
本地视觉分析器 - 使用 Ollama 本地模型

支持模型：
- moondream (1.8B, 1.5GB) - 首选，速度快，省显存
- llava-phi3 (3.8B, 2.5GB) - 逻辑性更好，显存稍高

优势：
- 完全本地运行，无需 API Key
- 零成本，无限次调用
- 速度快（GPU 加速）
- 隐私保护
"""
import base64
import json
import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Optional, Literal
import requests

from ..models.schemas import ScenesJSON, VisualMetadata


class LocalVisualAnalyzer:
    """本地视觉分析器 - 使用 Ollama"""
    
    def __init__(
        self,
        model: Literal["moondream", "llava-phi3"] = "moondream",
        ollama_host: str = "http://localhost:11434"
    ):
        """
        初始化本地视觉分析器
        
        Args:
            model: 使用的模型（moondream 或 llava-phi3）
            ollama_host: Ollama 服务地址
        """
        self.model = model
        self.ollama_host = ollama_host
        self.api_url = f"{ollama_host}/api/generate"
        
        # 检查 Ollama 是否运行
        if not self._check_ollama_running():
            raise RuntimeError(
                "Ollama 服务未运行。请先启动 Ollama:\n"
                "  Windows: 从开始菜单启动 Ollama\n"
                "  或运行: ollama serve"
            )
        
        # 检查模型是否已下载
        if not self._check_model_available():
            raise RuntimeError(
                f"模型 '{model}' 未安装。请先下载:\n"
                f"  ollama pull {model}"
            )
        
        print(f"✓ 本地视觉分析器已初始化: {model}")
    
    def _check_ollama_running(self) -> bool:
        """检查 Ollama 服务是否运行"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def _check_model_available(self) -> bool:
        """检查模型是否已下载"""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return any(self.model in m.get("name", "") for m in models)
            return False
        except:
            return False
    
    def _extract_frame_base64(self, video_path: str, time_sec: float) -> Optional[str]:
        """
        使用 FFmpeg 截取指定时间点的帧，返回 base64 字符串
        
        Args:
            video_path: 视频文件路径
            time_sec: 时间点（秒）
        
        Returns:
            base64 编码的图片字符串，失败返回 None
        """
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            temp_img = tmp.name
        
        try:
            cmd = [
                "ffmpeg",
                "-ss", str(time_sec),
                "-i", video_path,
                "-frames:v", "1",
                "-q:v", "2",
                "-y",
                temp_img
            ]
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            
            if not os.path.exists(temp_img):
                raise RuntimeError("Frame extraction failed")
            
            with open(temp_img, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        
        except Exception as e:
            print(f"  ⚠️ 截帧失败 ({time_sec}s): {e}")
            return None
        finally:
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
            max_scenes: 限制分析数量，None 为全部分析
        
        Returns:
            更新后的场景数据（包含 visual 字段）
        """
        print(f"\n👁️  开始本地视觉分析 ({self.model}): {len(scenes_data.scenes)} 个场景")
        
        if not Path(video_path).exists():
            print(f"  ❌ 视频文件不存在: {video_path}")
            return scenes_data
        
        count = 0
        for scene in scenes_data.scenes:
            if max_scenes and count >= max_scenes:
                print(f"\n  ⏸️  已达到限制 ({max_scenes} 个场景)，停止分析")
                break
            
            if scene.visual:
                print(f"  ⏭️  {scene.scene_id} 已有视觉数据，跳过")
                continue
            
            mid_frame = (scene.start_frame + scene.end_frame) // 2
            mid_sec = mid_frame / scenes_data.meta.fps
            
            print(f"  > 分析 {scene.scene_id} (T={mid_sec:.1f}s)...", end="", flush=True)
            img_b64 = self._extract_frame_base64(video_path, mid_sec)
            
            if not img_b64:
                print(" ❌ 截帧失败")
                continue
            
            try:
                scene.visual = self._call_vision_api(img_b64)
                print(f" ✅ [{scene.visual.shot_type}] {scene.visual.summary}")
                count += 1
            except Exception as e:
                print(f" ❌ 分析错误: {e}")
        
        print(f"\n✅ 本地视觉分析完成: {count}/{len(scenes_data.scenes)} 个场景")
        return scenes_data
    
    def _call_vision_api(self, img_b64: str) -> VisualMetadata:
        """
        调用 Ollama 本地模型分析图片
        
        Args:
            img_b64: base64 编码的图片
        
        Returns:
            视觉元数据
        """
        # 构建 prompt
        prompt = """请分析这张视频截图，提取关键视觉信息。

请以 JSON 格式返回，包含以下字段：
- summary: 画面内容的一句话描述（中文，15字以内）
- shot_type: 景别（从以下选择：特写/近景/中景/全景/远景）
- subjects: 画面中的主要物体或人物（列表，如 ["人物", "手机"]）
- action: 主体的动作或状态（如 "说话"、"跑步"、"静止"）
- mood: 画面传达的情绪（如 "开心"、"紧张"、"平静"）
- lighting: 光线情况（如 "自然光"、"室内"、"暗调"）
- quality_score: 画面质量评分 1-10（考虑清晰度、构图）

只返回 JSON，不要其他文字。"""
        
        try:
            # 调用 Ollama API
            payload = {
                "model": self.model,
                "prompt": prompt,
                "images": [img_b64],
                "stream": False,
                "format": "json"
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=30
            )
            
            if response.status_code != 200:
                raise ValueError(f"Ollama API 错误: {response.status_code}")
            
            result = response.json()
            response_text = result.get("response", "")
            
            # 解析 JSON
            try:
                data = json.loads(response_text)
            except json.JSONDecodeError:
                # 如果模型返回的不是纯 JSON，尝试提取
                import re
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    raise ValueError("无法解析模型返回的 JSON")
            
            # 验证和填充默认值
            return VisualMetadata(
                summary=data.get("summary", "未知场景"),
                shot_type=data.get("shot_type", "中景"),
                subjects=data.get("subjects", []),
                action=data.get("action", ""),
                mood=data.get("mood", ""),
                lighting=data.get("lighting", ""),
                quality_score=data.get("quality_score", 5)
            )
        
        except Exception as e:
            raise ValueError(f"本地视觉分析失败: {e}")


# 便捷函数
def analyze_scenes_with_local_vision(
    scenes_data: ScenesJSON,
    video_path: str,
    model: Literal["moondream", "llava-phi3"] = "moondream",
    max_scenes: Optional[int] = None
) -> ScenesJSON:
    """
    便捷函数：使用本地模型为场景数据添加视觉分析
    
    Args:
        scenes_data: 场景数据
        video_path: 视频文件路径
        model: 使用的模型
        max_scenes: 限制分析数量（可选）
    
    Returns:
        更新后的场景数据
    """
    analyzer = LocalVisualAnalyzer(model=model)
    return analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes)


# 独立测试入口
if __name__ == "__main__":
    import sys
    from pathlib import Path
    
    if len(sys.argv) < 3:
        print("用法: python -m app.tools.visual_analyzer_local <video.mp4> <scenes.json> [model]")
        print("模型选项: moondream (默认) 或 llava-phi3")
        sys.exit(1)
    
    video_path = sys.argv[1]
    scenes_path = sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "moondream"
    
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
    analyzer = LocalVisualAnalyzer(model=model)
    updated_scenes = analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes=5)
    
    # 保存结果
    output_path = scenes_path.replace('.json', f'_with_visual_{model}.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(updated_scenes.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 结果已保存到: {output_path}")
