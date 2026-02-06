"""完整 AI 工作流示例 - 从素材到成片"""
import json
from pathlib import Path
from app.tools.scene_from_edl import parse_edl_to_scenes
from app.tools.asr_whisper import transcribe_audio
from app.core.llm_engine import LLMDirector
from app.models.schemas import ScenesJSON, TranscriptJSON, DSLValidator
from app.executor.actions import (
    create_timeline,
    append_scene,
    render_subtitles,
    add_text_overlay,
    add_music,
    export_mp4
)
from app.executor.runner import run_actions


def ai_workflow_demo():
    """
    完整 AI 工作流演示
    
    流程：
    1. EDL → scenes.json（场景切分）
    2. Audio → transcript.json（语音转录）
    3. LLM → editing_dsl.json（AI 生成剪辑脚本）
    4. DSL → Actions（转换为执行动作）
    5. Resolve → 执行剪辑（自动化剪辑）
    """
    print("=" * 70)
    print("AutoCut Director - 完整 AI 工作流演示")
    print("=" * 70)
    
    # ========================================================================
    # Stage 1: 场景切分（EDL → scenes.json）
    # ========================================================================
    print("\n[Stage 1] 场景切分 - EDL → scenes.json")
    print("-" * 70)
    
    edl_path = "examples/test.edl"
    primary_clip = "D:/Footage/input.mp4"  # 请替换为实际路径
    fps = 30
    
    print(f"解析 EDL: {edl_path}")
    scenes_data = parse_edl_to_scenes(edl_path, fps, primary_clip)
    scenes = ScenesJSON(**scenes_data)
    
    print(f"✓ 解析成功，生成 {len(scenes.scenes)} 个场景")
    for scene in scenes.scenes[:3]:
        print(f"  - {scene.scene_id}: {scene.start_tc} → {scene.end_tc}")
    
    # 保存 scenes.json
    scenes_path = Path("examples/scenes.ai_workflow.json")
    scenes_path.write_text(
        json.dumps(scenes_data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✓ 保存到: {scenes_path}")
    
    # ========================================================================
    # Stage 2: 语音转录（Audio → transcript.json）
    # ========================================================================
    print("\n[Stage 2] 语音转录 - Audio → transcript.json")
    print("-" * 70)
    
    audio_path = "D:/Footage/input.mp4"  # 可以直接用视频文件
    
    print(f"转录音频: {audio_path}")
    print("(使用 Whisper 模型，可能需要几分钟...)")
    
    # 实际项目中取消注释
    # transcript_data = transcribe_audio(audio_path, model="base", language="zh")
    # transcript = TranscriptJSON(**transcript_data)
    
    # 演示用：加载示例
    transcript_path = Path("examples/transcript.v1.json")
    transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
    transcript = TranscriptJSON(**transcript_data)
    
    print(f"✓ 转录成功，生成 {len(transcript.segments)} 个字幕段")
    for seg in transcript.segments[:3]:
        print(f"  - [{seg.start:.1f}s] {seg.text}")
    
    # ========================================================================
    # Stage 3: AI 生成剪辑脚本（LLM → editing_dsl.json）
    # ========================================================================
    print("\n[Stage 3] AI 生成剪辑脚本 - LLM → editing_dsl.json")
    print("-" * 70)
    
    print("调用 LLM 生成剪辑脚本...")
    
    try:
        director = LLMDirector()
        
        style_prompt = """
抖音爆款风格：
1. 开头 3 秒必须有强烈的 Hook（钩子），吸引观众停留
2. 节奏快，每 3-5 秒切换画面或文字
3. 删除所有废话、停顿、重复内容
4. 文字叠加要简短有力（5-8 字），突出关键信息
5. 强调数字和对比（如"90%的人"、"第一步"）
6. 总时长控制在 30-60 秒
"""
        
        dsl = director.generate_editing_dsl(scenes, transcript, style_prompt)
        
        print("✓ AI 生成成功！")
        
        # 验证 DSL
        print("\n验证 DSL 硬规则...")
        errors = DSLValidator.validate_dsl_against_scenes(dsl, scenes_data)
        
        if errors:
            print("✗ 验证失败（AI 幻觉检测）：")
            for err in errors:
                print(f"  - {err}")
            return False
        
        print("✓ 验证通过！AI 没有幻觉")
        
        # 保存 DSL
        dsl_path = Path("examples/editing_dsl.ai_workflow.json")
        dsl_path.write_text(
            json.dumps(dsl, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"✓ 保存到: {dsl_path}")
        
        # 显示剪辑计划
        timeline = dsl["editing_plan"]["timeline"]
        print(f"\n剪辑计划预览（共 {len(timeline)} 个片段）：")
        for item in timeline[:5]:
            scene_id = item["scene_id"]
            trim = item["trim_frames"]
            purpose = item.get("purpose", "body")
            text = item.get("overlay_text", "")
            print(f"  {item['order']}. {scene_id} [{trim[0]}-{trim[1]}] ({purpose}) {text}")
        
    except ValueError as e:
        print(f"✗ LLM 调用失败: {e}")
        print("\n请确保在 .env 中配置了 OPENAI_API_KEY")
        return False
    
    # ========================================================================
    # Stage 4: DSL → Actions（转换为执行动作）
    # ========================================================================
    print("\n[Stage 4] DSL → Actions（转换为执行动作）")
    print("-" * 70)
    
    actions = []
    
    # 1. 创建时间线
    resolution_str = dsl["export"]["resolution"]  # "1080x1920"
    width, height = map(int, resolution_str.split("x"))
    
    actions.append(create_timeline(
        name="AI_Generated_Timeline",
        fps=fps,
        resolution={"width": width, "height": height}
    ))
    
    # 2. 添加视频片段
    for item in dsl["editing_plan"]["timeline"]:
        scene_id = item["scene_id"]
        trim_frames = item["trim_frames"]
        
        actions.append(append_scene(
            scene_id=scene_id,
            in_frame=trim_frames[0],
            out_frame=trim_frames[1],
            source=primary_clip
        ))
        
        # 如果有 overlay_text，添加文字叠加
        if item.get("overlay_text"):
            duration = trim_frames[1] - trim_frames[0]
            actions.append(add_text_overlay(
                text=item["overlay_text"],
                start_frame=trim_frames[0],
                duration_frames=duration
            ))
    
    # 3. 渲染字幕
    if dsl["editing_plan"]["subtitles"]["mode"] == "from_transcript":
        style = dsl["editing_plan"]["subtitles"].get("style", "bold_yellow")
        actions.append(render_subtitles(
            transcript_segments=transcript_data["segments"],
            fps=fps,
            style=style
        ))
    
    # 4. 添加背景音乐（如果有）
    music = dsl["editing_plan"].get("music", {})
    if music.get("track_path"):
        actions.append(add_music(
            path=music["track_path"],
            volume_db=music.get("volume_db", -18)
        ))
    
    # 5. 导出
    output_path = "D:/Output/ai_generated_video.mp4"  # 请替换为实际路径
    actions.append(export_mp4(
        path=output_path,
        resolution=resolution_str
    ))
    
    print(f"✓ 生成 {len(actions)} 个执行动作")
    
    # ========================================================================
    # Stage 5: Resolve 执行剪辑
    # ========================================================================
    print("\n[Stage 5] Resolve 执行剪辑（自动化）")
    print("-" * 70)
    
    print("注意：此步骤需要 DaVinci Resolve 运行")
    print("按 Enter 继续执行，或 Ctrl+C 取消...")
    try:
        input()
    except KeyboardInterrupt:
        print("\n✗ 用户取消执行")
        return False
    
    print("\n执行动作序列...")
    try:
        trace = run_actions(actions, trace_path="ai_workflow_trace.json")
        
        print("\n执行结果：")
        for t in trace:
            status = "✓" if t["ok"] else "✗"
            print(f"{status} {t['action']}: {t['detail']} ({t['took_ms']}ms)")
        
        # 检查是否全部成功
        all_ok = all(t["ok"] for t in trace)
        
        if all_ok:
            print("\n" + "=" * 70)
            print("🎉 完整工作流执行成功！")
            print("=" * 70)
            print(f"\n成片已导出到: {output_path}")
            print("\n工作流总结：")
            print(f"  - 输入: {edl_path} + {audio_path}")
            print(f"  - 场景: {len(scenes.scenes)} 个")
            print(f"  - 字幕: {len(transcript.segments)} 段")
            print(f"  - 片段: {len(timeline)} 个")
            print(f"  - 输出: {output_path}")
        else:
            print("\n✗ 部分动作执行失败，请查看 trace")
        
    except Exception as e:
        print(f"\n✗ 执行失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("\n提示：")
    print("- 请确保 DaVinci Resolve 正在运行")
    print("- 请在 .env 中配置 OPENAI_API_KEY")
    print("- 请替换示例中的文件路径为实际路径")
    print("\n按 Enter 开始演示...")
    try:
        input()
        ai_workflow_demo()
    except KeyboardInterrupt:
        print("\n演示取消")
