"""
Execution Policy Resolver - 执行策略解析器

功能：
1. 根据 RuntimeProfile 生成执行策略
2. 动态调整策略
3. 自适应降级

输入：RuntimeProfile
输出：完整的执行策略
"""
from typing import Dict, Any, Literal, Optional
from dataclasses import dataclass, asdict

from .runtime_profile import RuntimeProfile


@dataclass
class VisionPolicy:
    """视觉分析策略"""
    provider: Literal["local", "cloud"]
    local_backend: Optional[Literal["ollama", "lmstudio"]] = None  # 本地后端类型
    model: str = ""
    device: Literal["cpu", "gpu", "auto"] = "auto"
    max_scenes: int = 10
    timeout: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PlanningPolicy:
    """规划策略"""
    provider: Literal["local", "cloud"]
    model: str
    temperature: float = 0.7
    max_tokens: int = 4000
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EditingPolicy:
    """剪辑策略"""
    executor: Literal["davinci", "premiere", "finalcut"]
    parallelism: int
    preview_quality: Literal["low", "medium", "high"]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionPolicy:
    """完整的执行策略"""
    vision: VisionPolicy
    planning: PlanningPolicy
    editing: EditingPolicy
    profile_class: str
    explanation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "vision": self.vision.to_dict(),
            "planning": self.planning.to_dict(),
            "editing": self.editing.to_dict(),
            "profile_class": self.profile_class,
            "explanation": self.explanation
        }


