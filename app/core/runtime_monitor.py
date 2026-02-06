"""
Runtime Monitor - 运行时动态监控

功能：
1. 监控 GPU 显存使用率
2. 监控 Resolve 状态
3. 监控内存压力
4. 监控任务失败率
5. 自动触发降级

核心：让系统"知道自己在干什么"
"""
import psutil
import threading
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class MonitorMetrics:
    """监控指标"""
    timestamp: datetime
    gpu_vram_used_percent: float
    gpu_vram_used_gb: float
    gpu_vram_total_gb: float
    memory_used_percent: float
    memory_available_gb: float
    cpu_percent: float
    resolve_busy: bool
    task_failure_rate: float


class RuntimeMonitor:
    """运行时监控器"""
    
    def __init__(self, check_interval: int = 5):
        """
        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._metrics_history = []
        self._max_history = 100
        
        # 降级回调
        self._degradation_callbacks: list[Callable[[str], None]] = []
        
        # 任务统计
        self._task_total = 0
        self._task_failed = 0
        
        # 降级标志
        self._degraded = False
        self._degradation_reason = None
    
    def register_degradation_callback(self, callback: Callable[[str], None]):
        """注册降级回调函数"""
        self._degradation_callbacks.append(callback)
    
    def start(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        print("🔍 Runtime Monitor 已启动")
    
    def stop(self):
        """停止监控"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("🔍 Runtime Monitor 已停止")
    
    def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                metrics = self._collect_metrics()
                self._metrics_history.append(metrics)
                
                # 限制历史记录数量
                if len(self._metrics_history) > self._max_history:
                    self._metrics_history.pop(0)
                
                # 检查是否需要降级
                self._check_degradation(metrics)
                
            except Exception as e:
                print(f"⚠️  监控错误: {e}")
            
            time.sleep(self.check_interval)
    
    def _collect_metrics(self) -> MonitorMetrics:
        """收集监控指标"""
        # CPU 和内存
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_used_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # GPU 显存
        gpu_vram_used_percent = 0.0
        gpu_vram_used_gb = 0.0
        gpu_vram_total_gb = 0.0
        
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_vram_total_gb = gpu.memoryTotal / 1024
                gpu_vram_used_gb = gpu.memoryUsed / 1024
                gpu_vram_used_percent = (gpu_vram_used_gb / gpu_vram_total_gb) * 100
        except:
            pass
        
        # Resolve 状态（从 Orchestrator 获取）
        resolve_busy = False
        try:
            from .orchestrator import get_orchestrator
            orchestrator = get_orchestrator()
            resolve_busy = orchestrator.resource_lock.is_locked("RESOLVE_BUSY")
        except:
            pass
        
        # 任务失败率
        task_failure_rate = 0.0
        if self._task_total > 0:
            task_failure_rate = self._task_failed / self._task_total
        
        return MonitorMetrics(
            timestamp=datetime.now(),
            gpu_vram_used_percent=gpu_vram_used_percent,
            gpu_vram_used_gb=gpu_vram_used_gb,
            gpu_vram_total_gb=gpu_vram_total_gb,
            memory_used_percent=memory_used_percent,
            memory_available_gb=memory_available_gb,
            cpu_percent=cpu_percent,
            resolve_busy=resolve_busy,
            task_failure_rate=task_failure_rate
        )
    
    def _check_degradation(self, metrics: MonitorMetrics):
        """检查是否需要降级"""
        if self._degraded:
            return  # 已经降级，不再重复
        
        # 规则 1: GPU 显存 > 85%
        if metrics.gpu_vram_used_percent > 85:
            reason = f"GPU 显存使用率过高 ({metrics.gpu_vram_used_percent:.1f}%)"
            self._trigger_degradation(reason)
            return
        
        # 规则 2: 内存 < 2GB
        if metrics.memory_available_gb < 2.0:
            reason = f"可用内存不足 ({metrics.memory_available_gb:.1f}GB)"
            self._trigger_degradation(reason)
            return
        
        # 规则 3: 任务失败率 > 30%
        if self._task_total >= 5 and metrics.task_failure_rate > 0.3:
            reason = f"任务失败率过高 ({metrics.task_failure_rate*100:.1f}%)"
            self._trigger_degradation(reason)
            return
    
    def _trigger_degradation(self, reason: str):
        """触发降级"""
        print(f"\n⚠️  触发自动降级: {reason}")
        
        self._degraded = True
        self._degradation_reason = reason
        
        # 调用所有降级回调
        for callback in self._degradation_callbacks:
            try:
                callback(reason)
            except Exception as e:
                print(f"⚠️  降级回调错误: {e}")
    
    def record_task_result(self, success: bool):
        """记录任务结果"""
        self._task_total += 1
        if not success:
            self._task_failed += 1
    
    def get_current_metrics(self) -> Optional[MonitorMetrics]:
        """获取当前指标"""
        if not self._metrics_history:
            return None
        return self._metrics_history[-1]
    
    def get_metrics_history(self, minutes: int = 5) -> list[MonitorMetrics]:
        """获取历史指标"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [
            m for m in self._metrics_history
            if m.timestamp >= cutoff
        ]
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        current = self.get_current_metrics()
        
        if not current:
            return {
                "running": self._running,
                "degraded": self._degraded,
                "degradation_reason": self._degradation_reason,
                "metrics": None
            }
        
        return {
            "running": self._running,
            "degraded": self._degraded,
            "degradation_reason": self._degradation_reason,
            "metrics": {
                "timestamp": current.timestamp.isoformat(),
                "gpu": {
                    "vram_used_percent": round(current.gpu_vram_used_percent, 1),
                    "vram_used_gb": round(current.gpu_vram_used_gb, 1),
                    "vram_total_gb": round(current.gpu_vram_total_gb, 1)
                },
                "memory": {
                    "used_percent": round(current.memory_used_percent, 1),
                    "available_gb": round(current.memory_available_gb, 1)
                },
                "cpu": {
                    "percent": round(current.cpu_percent, 1)
                },
                "resolve_busy": current.resolve_busy,
                "task_failure_rate": round(current.task_failure_rate * 100, 1)
            },
            "task_stats": {
                "total": self._task_total,
                "failed": self._task_failed,
                "success_rate": round((1 - current.task_failure_rate) * 100, 1) if self._task_total > 0 else 100.0
            }
        }
    
    def should_use_cpu_for_vision(self) -> bool:
        """判断是否应该使用 CPU 模式进行视觉分析"""
        current = self.get_current_metrics()
        
        if not current:
            return False
        
        # GPU 显存 > 70% → CPU 模式
        if current.gpu_vram_used_percent > 70:
            return True
        
        # Resolve 繁忙 → CPU 模式
        if current.resolve_busy:
            return True
        
        # 内存 < 4GB → CPU 模式
        if current.memory_available_gb < 4.0:
            return True
        
        return False


# 全局单例
_runtime_monitor: Optional[RuntimeMonitor] = None


def get_runtime_monitor() -> RuntimeMonitor:
    """获取运行时监控器单例"""
    global _runtime_monitor
    if _runtime_monitor is None:
        _runtime_monitor = RuntimeMonitor()
    return _runtime_monitor


def start_runtime_monitor():
    """启动运行时监控"""
    monitor = get_runtime_monitor()
    monitor.start()


def stop_runtime_monitor():
    """停止运行时监控"""
    monitor = get_runtime_monitor()
    monitor.stop()
