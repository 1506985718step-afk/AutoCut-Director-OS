"""测试字幕渲染功能"""
import json
from pathlib import Path
from app.executor.actions import (
    create_timeline, 
    append_scene, 
    add_text_overlay,
    render_subtitles,
    export_mp4
)
from app.executor.runner import run_actions


def test_text_overlay():
    """测试文字叠加功能"""
    print("=" * 60)
    print("测试文字叠加功能")
    print("=" * 60)
    
    print("\n注意：此测试需要 DaVinci Resolve 运行")
    print("按 Enter 继续，或 Ctrl+C 取消...")
    input()
    
    # 创建测试动作序列
    actions = [
        # 1. 创建时间线
        create_timeline(
            name="Test_TextOverlay",
            fps=30,
            resolution={"width": 1080, "height": 1920}
        ),
        
        # 2. 添加主视频片段（假设已有素材）
        append_scene(
            scene_id="S0001",
            in_frame=0,
            out_frame=150,  # 5 秒
            source="D:/Footage/test.mp4"  # 请替换为实际路径
        ),
        
        # 3. 添加文字叠加（抖音风格）
        add_text_overlay(
            text="第一步就错了",
            start_frame=30,  # 1 秒后出现
            duration_frames=60,  # 持续 2 秒
            style={
                "font_size": 72,
                "font_color": [1.0, 1.0, 0.0],  # 黄色
                "position": [0.5, 0.3],  # 屏幕中上部
                "stroke_width": 3,
                "stroke_color": [0.0, 0.0, 0.0]  # 黑色描边
            }
        ),
        
        # 4. 再添加一个文字
        add_text_overlay(
            text="90%的人都不知道",
            start_frame=90,  # 3 秒后出现
            duration_frames=60,
            style={
                "font_size": 80,
                "font_color": [1.0, 0.0, 0.0],  # 红色
                "position": [0.5, 0.5],
                "stroke_width": 4,
                "stroke_color": [1.0, 1.0, 1.0]  # 白色描边
            }
        )
    ]
    
    # 执行动作
    print("\n执行动作序列...")
    try:
        trace = run_actions(actions, trace_path="test_text_overlay_trace.json")
        
        print("\n执行结果：")
        for t in trace:
            status = "✓" if t["ok"] else "✗"
            print(f"{status} {t['action']}: {t['detail']} ({t['took_ms']}ms)")
        
        print("\n✓ 测试完成！请在 Resolve 中查看效果")
        
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        return False
    
    return True


def test_subtitle_rendering():
    """测试字幕渲染功能"""
    print("\n" + "=" * 60)
    print("测试字幕渲染功能")
    print("=" * 60)
    
    print("\n注意：此测试需要 DaVinci Resolve 运行")
    print("按 Enter 继续，或 Ctrl+C 取消...")
    input()
    
    # 加载 transcript
    transcript_path = Path("examples/transcript.v1.json")
    transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
    
    # 创建测试动作序列
    actions = [
        # 1. 创建时间线
        create_timeline(
            name="Test_Subtitles",
            fps=30,
            resolution={"width": 1080, "height": 1920}
        ),
        
        # 2. 添加主视频片段
        append_scene(
            scene_id="S0001",
            in_frame=0,
            out_frame=300,  # 10 秒
            source="D:/Footage/test.mp4"  # 请替换为实际路径
        ),
        
        # 3. 渲染字幕（抖音风格）
        render_subtitles(
            transcript_segments=transcript_data["segments"],
            fps=30,
            style="bold_yellow"
        )
    ]
    
    # 执行动作
    print("\n执行动作序列...")
    try:
        trace = run_actions(actions, trace_path="test_subtitles_trace.json")
        
        print("\n执行结果：")
        for t in trace:
            status = "✓" if t["ok"] else "✗"
            print(f"{status} {t['action']}: {t['detail']} ({t['took_ms']}ms)")
        
        print("\n✓ 测试完成！请在 Resolve 中查看字幕效果")
        
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        return False
    
    return True


def test_style_presets():
    """测试不同字幕样式预设"""
    print("\n" + "=" * 60)
    print("测试字幕样式预设")
    print("=" * 60)
    
    styles = ["bold_yellow", "clean_white", "elegant_black"]
    
    print("\n可用样式：")
    print("1. bold_yellow - 抖音风格（粗体黄字黑边）")
    print("2. clean_white - 简洁白字")
    print("3. elegant_black - 优雅黑字")
    
    print("\n样式预设说明：")
    print("- bold_yellow: 适合短视频平台（抖音、快手）")
    print("- clean_white: 适合 B站、YouTube")
    print("- elegant_black: 适合纪录片、Vlog")
    
    return True


if __name__ == "__main__":
    print("字幕渲染功能测试套件")
    print("=" * 60)
    
    # 测试 1: 文字叠加
    try:
        test_text_overlay()
    except KeyboardInterrupt:
        print("\n测试取消")
    
    # 测试 2: 字幕渲染
    try:
        test_subtitle_rendering()
    except KeyboardInterrupt:
        print("\n测试取消")
    
    # 测试 3: 样式预设
    test_style_presets()
    
    print("\n" + "=" * 60)
    print("提示：")
    print("- 请确保 DaVinci Resolve 正在运行")
    print("- 请替换测试中的素材路径为实际文件")
    print("- 字幕渲染使用 Fusion Text+ 节点（更灵活）")
    print("- 如果 Fusion 不可用，会自动降级到 Title 生成器")
