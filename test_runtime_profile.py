"""
测试 Runtime Profile 系统

测试内容：
1. RuntimeProfile 自动检测
2. ExecutionPolicy 生成
3. RuntimeMonitor 监控
4. 自动降级机制
5. 完整集成测试
"""
import sys
import time
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.core.runtime_profile import (
    RuntimeProfile,
    get_runtime_profile,
    save_runtime_profile
)
from app.core.execution_policy import (
    ExecutionPolicyResolver,
    get_execution_policy,
    degrade_execution_policy
)
from app.core.runtime_monitor import (
    RuntimeMonitor,
    get_runtime_monitor,
    start_runtime_monitor,
    stop_runtime_monitor
)


def test_runtime_profile_detection():
    """测试 1: RuntimeProfile 自动检测"""
    print("\n" + "="*60)
    print("测试 1: RuntimeProfile 自动检测")
    print("="*60)
    
    profile = RuntimeProfile.detect()
    
    print(f"\n✓ CPU: {profile.cpu.threads} 线程 ({profile.cpu.score})")
    print(f"✓ 内存: {profile.memory.total_gb}GB (可用 {profile.memory.available_gb}GB)")
    
    if profile.gpu:
        print(f"✓ GPU: {profile.gpu.vendor} {profile.gpu.model} ({profile.gpu.vram_gb}GB)")
    else:
        print("✓ GPU: 未检测到")
    
    print(f"✓ Ollama: {'已安装' if profile.ai_runtime.ollama else '未安装'}")
    if profile.ai_runtime.ollama_models:
        print(f"  模型: {', '.join(profile.ai_runtime.ollama_models)}")
    
    print(f"✓ DaVinci Resolve: {'已安装' if profile.editor.davinci['installed'] else '未安装'}")
    
    print(f"\n✓ Profile Class: {profile.profile_class}")
    
    # 保存到文件
    profile_path = Path(__file__).parent / "runtime_profile.json"
    save_runtime_profile(profile_path)
    print(f"✓ 已保存到: {profile_path}")
    
    return profile


def test_execution_policy_generation(profile: RuntimeProfile):
    """测试 2: ExecutionPolicy 生成"""
    print("\n" + "="*60)
    print("测试 2: ExecutionPolicy 生成")
    print("="*60)
    
    policy = ExecutionPolicyResolver.resolve(profile)
    
    print(f"\n✓ Vision:")
    print(f"  Provider: {policy.vision.provider}")
    print(f"  Model: {policy.vision.model}")
    print(f"  Device: {policy.vision.device}")
    print(f"  Max Scenes: {policy.vision.max_scenes}")
    
    print(f"\n✓ Planning:")
    print(f"  Provider: {policy.planning.provider}")
    print(f"  Model: {policy.planning.model}")
    
    print(f"\n✓ Editing:")
    print(f"  Executor: {policy.editing.executor}")
    print(f"  Parallelism: {policy.editing.parallelism}")
    print(f"  Preview Quality: {policy.editing.preview_quality}")
    
    print(f"\n✓ Explanation: {policy.explanation}")
    
    return policy


def test_policy_degradation(policy):
    """测试 3: 策略降级"""
    print("\n" + "="*60)
    print("测试 3: 策略降级")
    print("="*60)
    
    print(f"\n原始策略:")
    print(f"  Vision: {policy.vision.provider} / {policy.vision.model}")
    print(f"  Max Scenes: {policy.vision.max_scenes}")
    
    # 模拟降级
    degraded_policy = ExecutionPolicyResolver.degrade_policy(
        policy,
        "GPU 显存使用率过高 (87%)"
    )
    
    print(f"\n降级后策略:")
    print(f"  Vision: {degraded_policy.vision.provider} / {degraded_policy.vision.model}")
    print(f"  Max Scenes: {degraded_policy.vision.max_scenes}")
    print(f"  Explanation: {degraded_policy.explanation}")
    
    return degraded_policy


