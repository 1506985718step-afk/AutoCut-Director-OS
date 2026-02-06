"""
Orchestrator - 全局调度器（状态机 + 资源锁）

职责：
- 管理 Job 状态机
- 控制资源分配（GPU/CPU/Resolve）
- 防止系统崩溃
- 确保任务可暂停/恢复

原则：
- AI = 导演（决策）
- Resolve = 工人（执行）
- Orchestrator = 调度员（协调）
"""
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime
import threading
import psutil


class JobState(Enum):
    """Job 状态枚举"""
    CREATED = "created"
    INGESTING = "ingesting"
    INGESTED = "ingested"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    PLANNING = "planning"
    PLANNED = "planned"
    EXECUTING = "executing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ResourceLock:
    """全局资源锁"""
    
    def __init__(self):
        self._lock = threading.Lock()
        self._locks = {
            "GPU_HEAVY": False,      # Resolve Export/Render
            "VISION_ALLOWED": True,  # 是否允许跑 VLM
            "RESOLVE_BUSY": False,   # Resolve 是否繁忙
            "AI_ALLOWED": True       # 是否允许 AI 调用
        }
    
    def acquire(self, resource: str) -> bool:
        """
        尝试获取资源锁
        
        Args:
            resource: 资源名称
        
        Returns:
            是否成功获取
        """
        with self._lock:
            if self._locks.get(resource, False):
                return False
            self._locks[resource] = True
            return True
    
    def release(self, resource: str):
        """释放资源锁"""
        with self._lock:
            self._locks[resource] = False
    
    def is_locked(self, resource: str) -> bool:
        """检查资源是否被锁定"""
        with self._lock:
            return self._locks.get(resource, False)
    
    def get_status(self) -> Dict[str, bool]:
        """获取所有锁状态"""
        with self._lock:
            return self._locks.copy()


class StateTransition:
    """状态转换规则"""
    
    # 允许的状态转换
    ALLOWED_TRANSITIONS = {
        JobState.CREATED: [JobState.INGESTING, JobState.FAILED],
        JobState.INGESTING: [JobState.INGESTED, JobState.FAILED],
        JobState.INGESTED: [JobState.ANALYZING, JobState.FAILED],
        JobState.ANALYZING: [JobState.ANALYZED, JobState.FAILED, JobState.PAUSED],
        JobState.ANALYZED: [JobState.PLANNING, JobState.FAILED],
        JobState.PLANNING: [JobState.PLANNED, JobState.FAILED, JobState.PAUSED],
        JobState.PLANNED: [JobState.EXECUTING, JobState.FAILED],
        JobState.EXECUTING: [JobState.EXPORTING, JobState.FAILED, JobState.PAUSED],
        JobState.EXPORTING: [JobState.COMPLETED, JobState.FAILED],
        JobState.PAUSED: [JobState.ANALYZING, JobState.PLANNING, JobState.EXECUTING],
        JobState.FAILED: [],
        JobState.COMPLETED: []
    }
    
    # 每个状态的资源需求
    STATE_RESOURCES = {
        JobState.CREATED: {
            "cpu": "low",
            "gpu": "none",
            "resolve": False,
            "vision": False,
            "ai": False
        },
        JobState.INGESTING: {
            "cpu": "medium",
            "gpu": "low",
            "resolve": False,
            "vision": False,
            "ai": False
        },
        JobState.INGESTED: {
            "cpu": "low",
            "gpu": "none",
            "resolve": False,
            "vision": False,
            "ai": False
        },
        JobState.ANALYZING: {
            "cpu": "medium",
            "gpu": "medium",  # 可选，取决于 Resolve 状态
            "resolve": False,  # 禁止 Resolve 操作
            "vision": True,    # 允许 Vision
            "ai": False
        },
        JobState.ANALYZED: {
            "cpu": "low",
            "gpu": "none",
            "resolve": False,
            "vision": False,
            "ai": False
        },
        JobState.PLANNING: {
            "cpu": "low",
            "gpu": "none",
            "resolve": False,
            "vision": False,
            "ai": True  # 云端 AI，最安全
        },
        JobState.PLANNED: {
            "cpu": "low",
            "gpu": "none",
            "resolve": False,
            "vision": False,
            "ai": False
        },
        JobState.EXECUTING: {
            "cpu": "high",
            "gpu": "high",
            "resolve": True,   # Resolve 全权
            "vision": False,   # 禁止 Vision
            "ai": False        # 禁止 AI
        },
        JobState.EXPORTING: {
            "cpu": "critical",
            "gpu": "critical",
            "resolve": True,
            "vision": False,
            "ai": False
        }
    }
    
    @classmethod
    def can_transition(cls, from_state: JobState, to_state: JobState) -> bool:
        """检查是否允许状态转换"""
        allowed = cls.ALLOWED_TRANSITIONS.get(from_state, [])
        return to_state in allowed
    
    @classmethod
    def get_resource_requirements(cls, state: JobState) -> Dict[str, Any]:
        """获取状态的资源需求"""
        return cls.STATE_RESOURCES.get(state, {})


