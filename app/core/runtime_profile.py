"""
Runtime Profile - 运行时配置文件

功能：
1. 自动检测硬件配置
2. 生成运行时 Profile
3. 动态监控系统状态
4. 自适应降级策略

核心协议：让系统"知道自己在干什么"
"""
import psutil
import platform
from typing import Dict, Any, Optional, Literal
from dataclasses import dataclass, asdict
from pathlib import Path
import json


@dataclass
class CPUProfile:
    """CPU 配置"""
    cores: int
    threads: int
    score: Literal["low", "medium", "high", "ultra"]
    
    @classmethod
    def detect(cls) -> "CPUProfile":
        """自动检测 CPU"""
        cores = psutil.cpu_count(logical=False) or 4
        threads = psutil.cpu_count(logical=True) or 8
        
        # 评分规则
        if threads >= 16:
            score = "ultra"
        elif threads >= 12:
            score = "high"
        elif threads >= 8:
            score = "medium"
        else:
            score = "low"
        
        return cls(cores=cores, threads=threads, score=score)


@dataclass
class MemoryProfile:
    """内存配置"""
    total_gb: float
    available_gb: float
    
    @classmethod
    def detect(cls) -> "MemoryProfile":
        """自动检测内存"""
        memory = psutil.virtual_memory()
        total_gb = memory.total / (1024**3)
        available_gb = memory.available / (1024**3)
        
        return cls(total_gb=round(total_gb, 1), available_gb=round(available_gb, 1))


@dataclass
class GPUProfile:
    """GPU 配置"""
    vendor: str
    model: str
    vram_gb: float
    cuda: bool
    
    @classmethod
    def detect(cls) -> Optional["GPUProfile"]:
        """自动检测 GPU"""
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            
            if gpus:
                gpu = gpus[0]
                return cls(
                    vendor="NVIDIA",
                    model=gpu.name,
                    vram_gb=round(gpu.memoryTotal / 1024, 1),
                    cuda=True
                )
        except:
            pass
        
        # 尝试检测 AMD/Intel
        try:
            import wmi
            w = wmi.WMI()
            for gpu in w.Win32_VideoController():
                if "AMD" in gpu.Name or "Radeon" in gpu.Name:
                    return cls(
                        vendor="AMD",
                        model=gpu.Name,
                        vram_gb=0.0,  # 无法准确获取
                        cuda=False
                    )
                elif "Intel" in gpu.Name:
                    return cls(
                        vendor="Intel",
                        model=gpu.Name,
                        vram_gb=0.0,
                        cuda=False
                    )
        except:
            pass
        
        return None


@dataclass
class AIRuntimeProfile:
    """AI 运行时配置"""
    ollama: bool
    ollama_models: list[str]
    lmstudio: bool
    lmstudio_model: Optional[str]
    cuda_available: bool
    
    @classmethod
    def detect(cls) -> "AIRuntimeProfile":
        """自动检测 AI 运行时"""
        import requests
        
        # 检测 Ollama
        ollama = False
        ollama_models = []
        
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=2)
            if response.status_code == 200:
                ollama = True
                models = response.json().get("models", [])
                ollama_models = [m.get("name", "").split(":")[0] for m in models]
        except:
            pass
        
        # 检测 LM Studio
        lmstudio = False
        lmstudio_model = None
        
        try:
            response = requests.get("http://localhost:1234/v1/models", timeout=2)
            if response.status_code == 200:
                lmstudio = True
                data = response.json()
                models = data.get("data", [])
                if models:
                    lmstudio_model = models[0].get("id", "unknown")
        except:
            pass
        
        # 检测 CUDA
        cuda_available = False
        try:
            import torch
            cuda_available = torch.cuda.is_available()
        except:
            pass
        
        return cls(
            ollama=ollama,
            ollama_models=ollama_models,
            lmstudio=lmstudio,
            lmstudio_model=lmstudio_model,
            cuda_available=cuda_available
        )


