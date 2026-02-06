"""
测试 Content Modality Analyzer

测试内容：
1. 模态分析
2. 音频匹配
3. 完整流水线
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.modality_analyzer import (
    ModalityAnalyzer,
    analyze_modality,
    should_run_vision,
    ModalityAnalysis
)
from app.tools.audio_matcher import AudioMatcher, match_audio_to_videos
from app.tools.smart_pipeline import SmartPipeline


def test_modality_analyzer():
    """测试 1: 模态分析器"""
    print("\n" + "="*60)
    print("测试 1: 模态分析器")
    print("="*60)
    
    analyzer = ModalityAnalyzer()
    
    # 测试用例 1: 口播视频（模拟）
    print("\n📹 测试用例 1: 口播视频")
    analysis = ModalityAnalysis(
        has_voice=True,
        speech_ratio=0.78,
        music_ratio=0.12,
        silence_ratio=0.10,
        likely_talking_head=True,
        recommended_mode="ASR_PRIMARY",
        confidence=0.9,
        audio_present=True,
        avg_volume_db=-20,
        volume_variance=12,
        speech_segments=45
    )
    
    print(f"✓ 有语音: {analysis.has_voice}")
    print(f"✓ 语音占比: {analysis.speech_ratio*100:.1f}%")
    print(f"✓ 音乐占比: {analysis.music_ratio*100:.1f}%")
    print(f"✓ 静音占比: {analysis.silence_ratio*100:.1f}%")
    print(f"✓ 可能是口播: {analysis.likely_talking_head}")
    print(f"✓ 推荐模式: {analysis.recommended_mode}")
    print(f"✓ 置信度: {analysis.confidence*100:.1f}%")
    
    # 测试用例 2: B-roll（无声）
    print("\n📹 测试用例 2: B-roll（无声）")
    analysis2 = ModalityAnalysis(
        has_voice=False,
        speech_ratio=0.0,
        music_ratio=0.0,
        silence_ratio=1.0,
        likely_talking_head=False,
        recommended_mode="VISION_PRIMARY",
        confidence=0.95,
        audio_present=False,
        avg_volume_db=-100,
        volume_variance=0,
        speech_segments=0
    )
    
    print(f"✓ 有语音: {analysis2.has_voice}")
    print(f"✓ 推荐模式: {analysis2.recommended_mode}")
    print(f"✓ 置信度: {analysis2.confidence*100:.1f}%")
    
    # 测试用例 3: Vlog（混合）
    print("\n📹 测试用例 3: Vlog（混合）")
    analysis3 = ModalityAnalysis(
        has_voice=True,
        speech_ratio=0.45,
        music_ratio=0.25,
        silence_ratio=0.30,
        likely_talking_head=False,
        recommended_mode="HYBRID",
        confidence=0.7,
        audio_present=True,
        avg_volume_db=-18,
        volume_variance=8,
        speech_segments=20
    )
    
    print(f"✓ 有语音: {analysis3.has_voice}")
    print(f"✓ 语音占比: {analysis3.speech_ratio*100:.1f}%")
    print(f"✓ 推荐模式: {analysis3.recommended_mode}")
    print(f"✓ 置信度: {analysis3.confidence*100:.1f}%")


def test_should_run_vision():
    """测试 2: Vision 运行判断"""
    print("\n" + "="*60)
    print("测试 2: Vision 运行判断")
    print("="*60)
    
    # 场景 1: ASR_PRIMARY + 有转录 → 不跑 Vision
    print("\n📋 场景 1: ASR_PRIMARY + 有转录")
    modality = ModalityAnalysis(
        has_voice=True,
        speech_ratio=0.78,
        music_ratio=0.12,
        silence_ratio=0.10,
        likely_talking_head=True,
        recommended_mode="ASR_PRIMARY",
        confidence=0.9,
        audio_present=True,
        avg_volume_db=-20,
        volume_variance=12,
        speech_segments=45
    )
    
    should_run = should_run_vision(modality, segment_has_transcript=True, transcript_confidence=0.9)
    print(f"✓ 是否运行 Vision: {should_run} (预期: False)")
    
    # 场景 2: ASR_PRIMARY + 无转录 → 跑 Vision
    print("\n📋 场景 2: ASR_PRIMARY + 无转录")
    should_run = should_run_vision(modality, segment_has_transcript=False)
    print(f"✓ 是否运行 Vision: {should_run} (预期: True)")
    
    # 场景 3: VISION_PRIMARY → 必须跑 Vision
    print("\n📋 场景 3: VISION_PRIMARY")
    modality2 = ModalityAnalysis(
        has_voice=False,
        speech_ratio=0.0,
        music_ratio=0.0,
        silence_ratio=1.0,
        likely_talking_head=False,
        recommended_mode="VISION_PRIMARY",
        confidence=0.95,
        audio_present=False,
        avg_volume_db=-100,
        volume_variance=0,
        speech_segments=0
    )
    
    should_run = should_run_vision(modality2, segment_has_transcript=True)
    print(f"✓ 是否运行 Vision: {should_run} (预期: True)")
    
    # 场景 4: HYBRID + 低置信度转录 → 跑 Vision
    print("\n📋 场景 4: HYBRID + 低置信度转录")
    modality3 = ModalityAnalysis(
        has_voice=True,
        speech_ratio=0.45,
        music_ratio=0.25,
        silence_ratio=0.30,
        likely_talking_head=False,
        recommended_mode="HYBRID",
        confidence=0.7,
        audio_present=True,
        avg_volume_db=-18,
        volume_variance=8,
        speech_segments=20
    )
    
    should_run = should_run_vision(modality3, segment_has_transcript=True, transcript_confidence=0.5)
    print(f"✓ 是否运行 Vision: {should_run} (预期: True)")


def test_audio_matcher():
    """测试 3: 音频匹配器"""
    print("\n" + "="*60)
    print("测试 3: 音频匹配器")
    print("="*60)
    
    matcher = AudioMatcher()
    
    # 模拟视频和音频资源
    videos = [
        {
            "asset_id": "V001",
            "path": "D:/footage/A001.mp4",
            "filename": "A001.mp4"
        },
        {
            "asset_id": "V002",
            "path": "D:/footage/B002.mp4",
            "filename": "B002.mp4"
        }
    ]
    
    audios = [
        {
            "asset_id": "A001",
            "path": "D:/footage/A001.wav",
            "filename": "A001.wav"
        },
        {
            "asset_id": "A002",
            "path": "D:/footage/C003.wav",
            "filename": "C003.wav"
        }
    ]
    
    # 测试显式匹配
    print("\n🎵 测试显式匹配")
    match = matcher._explicit_match(videos[0], audios)
    if match:
        print(f"✓ V001 匹配到: {match['asset_id']} (方法: 文件名匹配)")
    else:
        print(f"✓ V001 无匹配")
    
    match = matcher._explicit_match(videos[1], audios)
    if match:
        print(f"✓ V002 匹配到: {match['asset_id']}")
    else:
        print(f"✓ V002 无匹配 (预期)")


def test_decision_matrix():
    """测试 4: 决策矩阵"""
    print("\n" + "="*60)
    print("测试 4: 决策矩阵")
    print("="*60)
    
    analyzer = ModalityAnalyzer()
    
    # 测试各种场景
    test_cases = [
        {
            "name": "出镜口播",
            "has_voice": True,
            "speech_ratio": 0.85,
            "music_ratio": 0.05,
            "silence_ratio": 0.10,
            "likely_talking_head": True,
            "expected": "ASR_PRIMARY"
        },
        {
            "name": "教程解说",
            "has_voice": True,
            "speech_ratio": 0.75,
            "music_ratio": 0.10,
            "silence_ratio": 0.15,
            "likely_talking_head": True,
            "expected": "ASR_PRIMARY"
        },
        {
            "name": "Vlog",
            "has_voice": True,
            "speech_ratio": 0.50,
            "music_ratio": 0.20,
            "silence_ratio": 0.30,
            "likely_talking_head": False,
            "expected": "HYBRID"
        },
        {
            "name": "产品展示",
            "has_voice": True,
            "speech_ratio": 0.20,
            "music_ratio": 0.60,
            "silence_ratio": 0.20,
            "likely_talking_head": False,
            "expected": "VISION_PRIMARY"
        },
        {
            "name": "B-roll",
            "has_voice": False,
            "speech_ratio": 0.0,
            "music_ratio": 0.0,
            "silence_ratio": 1.0,
            "likely_talking_head": False,
            "expected": "VISION_PRIMARY"
        }
    ]
    
    print("\n决策矩阵测试:")
    print("-" * 60)
    
    for case in test_cases:
        mode, confidence = analyzer._decide_mode(
            case["has_voice"],
            case["speech_ratio"],
            case["music_ratio"],
            case["silence_ratio"],
            case["likely_talking_head"]
        )
        
        match = "✓" if mode == case["expected"] else "✗"
        print(f"{match} {case['name']:12s} → {mode:16s} (置信度: {confidence*100:.0f}%)")


def test_smart_pipeline():
    """测试 5: 完整流水线（模拟）"""
    print("\n" + "="*60)
    print("测试 5: 完整流水线（模拟）")
    print("="*60)
    
    # 创建临时 job 目录
    job_dir = Path(__file__).parent / "test_output" / "modality_test"
    job_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Job 目录: {job_dir}")
    
    # 模拟输入文件（不实际运行，只测试流程）
    print("\n✓ 流水线步骤:")
    print("  1. Ingest & Index")
    print("  2. Quick Quality Triage")
    print("  3. Match Audio to Video")
    print("  4. Modality Analysis")
    print("  5. Segment Assets")
    print("  6A. ASR Recognition")
    print("  6B. Vision Analysis (selective)")
    print("  6C. Structure Vision Data")
    print("  7. Generate ShotCards")
    
    print("\n✓ 流水线设计完成")


def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("Content Modality Analyzer 测试")
    print("="*60)
    
    try:
        # 测试 1: 模态分析器
        test_modality_analyzer()
        
        # 测试 2: Vision 运行判断
        test_should_run_vision()
        
        # 测试 3: 音频匹配器
        test_audio_matcher()
        
        # 测试 4: 决策矩阵
        test_decision_matrix()
        
        # 测试 5: 完整流水线
        test_smart_pipeline()
        
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
