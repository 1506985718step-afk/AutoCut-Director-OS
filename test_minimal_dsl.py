"""
测试最小 DSL 执行

最小 DSL 包含：
- 3 段视频片段
- 字幕（from_transcript）
- 背景音乐（可选）
- 不包含 fancy overlay 动画
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.executor.actions import (
    create_timeline,
    append_scene,
    render_subtitles,
    add_music,
    export_mp4
)
from app.executor.runner import run_actions
from app.models.schemas import DSLValidator


def test_minimal_dsl():
    """测试最小 DSL 执行"""
    
    print("\n" + "=" * 70)
    print("🎬 最小 DSL 执行测试")
    print("=" * 70)
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 加载 DSL 和 scenes
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n1️⃣  加载 DSL 和 scenes...")
    
    dsl_path = Path("examples/minimal_dsl.v1.json")
    scenes_path = Path("examples/scenes.v1.json")
    
    if not dsl_path.exists():
        print(f"❌ DSL 文件不存在: {dsl_path}")
        return False
    
    if not scenes_path.exists():
        print(f"❌ scenes 文件不存在: {scenes_path}")
        return False
    
    with open(dsl_path, 'r', encoding='utf-8') as f:
        dsl = json.load(f)
    
    with open(scenes_path, 'r', encoding='utf-8') as f:
        scenes_data = json.load(f)
    
    print(f"✅ DSL 加载成功")
    print(f"   Timeline: {len(dsl['editing_plan']['timeline'])} 段")
    print(f"   Subtitles: {dsl['editing_plan']['subtitles']['mode']}")
    print(f"   Music: {dsl['editing_plan']['music']['track_path'] or '无'}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 验证 DSL
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n2️⃣  验证 DSL...")
    
    errors = DSLValidator.validate_dsl_against_scenes(
        dsl, 
        scenes_data,
        broll_library=None
    )
    
    if errors:
        print("❌ DSL 验证失败:")
        for err in errors:
            print(f"   - {err}")
        return False
    
    print("✅ DSL 验证通过")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 转换为 Actions
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n3️⃣  转换为 Actions...")
    
    actions = []
    
    # 获取配置
    fps = scenes_data['meta']['fps']
    primary_clip = scenes_data['media']['primary_clip_path']
    resolution_str = dsl['export']['resolution']
    width, height = map(int, resolution_str.split('x'))
    
    # 1. 创建时间线
    actions.append(create_timeline(
        name="MinimalDSL_Test",
        fps=fps,
        resolution={"width": width, "height": height}
    ))
    
    # 2. 添加视频片段（3 段）
    for item in dsl['editing_plan']['timeline']:
        scene_id = item['scene_id']
        trim_frames = item['trim_frames']
        
        actions.append(append_scene(
            scene_id=scene_id,
            in_frame=trim_frames[0],
            out_frame=trim_frames[1],
            source=primary_clip
        ))
    
    # 3. 渲染字幕（如果有 transcript）
    transcript_path = Path("examples/transcript.v1.json")
    if transcript_path.exists() and dsl['editing_plan']['subtitles']['mode'] == 'from_transcript':
        with open(transcript_path, 'r', encoding='utf-8') as f:
            transcript_data = json.load(f)
        
        actions.append(render_subtitles(
            transcript_segments=transcript_data['segments'],
            fps=fps,
            style=dsl['editing_plan']['subtitles'].get('style', 'clean_white')
        ))
    
    # 4. 添加背景音乐（如果有）
    music_path = dsl['editing_plan']['music'].get('track_path')
    if music_path:
        actions.append(add_music(
            path=music_path,
            volume_db=dsl['editing_plan']['music'].get('volume_db', -18)
        ))
    
    # 5. 导出
    actions.append(export_mp4(
        path="test_output/minimal_dsl_output.mp4",
        resolution=resolution_str
    ))
    
    print(f"✅ 生成 {len(actions)} 个 Actions")
    for i, action in enumerate(actions, 1):
        print(f"   {i}. {action['type']}")
    
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 执行 Actions
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    print("\n4️⃣  执行 Actions...")
    print("\n⚠️  注意: 需要 DaVinci Resolve 正在运行")
    
    confirm = input("\n是否继续执行？(y/n): ").strip().lower()
    
    if confirm != 'y':
        print("已取消")
        return False
    
    try:
        trace = run_actions(actions, trace_path="test_output/minimal_dsl_trace.json")
        
        print("\n📊 执行结果:")
        for t in trace:
            status = "✅" if t['ok'] else "❌"
            print(f"   {status} {t['action']}: {t['detail']} ({t['took_ms']}ms)")
        
        # 检查是否全部成功
        all_ok = all(t['ok'] for t in trace)
        
        if all_ok:
            print("\n✅ 所有 Actions 执行成功")
            return True
        else:
            print("\n❌ 部分 Actions 执行失败")
            return False
            
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - 最小 DSL 测试\n")
    
    print("最小 DSL 包含:")
    print("  - 3 段视频片段")
    print("  - 字幕（from_transcript）")
    print("  - 背景音乐（可选）")
    print("  - 不包含 fancy overlay 动画")
    
    print("\n前置条件:")
    print("  1. DaVinci Resolve 正在运行")
    print("  2. 已打开一个项目")
    print("  3. examples/scenes.v1.json 存在")
    print("  4. examples/minimal_dsl.v1.json 存在")
    
    try:
        success = test_minimal_dsl()
        
        if success:
            print("\n" + "=" * 70)
            print("🎉 最小 DSL 测试通过！")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("❌ 最小 DSL 测试失败")
            print("=" * 70)
            
    except KeyboardInterrupt:
        print("\n\n已取消")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
