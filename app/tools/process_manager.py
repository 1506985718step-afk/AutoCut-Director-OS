"""
OS 进程管理器 - 赋予 AI "生命权"（增强版）

功能：
1. 检测 DaVinci Resolve 是否运行
2. 自动启动 Resolve
3. 监控进程状态
4. 优雅关闭进程

增强功能：
- 支持环境变量 RESOLVE_EXECUTABLE_PATH 自定义路径
- 支持多盘符安装（C/D/E/F 盘）
- 支持 Steam 版本路径
- 更详细的路径查找日志
"""
import psutil
import subprocess
import time
import os
from pathlib import Path
from typing import Optional, Dict, Any
import platform


class ProcessManager:
    """OS 进程管理器"""
    
    def __init__(self):
        """初始化进程管理器"""
        self.system = platform.system()
        self.resolve_process_name = self._get_resolve_process_name()
        self.resolve_executable = self._find_resolve_executable()
    
    def _get_resolve_process_name(self) -> str:
        """获取 Resolve 进程名称"""
        if self.system == "Windows":
            return "Resolve.exe"
        elif self.system == "Darwin":  # macOS
            return "DaVinci Resolve"
        else:  # Linux
            return "resolve"
    
    def _find_resolve_executable(self) -> Optional[Path]:
        """
        查找 Resolve 可执行文件路径（增强版）
        
        查找顺序：
        1. 环境变量 RESOLVE_EXECUTABLE_PATH
        2. 常见安装路径（多盘符支持）
        3. Steam 安装路径
        """
        # 1. 优先检查环境变量
        custom_path = os.environ.get("RESOLVE_EXECUTABLE_PATH")
        if custom_path:
            path = Path(custom_path)
            if path.exists():
                print(f"✓ 使用自定义路径: {path}")
                return path
            else:
                print(f"⚠️ 环境变量路径不存在: {custom_path}")
        
        # 2. 检查常见安装路径
        if self.system == "Windows":
            # Windows 常见安装路径（支持多盘符）
            possible_paths = []
            
            # 遍历常见盘符 C, D, E, F
            for drive in ['C', 'D', 'E', 'F']:
                possible_paths.extend([
                    Path(f"{drive}:/Program Files/Blackmagic Design/DaVinci Resolve/Resolve.exe"),
                    Path(f"{drive}:/Program Files (x86)/Blackmagic Design/DaVinci Resolve/Resolve.exe"),
                    # Steam 路径
                    Path(f"{drive}:/Program Files (x86)/Steam/steamapps/common/DaVinci Resolve/Resolve.exe"),
                    Path(f"{drive}:/Steam/steamapps/common/DaVinci Resolve/Resolve.exe"),
                ])
            
        elif self.system == "Darwin":  # macOS
            possible_paths = [
                Path("/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/MacOS/Resolve"),
                Path("/Applications/DaVinci Resolve Studio/DaVinci Resolve Studio.app/Contents/MacOS/Resolve"),
            ]
        else:  # Linux
            possible_paths = [
                Path("/opt/resolve/bin/resolve"),
                Path("/usr/local/bin/resolve"),
                Path("~/resolve/bin/resolve").expanduser(),
            ]
        
        # 查找第一个存在的路径
        for path in possible_paths:
            if path.exists():
                print(f"✓ 找到 Resolve: {path}")
                return path
        
        # 未找到
        print("❌ 未找到 DaVinci Resolve 可执行文件")
        print("请设置环境变量 RESOLVE_EXECUTABLE_PATH 指向 Resolve.exe")
        print("例如: set RESOLVE_EXECUTABLE_PATH=D:\\Program Files\\Blackmagic Design\\DaVinci Resolve\\Resolve.exe")
        return None
    
    def is_resolve_running(self) -> bool:
        """
        检测 DaVinci Resolve 是否正在运行
        
        Returns:
            True 如果 Resolve 正在运行
        """
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == self.resolve_process_name:
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return False
    
    def get_resolve_process(self) -> Optional[psutil.Process]:
        """
        获取 Resolve 进程对象
        
        Returns:
            psutil.Process 对象，如果未运行则返回 None
        """
        for proc in psutil.process_iter(['name', 'pid', 'memory_info', 'cpu_percent']):
            try:
                if proc.info['name'] == self.resolve_process_name:
                    return proc
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return None
    
    def get_resolve_status(self) -> Dict[str, Any]:
        """
        获取 Resolve 进程状态
        
        Returns:
            {
                "running": True/False,
                "pid": 12345,
                "memory_mb": 1024.5,
                "cpu_percent": 15.3,
                "uptime_seconds": 3600
            }
        """
        proc = self.get_resolve_process()
        
        if not proc:
            return {
                "running": False,
                "pid": None,
                "memory_mb": 0,
                "cpu_percent": 0,
                "uptime_seconds": 0
            }
        
        try:
            memory_info = proc.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)  # 转换为 MB
            
            # 获取 CPU 使用率（需要一点时间采样）
            cpu_percent = proc.cpu_percent(interval=0.1)
            
            # 计算运行时间
            create_time = proc.create_time()
            uptime_seconds = time.time() - create_time
            
            return {
                "running": True,
                "pid": proc.pid,
                "memory_mb": round(memory_mb, 2),
                "cpu_percent": round(cpu_percent, 2),
                "uptime_seconds": int(uptime_seconds)
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {
                "running": False,
                "pid": None,
                "memory_mb": 0,
                "cpu_percent": 0,
                "uptime_seconds": 0
            }
    
    def start_resolve(self, wait_for_startup: bool = True, timeout: int = 60) -> bool:
        """
        启动 DaVinci Resolve
        
        Args:
            wait_for_startup: 是否等待启动完成
            timeout: 超时时间（秒）
        
        Returns:
            True 如果启动成功
        """
        # 检查是否已经运行
        if self.is_resolve_running():
            print("✓ DaVinci Resolve 已经在运行")
            return True
        
        # 检查可执行文件
        if not self.resolve_executable:
            print("❌ 找不到 DaVinci Resolve 可执行文件")
            print("请手动启动 Resolve 或设置正确的安装路径")
            return False
        
        print(f"🚀 正在启动 DaVinci Resolve...")
        print(f"   路径: {self.resolve_executable}")
        
        try:
            # 启动进程
            if self.system == "Windows":
                # Windows: 使用 subprocess.Popen
                subprocess.Popen(
                    [str(self.resolve_executable)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
                )
            else:
                # macOS/Linux: 使用 subprocess.Popen
                subprocess.Popen(
                    [str(self.resolve_executable)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
            
            if wait_for_startup:
                # 等待进程启动
                print("   等待启动...")
                start_time = time.time()
                
                while time.time() - start_time < timeout:
                    if self.is_resolve_running():
                        elapsed = time.time() - start_time
                        print(f"✓ DaVinci Resolve 已启动（耗时 {elapsed:.1f} 秒）")
                        
                        # 额外等待几秒，确保完全启动
                        time.sleep(5)
                        return True
                    
                    time.sleep(1)
                
                print(f"⚠️ 启动超时（{timeout} 秒）")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 启动失败: {e}")
            return False
    
    def stop_resolve(self, force: bool = False) -> bool:
        """
        停止 DaVinci Resolve
        
        Args:
            force: 是否强制终止
        
        Returns:
            True 如果停止成功
        """
        proc = self.get_resolve_process()
        
        if not proc:
            print("✓ DaVinci Resolve 未运行")
            return True
        
        try:
            if force:
                print("🛑 强制终止 DaVinci Resolve...")
                proc.kill()
            else:
                print("🛑 优雅关闭 DaVinci Resolve...")
                proc.terminate()
                
                # 等待进程结束
                try:
                    proc.wait(timeout=30)
                except psutil.TimeoutExpired:
                    print("⚠️ 优雅关闭超时，强制终止...")
                    proc.kill()
            
            print("✓ DaVinci Resolve 已停止")
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            print(f"❌ 停止失败: {e}")
            return False
    
    def restart_resolve(self, wait_for_startup: bool = True) -> bool:
        """
        重启 DaVinci Resolve
        
        Args:
            wait_for_startup: 是否等待启动完成
        
        Returns:
            True 如果重启成功
        """
        print("🔄 重启 DaVinci Resolve...")
        
        # 停止
        if not self.stop_resolve():
            return False
        
        # 等待完全停止
        time.sleep(2)
        
        # 启动
        return self.start_resolve(wait_for_startup=wait_for_startup)
    
    def ensure_resolve_running(self, auto_start: bool = True) -> bool:
        """
        确保 Resolve 正在运行
        
        Args:
            auto_start: 如果未运行，是否自动启动
        
        Returns:
            True 如果 Resolve 正在运行
        """
        if self.is_resolve_running():
            return True
        
        if auto_start:
            print("⚠️ DaVinci Resolve 未运行，尝试自动启动...")
            return self.start_resolve()
        
        return False
    
    def get_system_resources(self) -> Dict[str, Any]:
        """
        获取系统资源使用情况
        
        Returns:
            {
                "cpu_percent": 45.2,
                "memory_percent": 67.8,
                "memory_available_gb": 8.5,
                "disk_usage_percent": 72.3
            }
        """
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_percent": round(cpu_percent, 2),
            "memory_percent": round(memory.percent, 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": round(disk.percent, 2)
        }


# 单例模式
_process_manager_instance = None


def get_process_manager() -> ProcessManager:
    """获取 ProcessManager 单例"""
    global _process_manager_instance
    if _process_manager_instance is None:
        _process_manager_instance = ProcessManager()
    return _process_manager_instance


# 便捷函数
def ensure_resolve_running(auto_start: bool = True) -> bool:
    """
    便捷函数：确保 Resolve 正在运行
    
    Args:
        auto_start: 如果未运行，是否自动启动
    
    Returns:
        True 如果 Resolve 正在运行
    """
    manager = get_process_manager()
    return manager.ensure_resolve_running(auto_start)


def get_resolve_status() -> Dict[str, Any]:
    """
    便捷函数：获取 Resolve 状态
    
    Returns:
        状态字典
    """
    manager = get_process_manager()
    return manager.get_resolve_status()


# 独立测试入口
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("OS 进程管理器测试")
    print("=" * 70)
    
    manager = ProcessManager()
    
    # 1. 检查状态
    print("\n[1/4] 检查 Resolve 状态...")
    status = manager.get_resolve_status()
    
    if status["running"]:
        print(f"  ✓ Resolve 正在运行")
        print(f"    PID: {status['pid']}")
        print(f"    内存: {status['memory_mb']} MB")
        print(f"    CPU: {status['cpu_percent']}%")
        print(f"    运行时间: {status['uptime_seconds']} 秒")
    else:
        print(f"  ✗ Resolve 未运行")
    
    # 2. 系统资源
    print("\n[2/4] 系统资源...")
    resources = manager.get_system_resources()
    print(f"  CPU: {resources['cpu_percent']}%")
    print(f"  内存: {resources['memory_percent']}% (可用: {resources['memory_available_gb']} GB)")
    print(f"  磁盘: {resources['disk_usage_percent']}%")
    
    # 3. 自动启动测试（可选）
    print("\n[3/4] 自动启动测试...")
    print("  是否测试自动启动？(y/n): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            if manager.ensure_resolve_running(auto_start=True):
                print("  ✓ Resolve 已确保运行")
            else:
                print("  ✗ 启动失败")
    except:
        print("  跳过")
    
    # 4. 最终状态
    print("\n[4/4] 最终状态...")
    final_status = manager.get_resolve_status()
    print(f"  运行状态: {'✓ 运行中' if final_status['running'] else '✗ 未运行'}")
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
