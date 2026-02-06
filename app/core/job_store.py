"""任务存储管理 - 管理 job 目录和状态（集成状态机）"""
from pathlib import Path
from datetime import datetime
import json
import uuid
from typing import Optional, Dict, Any

from ..config import settings
from .orchestrator import get_orchestrator, JobState


class JobStore:
    """任务存储管理器"""
    
    def __init__(self):
        self.jobs_dir = settings.JOBS_DIR
        self.jobs_dir.mkdir(exist_ok=True)
    
    def create_job(self) -> str:
        """创建新任务，返回 job_id"""
        job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(exist_ok=True)
        
        # 创建子目录
        (job_dir / "input").mkdir(exist_ok=True)
        (job_dir / "temp").mkdir(exist_ok=True)
        (job_dir / "output").mkdir(exist_ok=True)
        
        # 初始化任务元数据
        metadata = {
            "job_id": job_id,
            "state": JobState.CREATED.value,
            "status": "created",
            "progress": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "error": None,
            "result": None,
            "state_history": [
                {
                    "state": JobState.CREATED.value,
                    "timestamp": datetime.now().isoformat()
                }
            ]
        }
        
        self._save_metadata(job_id, metadata)
        
        # 注册到调度器
        orchestrator = get_orchestrator()
        orchestrator.enter_state(job_id, JobState.CREATED)
        
        return job_id
    
    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        metadata_path = self.jobs_dir / job_id / "metadata.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_job_artifacts(self, job_id: str) -> Dict[str, Any]:
        """
        获取任务的所有产物文件
        
        Returns:
            {
                "input": [...],
                "temp": [...],
                "output": [...]
            }
        """
        job_dir = self.jobs_dir / job_id
        
        if not job_dir.exists():
            return {}
        
        artifacts = {
            "input": [],
            "temp": [],
            "output": []
        }
        
        # 扫描各个目录
        for category in ["input", "temp", "output"]:
            category_dir = job_dir / category
            if category_dir.exists():
                for file_path in category_dir.iterdir():
                    if file_path.is_file():
                        file_info = {
                            "name": file_path.name,
                            "path": str(file_path.relative_to(self.jobs_dir)),
                            "size": file_path.stat().st_size,
                            "modified": datetime.fromtimestamp(
                                file_path.stat().st_mtime
                            ).isoformat()
                        }
                        artifacts[category].append(file_info)
        
        return artifacts
    
    def get_job_trace(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        获取任务的最近执行 trace
        
        Returns:
            {
                "total_actions": 10,
                "successful": 9,
                "failed": 1,
                "total_time_ms": 5432,
                "actions": [...]
            }
        """
        trace_path = self.jobs_dir / job_id / "output" / "trace.json"
        
        if not trace_path.exists():
            return None
        
        with open(trace_path, "r", encoding="utf-8") as f:
            trace_data = json.load(f)
        
        # 生成摘要
        if isinstance(trace_data, list):
            total = len(trace_data)
            successful = sum(1 for t in trace_data if t.get("ok", False))
            failed = total - successful
            total_time = sum(t.get("took_ms", 0) for t in trace_data)
            
            return {
                "total_actions": total,
                "successful": successful,
                "failed": failed,
                "total_time_ms": total_time,
                "actions": trace_data
            }
        
        return trace_data
    
    def transition_state(
        self,
        job_id: str,
        target_state: JobState,
        force: bool = False
    ) -> tuple[bool, str]:
        """
        转换 Job 状态（通过调度器）
        
        Args:
            job_id: 任务 ID
            target_state: 目标状态
            force: 是否强制转换（跳过检查）
        
        Returns:
            (是否成功, 消息)
        """
        orchestrator = get_orchestrator()
        
        # 检查是否可以转换
        if not force:
            can_enter, reason = orchestrator.can_enter_state(job_id, target_state)
            if not can_enter:
                return False, reason
        
        # 获取当前状态
        metadata = self.get_job(job_id)
        if not metadata:
            return False, f"任务不存在: {job_id}"
        
        current_state_str = metadata.get("state", JobState.CREATED.value)
        current_state = JobState(current_state_str)
        
        # 退出旧状态
        orchestrator.exit_state(job_id, current_state)
        
        # 进入新状态
        orchestrator.enter_state(job_id, target_state)
        
        # 更新元数据
        metadata["state"] = target_state.value
        metadata["status"] = target_state.value
        metadata["updated_at"] = datetime.now().isoformat()
        
        # 记录状态历史
        if "state_history" not in metadata:
            metadata["state_history"] = []
        
        metadata["state_history"].append({
            "state": target_state.value,
            "timestamp": datetime.now().isoformat()
        })
        
        self._save_metadata(job_id, metadata)
        
        return True, f"已转换到 {target_state.value}"
    
    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        progress: Optional[int] = None,
        error: Optional[Any] = None,
        result: Optional[Any] = None,
        state: Optional[JobState] = None
    ):
        """更新任务状态"""
        metadata = self.get_job(job_id)
        if not metadata:
            raise ValueError(f"任务不存在: {job_id}")
        
        # 如果指定了新状态，使用状态机转换
        if state:
            success, message = self.transition_state(job_id, state)
            if not success:
                raise RuntimeError(f"状态转换失败: {message}")
        
        if status:
            metadata["status"] = status
        if progress is not None:
            metadata["progress"] = progress
        if error is not None:
            metadata["error"] = error
            # 错误时自动转换到 FAILED 状态
            if not state:
                self.transition_state(job_id, JobState.FAILED, force=True)
        if result is not None:
            metadata["result"] = result
        
        metadata["updated_at"] = datetime.now().isoformat()
        
        self._save_metadata(job_id, metadata)
    
    def list_jobs(self, limit: int = 50) -> list:
        """列出所有任务"""
        jobs = []
        
        for job_dir in sorted(self.jobs_dir.iterdir(), reverse=True):
            if job_dir.is_dir():
                metadata = self.get_job(job_dir.name)
                if metadata:
                    jobs.append(metadata)
                
                if len(jobs) >= limit:
                    break
        
        return jobs
    
    def delete_job(self, job_id: str):
        """删除任务"""
        job_dir = self.jobs_dir / job_id
        if job_dir.exists():
            import shutil
            shutil.rmtree(job_dir)
    
    def _save_metadata(self, job_id: str, metadata: dict):
        """保存任务元数据"""
        metadata_path = self.jobs_dir / job_id / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