def test_runtime_monitor():
    """测试 4: RuntimeMonitor 监控"""
    print("\n" + "="*60)
    print("测试 4: RuntimeMonitor 监控")
    print("="*60)
    
    monitor = RuntimeMonitor(check_interval=2)
    
    # 注册降级回调
    degradation_triggered = []
    
    def on_degradation(reason: str):
        print(f"\n⚠️  降级回调触发: {reason}")
        degradation_triggered.append(reason)
    
    monitor.register_degradation_callback(on_degradation)
    
    # 启动监控
    monitor.start()
    
    print("\n✓ 监控已启动，收集 10 秒数据...")
    
    # 模拟任务
    for i in range(5):
        time.sleep(2)
        
        # 记录任务结果
        success = (i % 3 != 0)  # 每 3 个失败一次
        monitor.record_task_result(success)
        
        # 获取当前指标
        metrics = monitor.get_current_metrics()
        if metrics:
            print(f"\n[{i+1}/5] 当前指标:")
            print(f"  GPU 显存: {metrics.gpu_vram_used_percent:.1f}%")
            print(f"  内存: {metrics.memory_used_percent:.1f}%")
            print(f"  CPU: {metrics.cpu_percent:.1f}%")
            print(f"  任务失败率: {metrics.task_failure_rate*100:.1f}%")
            
            # 检查是否应该使用 CPU 模式
            if monitor.should_use_cpu_for_vision():
                print(f"  ⚠️  建议使用 CPU 模式")
    
    # 获取状态
    status = monitor.get_status()
    print(f"\n✓ 监控状态:")
    print(f"  运行中: {status['running']}")
    print(f"  已降级: {status['degraded']}")
    print(f"  任务总数: {status['task_stats']['total']}")
    print(f"  成功率: {status['task_stats']['success_rate']}%")
    
    # 停止监控
    monitor.stop()
    
    return monitor


def test_user_explanation():
    """测试 5: 用户友好的解释"""
    print("\n" + "="*60)
    print("测试 5: 用户友好的解释")
    print("="*60)
    
    profile = get_runtime_profile()
    explanation = profile.get_explanation()
    
    print(f"\n{explanation}")
    
    return explanation


def test_integration():
    """测试 6: 完整集成测试"""
    print("\n" + "="*60)
    print("测试 6: 完整集成测试")
    print("="*60)
    
    # 1. 获取 Profile
    profile = get_runtime_profile()
    print(f"\n✓ Profile Class: {profile.profile_class}")
    
    # 2. 获取 Policy
    policy = get_execution_policy()
    print(f"✓ Vision: {policy.vision.provider} / {policy.vision.model}")
    
    # 3. 启动 Monitor
    start_runtime_monitor()
    monitor = get_runtime_monitor()
    
    # 4. 模拟工作流
    print(f"\n✓ 模拟工作流...")
    
    # 检查是否应该使用 CPU 模式
    time.sleep(1)
    if monitor.should_use_cpu_for_vision():
        print(f"  → 使用 CPU 模式进行视觉分析")
    else:
        print(f"  → 使用 GPU 模式进行视觉分析")
    
    # 5. 模拟降级
    print(f"\n✓ 模拟降级...")
    degraded_policy = degrade_execution_policy("测试降级")
    print(f"  → 降级后 Vision: {degraded_policy.vision.provider}")
    
    # 6. 检查 Profile 是否标记为降级
    profile = get_runtime_profile()
    print(f"  → Profile 降级状态: {profile.degraded}")
    print(f"  → 降级原因: {profile.degradation_reason}")
    
    # 7. 停止 Monitor
    stop_runtime_monitor()
    
    print(f"\n✅ 集成测试完成")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Runtime Profile 系统测试")
    print("="*60)
    
    try:
        # 测试 1: Profile 检测
        profile = test_runtime_profile_detection()
        
        # 测试 2: Policy 生成
        policy = test_execution_policy_generation(profile)
        
        # 测试 3: 策略降级
        test_policy_degradation(policy)
        
        # 测试 4: 运行时监控
        test_runtime_monitor()
        
        # 测试 5: 用户解释
        test_user_explanation()
        
        # 测试 6: 完整集成
        test_integration()
        
        print("\n" + "="*60)
        print("✅ 所有测试通过")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
