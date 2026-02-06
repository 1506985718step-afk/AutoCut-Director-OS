"""
LM Studio Visual Analyzer - 使用 LM Studio 进行本地视觉分析

LM Studio 优势：
1. 友好的 UI 界面
2. OpenAI 兼容 API
3. 支持多种视觉模型（Moondream, LLaVA, Qwen-VL 等）
4. 自动 GPU 加速
5. 模型管理简单

推荐模型（按优先级）：
- vikhyatk/moondream2 (1.5GB) - 🌟 首选，极快，专为边缘设备设计
- xtuner/llava-phi-3-mini (2.5GB) - 推荐，微软 Phi3 架构，逻辑性好
- MiniCPM-V (5GB) - 不推荐，体积大，不适合边缘设备
"""
import base64
import tempfile
import os
from pathlib import Path
from typing import List, Optional
import requests

from ..models.schemas import ScenesJSON, Scene


class LMStudioVisualAnalyzer:
    """LM Studio 视觉分析器"""
    
    def __init__(
        self,
        base_url: str = "http://localhost:1234/v1",
        model: str = "auto",  # LM Studio 会自动使用加载的模型
        timeout: int = 30
    ):
        """
        初始化 LM Studio 视觉分析器
        
        Args:
            base_url: LM Studio API 地址（默认 http://localhost:1234/v1）
            model: 模型名称（"auto" 表示使用当前加载的模型）
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
    
    def is_available(self) -> bool:
        """检查 LM Studio 是否可用"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def get_loaded_model(self) -> Optional[str]:
        """获取当前加载的模型"""
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=2
            )
            
            if response.status_code == 200:
                data = response.json()
                models = data.get("data", [])
                if models:
                    return models[0].get("id", "unknown")
            
            return None
        except:
            return None
    
    def analyze_image(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail, focusing on the main subject, action, mood, and visual quality."
    ) -> str:
        """
        分析单张图片
        
        Args:
            image_path: 图片路径
            prompt: 分析提示词
        
        Returns:
            图片描述文本
        """
        # 读取图片并转换为 base64
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # 构建 OpenAI 兼容的请求
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            return content.strip()
        
        except requests.exceptions.Timeout:
            raise TimeoutError(f"LM Studio 请求超时（{self.timeout}秒）")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"LM Studio 请求失败: {e}")
    
    def analyze_scene_visuals(
        self,
        scenes_data: ScenesJSON,
        video_path: str,
        max_scenes: Optional[int] = None
    ) -> ScenesJSON:
        """
        分析场景视觉内容
        
        Args:
            scenes_data: 场景数据
            video_path: 视频文件路径
            max_scenes: 最多分析多少个场景
        
        Returns:
            更新后的场景数据
        """
        import cv2
        
        # 检查 LM Studio 是否可用
        if not self.is_available():
            raise RuntimeError(
                "LM Studio 不可用。请确保：\n"
                "1. LM Studio 已启动\n"
                "2. 已加载视觉模型（如 LLaVA）\n"
                "3. 本地服务器已启动（默认端口 1234）"
            )
        
        # 获取当前加载的模型
        loaded_model = self.get_loaded_model()
        if loaded_model:
            print(f"🏠 使用 LM Studio 模型: {loaded_model}")
        else:
            print(f"⚠️  无法获取模型信息，使用默认配置")
        
        # 打开视频
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        # 限制分析数量
        scenes_to_analyze = scenes_data.scenes
        if max_scenes and len(scenes_to_analyze) > max_scenes:
            print(f"⚠️  场景数量 ({len(scenes_to_analyze)}) 超过限制，只分析前 {max_scenes} 个")
            scenes_to_analyze = scenes_to_analyze[:max_scenes]
        
        print(f"\n👁️  开始视觉分析（LM Studio）...")
        print(f"  场景数: {len(scenes_to_analyze)}")
        
        # 分析每个场景
        for i, scene in enumerate(scenes_to_analyze, 1):
            print(f"\n[{i}/{len(scenes_to_analyze)}] 分析场景 {scene.scene_id}...")
            
            try:
                # 提取关键帧（场景中间位置）
                mid_frame = (scene.start_frame + scene.end_frame) // 2
                cap.set(cv2.CAP_PROP_POS_FRAMES, mid_frame)
                ret, frame = cap.read()
                
                if not ret:
                    print(f"  ⚠️  无法提取帧，跳过")
                    continue
                
                # 保存临时图片
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                    temp_img = tmp.name
                    cv2.imwrite(temp_img, frame)
                
                try:
                    # 调用 LM Studio 分析
                    description = self.analyze_image(
                        temp_img,
                        prompt=(
                            "Analyze this video frame for editing purposes. Describe:\n"
                            "1. Main subject and action\n"
                            "2. Shot type (close-up, medium, wide)\n"
                            "3. Mood and atmosphere\n"
                            "4. Visual quality (1-10)\n"
                            "Be concise and focus on editing-relevant details."
                        )
                    )
                    
                    # 解析描述并更新场景
                    scene.visual = {
                        "summary": description,
                        "analyzed_by": "lmstudio",
                        "model": loaded_model or "unknown"
                    }
                    
                    print(f"  ✓ {description[:80]}...")
                
                finally:
                    # 清理临时文件
                    try:
                        os.remove(temp_img)
                    except:
                        pass
            
            except Exception as e:
                print(f"  ✗ 分析失败: {e}")
                continue
        
        cap.release()
        
        print(f"\n✓ 视觉分析完成")
        
        return scenes_data


def analyze_with_lmstudio(
    scenes_data: ScenesJSON,
    video_path: str,
    max_scenes: Optional[int] = None,
    base_url: str = "http://localhost:1234/v1"
) -> ScenesJSON:
    """
    快捷函数：使用 LM Studio 分析场景
    
    Args:
        scenes_data: 场景数据
        video_path: 视频文件路径
        max_scenes: 最多分析多少个场景
        base_url: LM Studio API 地址
    
    Returns:
        更新后的场景数据
    """
    analyzer = LMStudioVisualAnalyzer(base_url=base_url)
    return analyzer.analyze_scene_visuals(scenes_data, video_path, max_scenes)
