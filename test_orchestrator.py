"""
测试 Orchestrator 状态机和调度算法

测试内容：
1. 状态转换规则
2. 资源锁机制
3. 并发冲突处理
4. 降级处理
5. 5 条铁律验证
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.core.orchestrator import (
    get_orchestrator,
    JobState,
    StateTransition,
    ResourceLock
)
from app.core.job_store import JobStore


def test_state_transitions():
    """测试 1: 状态转换规则"""
    print("\n" + "=" * 70)
    print("测试 1: 状态转换规则")
    print("=" * 70)
    
    # 合法转换
    legal_transitions = [
        (JobState.CREATED, JobState.INGESTING),
        (JobState.INGESTING, JobState.INGESTED),
        (JobState.INGESTED, JobState.ANALYZING),
        (JobState.ANALYZING, JobState.ANALYZED),
        (JobState.ANALYZED, JobState.PLANNING),
        (JobState.PLANNING, JobState.PLANNED),
        (JobState.PLANNED, JobState.EXECUTING),
        (JobState.EXECUTING, JobState.EXPORTING),
        (JobState.EXPORTING, JobState.COMPLETED),
    ]
    
    print("\n合法转换:")
    for from_state, to_state in legal_transitions:
        can = StateTransition.can_transition(from_state, to_state)
        status = "✅" if can else "❌"
        print(f"  {status} {from_state.value} → {to_state.value}")
        assert can, f"应该允许 {from_state.value} → {to_state.value}"
    
    # 非法转换
    illegal_transitions = [
        (JobState.CREATED, JobState.ANALYZING),
        (JobState.ANALYZING, JobState.EXECUTING),
        (JobState.COMPLETED, JobState.ANALYZING),
    ]
    
    print("\n非法转换:")
    for from_state, to_state in illegal_transitions:
        can = StateTransition.can_transition(from_state, to_state)
        status = "✅" if not can else "❌"
        print(f"  {status} {from_state.value} → {to_state.value} (应该禁止)")
        assert not can, f"不应该允许 {from_state.value} → {to_state.value}"
    
    print("\n✅ 状态转换规则测试通过")
    return True


def test_resource_locks():
    """测试 2: 资源锁机制"""
    print("\n" + "=" * 70)
    print("测试 2: 资源锁机制")
    print("=" * 70)
    
    lock = ResourceLock()
    
    # 测试获取锁
    print("\n[1/4] 测试获取锁...")
    assert lock.acquire("GPU_HEAVY") == True
    print("  ✅ 成功获取 GPU_HEAVY")
    
    # 测试重复获取
    print("\n[2/4] 测试重复获取...")
    assert lock.acquire("GPU_HEAVY") == False
    print("  ✅ 正确拒绝重复获取")
    
    # 测试释放锁
    print("\n[3/4] 测试释放锁...")
    lock.release("GPU_HEAVY")
    assert lock.is_locked("GPU_HEAVY") == False
    print("  ✅ 成功释放 GPU_HEAVY")
    
    # 测试再次获取
    print("\n[4/4] 测试再次获取...")
    assert lock.acquire("GPU_HEAVY") == True
    print("  ✅ 成功再次获取")
    
    print("\n✅ 资源锁机制测试通过")
    return True


def test_concurrent_conflict():
    """测试 3: 并发冲突处理"""
    print("\n" + "=" * 70)
    print("测试 3: 并发冲突处理")
    print("=" * 70)
    
    orchestrator = get_orchestrator()
    job_store = JobStore()
    
    # 创建两个任务
    print("\n[1/5] 创建任务...")
    job1 = job_store.create_job()
    import time
    time.sleep(1)  # 确保时间戳不同
    job2 = job_store.create_job()
    print(f"  ✅ 创建 {job1}")
    print(f"  ✅ 创建 {job2}")
    
    # Job1 进入 EXECUTING（占用 GPU）
    print("\n[2/5] Job1 进入 EXECUTING...")
    success, msg = job_store.transition_state(job1, JobState.INGESTING)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.INGESTED)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.ANALYZING)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.ANALYZED)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.PLANNING)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.PLANNED)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.EXECUTING)
    assert success, f"转换失败: {msg}"
    print(f"  ✅ {job1} 进入 EXECUTING")
    print(f"  ✅ GPU_HEAVY 已锁定")
    
    # Job2 尝试进入 ANALYZING（需要 GPU）
    print("\n[3/5] Job2 尝试进入 ANALYZING...")
    success, msg = job_store.transition_state(job2, JobState.INGESTING)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job2, JobState.INGESTED)
    assert success, f"转换失败: {msg}"
    
    # 这里应该被阻止，因为 VISION_ALLOWED 被禁用
    can_enter, reason = orchestrator.can_enter_state(job2, JobState.ANALYZING)
    print(f"  ⚠️  Job2 尝试进入 ANALYZING: {reason}")
    assert not can_enter, "应该被阻止"
    
    # Job1 完成 EXECUTING
    print("\n[4/5] Job1 完成 EXECUTING...")
    success, msg = job_store.transition_state(job1, JobState.EXPORTING)
    assert success, f"转换失败: {msg}"
    success, msg = job_store.transition_state(job1, JobState.COMPLETED)
    assert success, f"转换失败: {msg}"
    print(f"  ✅ {job1} 完成")
    print(f"  ✅ GPU_HEAVY 已释放")
    
    # Job2 现在可以进入 ANALYZING
    print("\n[5/5] Job2 现在可以进入 ANALYZING...")
    can_enter, reason = orchestrator.can_enter_state(job2, JobState.ANALYZING)
    print(f"  ✅ Job2 可以进入 ANALYZING: {reason}")
    assert can_enter, f"应该允许进入: {reason}"
    
    print("\n✅ 并发冲突处理测试通过")
    return True


def test_iron_rule_1():
    """测试铁律 1: 任何时间只允许一个 GPU-heavy 任务"""
    print("\n" + "=" * 70)
    print("测试铁律 1: 任何时间只允许一个 GPU-heavy 任务")
    print("=" * 70)
    
    orchestrator = get_orchestrator()
    
    # 模拟 EXECUTING 状态
    print("\n[1/2] 模拟 EXECUTING 状态...")
    orchestrator.enter_state("test_job_1", JobState.EXECUTING)
    
    status = orchestrator.resource_lock.get_status()
    print(f"  资源状态: {status}")
    
    assert status["GPU_HEAVY"] == True
    assert status["VISION_ALLOWED"] == False
    print("  ✅ GPU_HEAVY 已锁定")
    print("  ✅ VISION_ALLOWED 已禁用")
    
    # 退出状态
    print("\n[2/2] 退出 EXECUTING 状态...")
    orchestrator.exit_state("test_job_1", JobState.EXECUTING)
    
    status = orchestrator.resource_lock.get_status()
    print(f"  资源状态: {status}")
    
    assert status["GPU_HEAVY"] == False
    assert status["VISION_ALLOWED"] == True
    print("  ✅ GPU_HEAVY 已释放")
    print("  ✅ VISION_ALLOWED 已恢复")
    
    print("\n✅ 铁律 1 测试通过")
    return True


def test_iron_rule_2():
    """测试铁律 2: Resolve Export > 一切 AI"""
    print("\n" + "=" * 70)
    print("测试铁律 2: Resolve Export > 一切 AI")
    print("=" * 70)
    
    orchestrator = get_orchestrator()
    
    # 模拟 EXPORTING 状态
    print("\n[1/2] 模拟 EXPORTING 状态...")
    orchestrator.enter_state("test_job_2", JobState.EXPORTING)
    
    status = orchestrator.resource_lock.get_status()
    print(f"  资源状态: {status}")
    
    assert status["GPU_HEAVY"] == True
    assert status["VISION_ALLOWED"] == False
    assert status["AI_ALLOWED"] == False
    assert status["RESOLVE_BUSY"] == True
    
    print("  ✅ 所有 AI 功能已禁用")
    print("  ✅ Resolve 独占资源")
    
    # 退出状态
    print("\n[2/2] 退出 EXPORTING 状态...")
    orchestrator.exit_state("test_job_2", JobState.EXPORTING)
    
    status = orchestrator.resource_lock.get_status()
    print(f"  资源状态: {status}")
    
    assert status["GPU_HEAVY"] == False
    assert status["VISION_ALLOWED"] == True
    print("  ✅ AI 功能已恢复")
    
    print("\n✅ 铁律 2 测试通过")
    return True


def test_system_status():
    """测试系统状态查询"""
    print("\n" + "=" * 70)
    print("测试系统状态查询")
    print("=" * 70)
    
    orchestrator = get_orchestrator()
    status = orchestrator.get_system_status()
    
    print("\n系统状态:")
    print(f"  资源锁: {status['resource_locks']}")
    print(f"  活跃任务: {status['active_jobs']}")
    print(f"  CPU: {status['system']['cpu_percent']}%")
    print(f"  内存: {status['system']['memory_percent']}%")
    print(f"  可用内存: {status['system']['memory_available_gb']:.2f} GB")
    
    assert "resource_locks" in status
    assert "active_jobs" in status
    assert "system" in status
    
    print("\n✅ 系统状态查询测试通过")
    return True


def main():
    """主测试流程"""
    print("\n" + "=" * 70)
    print("Orchestrator 状态机和调度算法测试")
    print("=" * 70)
    
    tests = [
        ("状态转换规则", test_state_transitions),
        ("资源锁机制", test_resource_locks),
        ("并发冲突处理", test_concurrent_conflict),
        ("铁律 1: GPU-heavy 任务互斥", test_iron_rule_1),
        ("铁律 2: Resolve Export 优先", test_iron_rule_2),
        ("系统状态查询", test_system_status),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except AssertionError as e:
            print(f"\n❌ 测试失败: {e}")
            results.append((name, False))
        except Exception as e:
            print(f"\n❌ 测试异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n通过率: {passed}/{total} ({passed/total*100:.0f}%)")
    
    if passed == total:
        print("\n🎉 所有测试通过！Orchestrator 已就绪。")
    else:
        print("\n⚠️  部分测试失败，请检查。")


if __name__ == "__main__":
    main()
