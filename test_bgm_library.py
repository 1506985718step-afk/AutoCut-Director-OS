"""
测试 BGM 素材库管理器
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.tools.bgm_library import BGMLibrary, create_bgm_library, search_bgm


def test_create_sample_library():
    """测试创建示例 BGM 库"""
    print("\n" + "=" * 70)
    print("🎵 测试 1: 创建示例 BGM 库")
    print("=" * 70)
    
    library = BGMLibrary("bgm_library")
    library.create_sample_library()
    
    print("\n✅ 示例库创建完成")


def test_scan_library():
    """测试扫描 BGM 库"""
    print("\n" + "=" * 70)
    print("🎵 测试 2: 扫描 BGM 库")
    print("=" * 70)
    
    library = BGMLibrary("bgm_library")
    bgm_list = library.scan_library()
    
    print(f"\n找到 {len(bgm_list)} 首 BGM:")
    for bgm in bgm_list:
        print(f"  - {bgm.id}: {bgm.mood} | {bgm.bpm} BPM | {bgm.energy} energy")
    
    print("\n✅ 扫描完成")


def test_search_bgm():
    """测试搜索 BGM"""
    print("\n" + "=" * 70)
    print("🎵 测试 3: 搜索 BGM")
    print("=" * 70)
    
    library = create_bgm_library("bgm_library")
    
    # 测试 1: 按 mood 搜索
    print("\n搜索 mood='calm':")
    results = library.search(mood="calm")
    for bgm in results:
        print(f"  - {bgm.id}: {bgm.bpm} BPM")
    
    # 测试 2: 按 energy 搜索
    print("\n搜索 energy='medium':")
    results = library.search(energy="medium")
    for bgm in results:
        print(f"  - {bgm.id}: {bgm.mood} | {bgm.bpm} BPM")
    
    # 测试 3: 按 BPM 范围搜索
    print("\n搜索 BPM 100-120:")
    results = library.search(bpm_range=(100, 120))
    for bgm in results:
        print(f"  - {bgm.id}: {bgm.bpm} BPM | {bgm.mood}")
    
    # 测试 4: 按 usage 搜索
    print("\n搜索 usage='teaching':")
    results = library.search(usage="teaching")
    for bgm in results:
        print(f"  - {bgm.id}: {bgm.mood} | {bgm.usage}")
    
    # 测试 5: 组合搜索
    print("\n搜索 mood='emotional' AND energy='medium':")
    results = library.search(mood="emotional", energy="medium")
    for bgm in results:
        print(f"  - {bgm.id}: {bgm.bpm} BPM")
    
    print("\n✅ 搜索测试完成")


def test_export_for_llm():
    """测试导出为 LLM 格式"""
    print("\n" + "=" * 70)
    print("🎵 测试 4: 导出为 LLM 格式")
    print("=" * 70)
    
    library = create_bgm_library("bgm_library")
    llm_data = library.export_for_llm()
    
    print(f"\n导出 {len(llm_data)} 首 BGM 供 LLM 使用:")
    
    import json
    print(json.dumps(llm_data, indent=2, ensure_ascii=False))
    
    print("\n✅ 导出完成")


def test_get_by_id():
    """测试根据 ID 获取 BGM"""
    print("\n" + "=" * 70)
    print("🎵 测试 5: 根据 ID 获取 BGM")
    print("=" * 70)
    
    library = create_bgm_library("bgm_library")
    
    # 获取第一个 BGM 的 ID
    all_bgm = library.get_all()
    if all_bgm:
        test_id = all_bgm[0].id
        print(f"\n测试 ID: {test_id}")
        
        bgm = library.get_by_id(test_id)
        if bgm:
            print(f"✓ 找到 BGM:")
            print(f"  ID: {bgm.id}")
            print(f"  Path: {bgm.path}")
            print(f"  Mood: {bgm.mood}")
            print(f"  BPM: {bgm.bpm}")
            print(f"  Energy: {bgm.energy}")
            print(f"  Usage: {bgm.usage}")
            print(f"  Copyright: {bgm.copyright}")
        else:
            print(f"❌ 未找到 BGM: {test_id}")
    else:
        print("⚠️  BGM 库为空")
    
    print("\n✅ 测试完成")


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "=" * 70)
    print("🎵 测试 6: 便捷搜索函数")
    print("=" * 70)
    
    # 使用便捷函数搜索
    results = search_bgm(mood="calm", energy="low")
    
    print(f"\n搜索 mood='calm' AND energy='low':")
    print(f"找到 {len(results)} 首 BGM:")
    for bgm in results:
        print(f"  - {bgm.id}: {bgm.bpm} BPM")
    
    print("\n✅ 便捷函数测试完成")


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - BGM 素材库测试")
    print("=" * 70)
    
    # 运行所有测试
    test_create_sample_library()
    test_scan_library()
    test_search_bgm()
    test_export_for_llm()
    test_get_by_id()
    test_convenience_function()
    
    print("\n" + "=" * 70)
    print("✅ 所有测试完成")
    print("=" * 70)
    
    print("\n📝 下一步:")
    print("  1. 将实际音频文件放入 bgm_library/ 目录")
    print("  2. 运行 python test_bgm_library.py 重新扫描")
    print("  3. 在 LLM 提示词中使用 BGM 库")
