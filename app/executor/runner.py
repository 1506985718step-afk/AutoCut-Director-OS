"""动作队列执行器 + trace 日志（简化版）"""
import time
import json
from pathlib import Path
from typing import List
from .resolve_adapter import connect_resolve
from .actions import Action, execute_action


def run_actions(actions: List[Action], trace_path: str = None) -> list:
    """
    执行动作队列并记录 trace
    
    Args:
        actions: Action 对象列表
        trace_path: trace 文件保存路径（可选）
        
    Returns:
        trace 列表
        
    设计原则：Executor 只跑动作，不关心业务逻辑
    """
    # 连接 Resolve
    resolve, proj = connect_resolve()
    
    # 创建 adapter（用于执行动作）
    from .resolve_adapter import ResolveAdapter
    adapter = ResolveAdapter()
    adapter.resolve = resolve
    adapter.project = proj
    adapter.media_pool = proj.GetMediaPool()
    
    trace = []
    
    # 执行每个动作
    for act in actions:
        t0 = time.time()
        ok, detail = True, {}
        
        try:
            # 数据驱动：根据 action.name 执行对应操作
            result = execute_action(act, adapter)
            detail = {"result": str(result) if result else "success"}
            
        except Exception as e:
            ok, detail = False, {"error": str(e)}
        
        # 记录 trace
        trace.append({
            "action": act.name,
            "params": act.params,
            "ok": ok,
            "detail": detail,
            "took_ms": int((time.time() - t0) * 1000)
        })
        
        # 如果失败，停止执行
        if not ok:
            break
    
    # 保存 trace（如果提供了路径）
    if trace_path:
        Path(trace_path).write_text(
            json.dumps(trace, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    return trace


class Runner:
    """
    Runner 类（兼容现有代码）
    
    内部使用 run_actions() 函数
    """
    
    def __init__(self, job_id: str = None):
        self.job_id = job_id
        self.trace = []
        
    def run(self, actions: List[Action]):
        """执行动作队列"""
        trace_path = f"jobs/{self.job_id}/trace.json" if self.job_id else None
        self.trace = run_actions(actions, trace_path)
    
    def get_trace(self) -> list:
        """获取执行 trace"""
        return self.trace