class ExecutionPolicyResolver:
    """执行策略解析器"""
    
    @staticmethod
    def resolve(profile: RuntimeProfile) -> ExecutionPolicy:
        """
        根据 RuntimeProfile 生成执行策略
        
        Args:
            profile: 运行时配置文件
        
        Returns:
            完整的执行策略
        """
        if profile.profile_class == "LOCAL_GPU_HIGH":
            return ExecutionPolicyResolver._policy_gpu_high(profile)
        elif profile.profile_class == "LOCAL_GPU_MID":
            return ExecutionPolicyResolver._policy_gpu_mid(profile)
        elif profile.profile_class == "LOCAL_GPU_LOW":
            return ExecutionPolicyResolver._policy_gpu_low(profile)
        elif profile.profile_class == "LOCAL_CPU_ONLY":
            return ExecutionPolicyResolver._policy_cpu_only(profile)
        else:
            return ExecutionPolicyResolver._policy_cloud_hybrid(profile)
    
    @staticmethod
    def _policy_gpu_high(profile: RuntimeProfile) -> ExecutionPolicy:
        """
        高端 GPU 策略（4090 工作站）
        
        特点：
        - 全本地运行
        - 使用最好的模型
        - 最大并行度
        """
        # 选择本地后端和模型
        local_backend = None
        vision_model = "moondream"
        
        if profile.ai_runtime.ollama and profile.ai_runtime.ollama_models:
            local_backend = "ollama"
            if "llava-phi3" in profile.ai_runtime.ollama_models:
                vision_model = "llava-phi3"
            elif "moondream" in profile.ai_runtime.ollama_models:
                vision_model = "moondream"
        elif profile.ai_runtime.lmstudio:
            local_backend = "lmstudio"
            vision_model = profile.ai_runtime.lmstudio_model or "auto"
        
        # 选择规划模型
        if "qwen2.5-14b" in profile.ai_runtime.ollama_models:
            planning_model = "qwen2.5-14b"
        elif "deepseek-chat" in profile.ai_runtime.ollama_models:
            planning_model = "deepseek-chat"
        else:
            planning_model = "deepseek-chat"  # 云端
        
        planning_provider = "local" if planning_model in profile.ai_runtime.ollama_models else "cloud"
        
        return ExecutionPolicy(
            vision=VisionPolicy(
                provider="local",
                local_backend=local_backend,
                model=vision_model,
                device="gpu",
                max_scenes=20
            ),
            planning=PlanningPolicy(
                provider=planning_provider,
                model=planning_model
            ),
            editing=EditingPolicy(
                executor="davinci",
                parallelism=1,
                preview_quality="high"
            ),
            profile_class=profile.profile_class,
            explanation="高端 GPU 配置，全本地运行，最佳性能"
        )
    
    @staticmethod
    def _policy_gpu_mid(profile: RuntimeProfile) -> ExecutionPolicy:
        """
        中端 GPU 策略（4060/3060）
        
        特点：
        - 本地 Vision（轻量模型）
        - 云端 Planning
        - 平衡性能和成本
        """
        # 选择本地后端和模型
        local_backend = None
        vision_model = "moondream"
        
        if profile.ai_runtime.ollama and profile.ai_runtime.ollama_models:
            local_backend = "ollama"
            if "moondream" in profile.ai_runtime.ollama_models:
                vision_model = "moondream"
            elif "llava-phi3" in profile.ai_runtime.ollama_models:
                vision_model = "llava-phi3"
        elif profile.ai_runtime.lmstudio:
            local_backend = "lmstudio"
            vision_model = profile.ai_runtime.lmstudio_model or "auto"
        
        return ExecutionPolicy(
            vision=VisionPolicy(
                provider="local",
                local_backend=local_backend,
                model=vision_model,
                device="auto",  # 自动选择
                max_scenes=10
            ),
            planning=PlanningPolicy(
                provider="cloud",
                model="deepseek-chat"
            ),
            editing=EditingPolicy(
                executor="davinci",
                parallelism=1,
                preview_quality="medium"
            ),
            profile_class=profile.profile_class,
            explanation="中端 GPU 配置，本地视觉分析 + 云端规划"
        )
    
    @staticmethod
    def _policy_gpu_low(profile: RuntimeProfile) -> ExecutionPolicy:
        """
        低端 GPU 策略（1660/2060）
        
        特点：
        - 本地 Vision（CPU 模式）
        - 云端 Planning
        - 限制场景数
        """
        # 选择本地后端和模型
        local_backend = None
        vision_model = "moondream"
        
        if profile.ai_runtime.lmstudio:
            # LM Studio 优先（更友好）
            local_backend = "lmstudio"
            vision_model = profile.ai_runtime.lmstudio_model or "auto"
        elif profile.ai_runtime.ollama:
            local_backend = "ollama"
            vision_model = "moondream"
        
        return ExecutionPolicy(
            vision=VisionPolicy(
                provider="local",
                local_backend=local_backend,
                model=vision_model,
                device="cpu",  # 强制 CPU
                max_scenes=5
            ),
            planning=PlanningPolicy(
                provider="cloud",
                model="deepseek-chat"
            ),
            editing=EditingPolicy(
                executor="davinci",
                parallelism=1,
                preview_quality="medium"
            ),
            profile_class=profile.profile_class,
            explanation="低端 GPU 配置，CPU 模式视觉分析 + 云端规划"
        )
    
    @staticmethod
    def _policy_cpu_only(profile: RuntimeProfile) -> ExecutionPolicy:
        """
        纯 CPU 策略（无独显）
        
        特点：
        - 优先本地 Vision（LM Studio/Ollama）
        - 云端 Planning
        - 最小资源占用
        """
        # 检查是否有本地 AI 可用
        if profile.ai_runtime.lmstudio:
            # LM Studio 可用，使用本地
            return ExecutionPolicy(
                vision=VisionPolicy(
                    provider="local",
                    local_backend="lmstudio",
                    model=profile.ai_runtime.lmstudio_model or "auto",
                    device="cpu",
                    max_scenes=10
                ),
                planning=PlanningPolicy(
                    provider="cloud",
                    model="deepseek-chat"
                ),
                editing=EditingPolicy(
                    executor="davinci",
                    parallelism=1,
                    preview_quality="low"
                ),
                profile_class=profile.profile_class,
                explanation="纯 CPU 配置，本地 LM Studio 视觉分析 + 云端规划"
            )
        elif profile.ai_runtime.ollama:
            # Ollama 可用，使用本地
            return ExecutionPolicy(
                vision=VisionPolicy(
                    provider="local",
                    local_backend="ollama",
                    model="moondream",
                    device="cpu",
                    max_scenes=10
                ),
                planning=PlanningPolicy(
                    provider="cloud",
                    model="deepseek-chat"
                ),
                editing=EditingPolicy(
                    executor="davinci",
                    parallelism=1,
                    preview_quality="low"
                ),
                profile_class=profile.profile_class,
                explanation="纯 CPU 配置，本地 Ollama 视觉分析 + 云端规划"
            )
        else:
            # 无本地 AI，使用云端
            return ExecutionPolicy(
                vision=VisionPolicy(
                    provider="cloud",
                    local_backend=None,
                    model="gpt-4o",
                    device="cpu",
                    max_scenes=10
                ),
                planning=PlanningPolicy(
                    provider="cloud",
                    model="deepseek-chat"
                ),
                editing=EditingPolicy(
                    executor="davinci",
                    parallelism=1,
                    preview_quality="low"
                ),
                profile_class=profile.profile_class,
                explanation="纯 CPU 配置，全云端 AI 处理"
            )
    
    @staticmethod
    def _policy_cloud_hybrid(profile: RuntimeProfile) -> ExecutionPolicy:
        """
        云端混合策略
        
        特点：
        - 云端 Vision
        - 云端 Planning
        - 本地 Editing
        """
        return ExecutionPolicy(
            vision=VisionPolicy(
                provider="cloud",
                model="gpt-4o",
                device="cpu",
                max_scenes=10
            ),
            planning=PlanningPolicy(
                provider="cloud",
                model="gpt-4o"
            ),
            editing=EditingPolicy(
                executor="davinci",
                parallelism=1,
                preview_quality="medium"
            ),
            profile_class=profile.profile_class,
            explanation="云端混合模式，AI 处理在云端"
        )
    
    @staticmethod
    def degrade_policy(
        policy: ExecutionPolicy,
        reason: str
    ) -> ExecutionPolicy:
        """
        降级策略
        
        Args:
            policy: 当前策略
            reason: 降级原因
        
        Returns:
            降级后的策略
        """
        # Vision 降级：本地 → 云端
        if policy.vision.provider == "local":
            policy.vision.provider = "cloud"
            policy.vision.model = "gpt-4o"
            policy.vision.device = "cpu"
            policy.explanation = f"已降级: {reason} → 切换到云端视觉分析"
        
        # 减少场景数
        if policy.vision.max_scenes > 5:
            policy.vision.max_scenes = max(5, policy.vision.max_scenes // 2)
            policy.explanation += f" → 减少分析场景数到 {policy.vision.max_scenes}"
        
        return policy


# 全局单例
_execution_policy: Optional[ExecutionPolicy] = None


def get_execution_policy(force_reload: bool = False) -> ExecutionPolicy:
    """获取执行策略（单例）"""
    global _execution_policy
    
    if _execution_policy is None or force_reload:
        from .runtime_profile import get_runtime_profile
        profile = get_runtime_profile()
        _execution_policy = ExecutionPolicyResolver.resolve(profile)
    
    return _execution_policy


def degrade_execution_policy(reason: str) -> ExecutionPolicy:
    """降级执行策略"""
    global _execution_policy
    
    policy = get_execution_policy()
    _execution_policy = ExecutionPolicyResolver.degrade_policy(policy, reason)
    
    # 同时标记 Profile 为降级
    from .runtime_profile import get_runtime_profile
    profile = get_runtime_profile()
    profile.mark_degraded(reason)
    
    return _execution_policy