class Orchestrator:
    """全局调度器"""
    
    def __init__(self):
        self.resource_lock = ResourceLock()
        self.current_jobs = {}  # job_id -> JobState
        self._lock = threading.Lock()
    
    def can_enter_state(self, job_id: str, target_state: JobState) -> tuple[bool, str]:
        """
        检查是否可以进入目标状态
        
        Returns:
            (是否可以, 原因)
        """
        # 1. 检查状态转换是否合法
        current_state = self.current_jobs.get(job_id)
        if current_state and not StateTransition.can_transition(current_state, target_state):
            return False, f"不允许从 {current_state.value} 转换到 {target_state.value}"
        
        # 2. 检查资源是否可用
        requirements = StateTransition.get_resource_requirements(target_state)
        
        # ANALYZING: 不能在 Resolve 繁忙时运行
        if target_state == JobState.ANALYZING:
            if self.resource_lock.is_locked("RESOLVE_BUSY"):
                return False, "Resolve 正在繁忙，等待完成"
            if not self.resource_lock.is_locked("VISION_ALLOWED"):
                return False, "Vision 当前不允许运行"
        
        # EXECUTING/EXPORTING: 需要独占资源
        if target_state in [JobState.EXECUTING, JobState.EXPORTING]:
            if self.resource_lock.is_locked("GPU_HEAVY"):
                return False, "GPU 资源被占用"
            if self.resource_lock.is_locked("VISION_ALLOWED"):
                # 需要先停止 Vision
                return False, "需要先停止 Vision 任务"
        
        return True, "OK"
    
    def enter_state(self, job_id: str, state: JobState):
        """
        进入新状态（更新资源锁）
        
        铁律：
        1. 任何时间只允许一个 GPU-heavy 任务
        2. Resolve Export > 一切 AI
        3. Vision 失败 ≠ Job 失败
        """
        with self._lock:
            print(f"\n🎬 [{job_id}] 进入状态: {state.value}")
            
            # 更新状态
            old_state = self.current_jobs.get(job_id)
            self.current_jobs[job_id] = state
            
            # 根据状态更新资源锁
            if state == JobState.ANALYZING:
                # Vision 阶段：允许 Vision，禁止 Resolve
                assert not self.resource_lock.is_locked("RESOLVE_BUSY"), "Resolve 必须空闲"
                self.resource_lock.acquire("VISION_ALLOWED")
                print("  ✓ Vision 已启用")
            
            elif state == JobState.PLANNING:
                # Planning 阶段：最安全，只用云端 AI
                self.resource_lock.acquire("AI_ALLOWED")
                print("  ✓ AI 规划已启用（云端）")
            
            elif state in [JobState.EXECUTING, JobState.EXPORTING]:
                # 执行/导出阶段：Resolve 全权，禁止一切 AI
                self.resource_lock.release("VISION_ALLOWED")
                self.resource_lock.release("AI_ALLOWED")
                self.resource_lock.acquire("GPU_HEAVY")
                self.resource_lock.acquire("RESOLVE_BUSY")
                
                print("  🔥 GPU 高负载模式")
                print("  🚫 Vision 已禁用")
                print("  🚫 AI 已禁用")
                print("  ✓ Resolve 全权控制")
            
            # 显示资源状态
            status = self.resource_lock.get_status()
            print(f"  资源状态: {status}")
    
    def exit_state(self, job_id: str, state: JobState):
        """退出状态（释放资源锁）"""
        with self._lock:
            print(f"\n🎬 [{job_id}] 退出状态: {state.value}")
            
            # 根据状态释放资源锁
            if state == JobState.ANALYZING:
                self.resource_lock.release("VISION_ALLOWED")
                print("  ✓ Vision 已释放")
            
            elif state == JobState.PLANNING:
                self.resource_lock.release("AI_ALLOWED")
                print("  ✓ AI 已释放")
            
            elif state in [JobState.EXECUTING, JobState.EXPORTING]:
                self.resource_lock.release("GPU_HEAVY")
                self.resource_lock.release("RESOLVE_BUSY")
                self.resource_lock.acquire("VISION_ALLOWED")  # 重新允许 Vision
                
                print("  ✓ GPU 已释放")
                print("  ✓ Resolve 已释放")
                print("  ✓ Vision 重新启用")
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        
        return {
            "resource_locks": self.resource_lock.get_status(),
            "active_jobs": {
                job_id: state.value
                for job_id, state in self.current_jobs.items()
            },
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3)
            }
        }
    
    def should_use_cpu_for_vision(self) -> bool:
        """
        判断 Vision 是否应该使用 CPU 模式
        
        规则：
        - 如果 GPU 被 Resolve 占用 → 强制 CPU
        - 如果系统资源紧张 → 强制 CPU
        """
        if self.resource_lock.is_locked("GPU_HEAVY"):
            return True
        
        if self.resource_lock.is_locked("RESOLVE_BUSY"):
            return True
        
        # 检查 GPU 使用率（如果可用）
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus and gpus[0].load > 0.7:  # GPU 使用率 > 70%
                return True
        except:
            pass
        
        return False


# 全局单例
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    """获取全局调度器单例"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