@dataclass
class EditorProfile:
    """编辑器配置"""
    davinci: Dict[str, Any]
    
    @classmethod
    def detect(cls) -> "EditorProfile":
        """自动检测编辑器"""
        davinci = {
            "installed": False,
            "version": None,
            "scriptable": False
        }
        
        # 检测 DaVinci Resolve
        try:
            import sys
            sys.path.append(r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules")
            import DaVinciResolveScript as dvr
            
            resolve = dvr.scriptapp("Resolve")
            if resolve:
                davinci["installed"] = True
                davinci["scriptable"] = True
                # 尝试获取版本
                try:
                    version = resolve.GetVersion()
                    davinci["version"] = version
                except:
                    davinci["version"] = "unknown"
        except:
            pass
        
        return cls(davinci=davinci)


@dataclass
class RuntimeProfile:
    """完整的运行时配置文件"""
    cpu: CPUProfile
    memory: MemoryProfile
    gpu: Optional[GPUProfile]
    ai_runtime: AIRuntimeProfile
    editor: EditorProfile
    os: str
    profile_class: Literal[
        "LOCAL_GPU_HIGH",    # 4090 工作站
        "LOCAL_GPU_MID",     # 4060/3060 级别
        "LOCAL_GPU_LOW",     # 1660/2060 级别
        "LOCAL_CPU_ONLY",    # 无独显
        "CLOUD_HYBRID"       # 混合模式
    ]
    degraded: bool = False  # 是否已降级
    degradation_reason: Optional[str] = None
    
    @classmethod
    def detect(cls) -> "RuntimeProfile":
        """自动检测完整配置"""
        cpu = CPUProfile.detect()
        memory = MemoryProfile.detect()
        gpu = GPUProfile.detect()
        ai_runtime = AIRuntimeProfile.detect()
        editor = EditorProfile.detect()
        os_name = platform.system()
        
        # 判断 profile_class
        profile_class = cls._classify_profile(cpu, memory, gpu, ai_runtime)
        
        return cls(
            cpu=cpu,
            memory=memory,
            gpu=gpu,
            ai_runtime=ai_runtime,
            editor=editor,
            os=os_name,
            profile_class=profile_class
        )
    
    @staticmethod
    def _classify_profile(
        cpu: CPUProfile,
        memory: MemoryProfile,
        gpu: Optional[GPUProfile],
        ai_runtime: AIRuntimeProfile
    ) -> str:
        """分类 Profile"""
        if not gpu or not gpu.cuda:
            return "LOCAL_CPU_ONLY"
        
        # 根据显存分类
        if gpu.vram_gb >= 16:
            return "LOCAL_GPU_HIGH"
        elif gpu.vram_gb >= 8:
            return "LOCAL_GPU_MID"
        elif gpu.vram_gb >= 4:
            return "LOCAL_GPU_LOW"
        else:
            return "LOCAL_CPU_ONLY"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "cpu": asdict(self.cpu),
            "memory": asdict(self.memory),
            "gpu": asdict(self.gpu) if self.gpu else None,
            "ai_runtime": asdict(self.ai_runtime),
            "editor": asdict(self.editor),
            "os": self.os,
            "profile_class": self.profile_class,
            "degraded": self.degraded,
            "degradation_reason": self.degradation_reason
        }
    
    def save(self, path: Path):
        """保存到文件"""
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load(cls, path: Path) -> "RuntimeProfile":
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        return cls(
            cpu=CPUProfile(**data["cpu"]),
            memory=MemoryProfile(**data["memory"]),
            gpu=GPUProfile(**data["gpu"]) if data["gpu"] else None,
            ai_runtime=AIRuntimeProfile(**data["ai_runtime"]),
            editor=EditorProfile(**data["editor"]),
            os=data["os"],
            profile_class=data["profile_class"],
            degraded=data.get("degraded", False),
            degradation_reason=data.get("degradation_reason")
        )
    
    def mark_degraded(self, reason: str):
        """标记为已降级"""
        self.degraded = True
        self.degradation_reason = reason
    
    def get_explanation(self) -> str:
        """生成用户友好的解释"""
        lines = ["🧠 系统运行模式"]
        
        # 硬件说明
        if self.gpu and self.gpu.cuda:
            lines.append(f"- 检测到 {self.gpu.vendor} {self.gpu.model} ({self.gpu.vram_gb}GB 显存)")
        else:
            lines.append("- 未检测到独立显卡")
        
        lines.append(f"- CPU: {self.cpu.threads} 线程 ({self.cpu.score} 性能)")
        lines.append(f"- 内存: {self.memory.total_gb}GB (可用 {self.memory.available_gb}GB)")
        
        # AI 运行时
        if self.ai_runtime.ollama:
            lines.append(f"- 本地 AI (Ollama): {len(self.ai_runtime.ollama_models)} 个模型")
        elif self.ai_runtime.lmstudio:
            lines.append(f"- 本地 AI (LM Studio): {self.ai_runtime.lmstudio_model}")
        else:
            lines.append("- 本地 AI: 未安装")
        
        # 降级说明
        if self.degraded:
            lines.append(f"\n⚠️  已自动降级: {self.degradation_reason}")
        
        # 运行策略
        lines.append(f"\n📊 运行级别: {self.profile_class}")
        
        return "\n".join(lines)


# 全局单例
_runtime_profile: Optional[RuntimeProfile] = None


def get_runtime_profile(force_reload: bool = False) -> RuntimeProfile:
    """获取运行时配置文件（单例）"""
    global _runtime_profile
    
    if _runtime_profile is None or force_reload:
        _runtime_profile = RuntimeProfile.detect()
    
    return _runtime_profile


def save_runtime_profile(path: Path):
    """保存运行时配置文件"""
    profile = get_runtime_profile()
    profile.save(path)


def load_runtime_profile(path: Path) -> RuntimeProfile:
    """加载运行时配置文件"""
    global _runtime_profile
    _runtime_profile = RuntimeProfile.load(path)
    return _runtime_profile
