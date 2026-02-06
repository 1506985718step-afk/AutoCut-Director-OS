"""
AutoCut Director - 完整流水线脚本

一键执行完整的 AI 驱动视频剪辑流程：
1. 分析素材（EDL → scenes.json + Audio → transcript.json）
2. AI 生成剪辑脚本（LLM → editing_dsl.json）
3. 执行剪辑（DSL → Actions → Resolve → 成片）
"""
import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 导入核心模块
from app.tools.scene_from_edl import parse_edl_to_scenes
from app.tools.asr_whisper import transcribe_audio
from app.tools.srt_generator import transcript_to_srt, dsl_to_srt_files
from app.core.llm_engine import LLMDirector
from app.models.schemas import ScenesJSON, TranscriptJSON, DSLValidator
from app.executor.actions import (
    create_timeline,
    append_scene,
    create_text_layer,
    render_subtitles,
    add_music,
    export_mp4
)
from app.executor.runner import run_actions


class Pipeline:
    """完整流水线管理器"""
    
    def __init__(self, config: dict):
        """
        初始化流水线
        
        Args:
            config: 配置字典 {
                "edl_path": "input.edl",
                "audio_path": "input.mp4",
                "primary_clip_path": "D:/Footage/input.mp4",
                "fps": 30,
                "style": "抖音爆款风格",
                "output_path": "D:/Output/final.mp4",
                "output_dir": "output"
            }
        """
        self.config = config
        self.output_dir = Path(config.get("output_dir", "output"))
        self.output_dir.mkdir(exist_ok=True)
        
        # 中间产物路径
        self.scenes_path = self.output_dir / "scenes.json"
        self.transcript_path = self.output_dir / "transcript.json"
        self.dsl_path = self.output_dir / "editing_dsl.json"
        self.trace_path = self.output_dir / "trace.json"
        
        # 数据存储
        self.scenes = None
        self.transcript = None
        self.dsl = None
        self.trace = None
    
    def print_stage(self, stage: int, title: str):
        """打印阶段标题"""
        print("\n" + "=" * 70)
        print(f"{stage}️⃣  {title}")
        print("=" * 70)
    
    def print_success(self, message: str):
        """打印成功消息"""
        print(f"✅ {message}")
    
    def print_error(self, message: str):
        """打印错误消息"""
        print(f"❌ {message}")
    
    def print_info(self, message: str):
        """打印信息消息"""
        print(f"ℹ️  {message}")
    
    async def stage_1_analyze(self):
        """阶段 1: 分析素材"""
        self.print_stage(1, "分析素材 - EDL + Audio → scenes.json + transcript.json")
        
        # 1.1 解析 EDL
        print("\n📹 解析 EDL 文件...")
        try:
            edl_path = self.config["edl_path"]
            fps = self.config.get("fps", 30)
            primary_clip = self.config["primary_clip_path"]
            
            scenes_data = parse_edl_to_scenes(edl_path, fps, primary_clip)
            self.scenes = ScenesJSON(**scenes_data)
            
            # 保存 scenes.json
            self.scenes_path.write_text(
                json.dumps(scenes_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            self.print_success(f"解析成功，生成 {len(self.scenes.scenes)} 个场景")
            for scene in self.scenes.scenes[:3]:
                print(f"   - {scene.scene_id}: {scene.start_tc} → {scene.end_tc}")
            if len(self.scenes.scenes) > 3:
                print(f"   ... 共 {len(self.scenes.scenes)} 个场景")
            
            self.print_info(f"已保存: {self.scenes_path}")
            
        except Exception as e:
            self.print_error(f"EDL 解析失败: {e}")
            return False
        
        # 1.2 转录音频
        print("\n🎤 转录音频文件...")
        try:
            audio_path = self.config["audio_path"]
            
            # 检查是否已有 transcript
            if self.transcript_path.exists():
                self.print_info("发现已有 transcript.json，跳过转录")
                transcript_data = json.loads(self.transcript_path.read_text(encoding="utf-8"))
            else:
                self.print_info("使用 Whisper 转录音频（可能需要几分钟）...")
                transcript_data = transcribe_audio(
                    audio_path,
                    model=self.config.get("whisper_model", "base"),
                    language=self.config.get("language", "zh")
                )
                
                # 保存 transcript.json
                self.transcript_path.write_text(
                    json.dumps(transcript_data, ensure_ascii=False, indent=2),
                    encoding="utf-8"
                )
            
            self.transcript = TranscriptJSON(**transcript_data)
            
            self.print_success(f"转录成功，生成 {len(self.transcript.segments)} 段字幕")
            for seg in self.transcript.segments[:3]:
                print(f"   - [{seg.start:.1f}s] {seg.text}")
            if len(self.transcript.segments) > 3:
                print(f"   ... 共 {len(self.transcript.segments)} 段")
            
            self.print_info(f"已保存: {self.transcript_path}")
            
        except Exception as e:
            self.print_error(f"音频转录失败: {e}")
            return False
        
        return True
    
    async def stage_2_generate_dsl(self):
        """阶段 2: AI 生成剪辑脚本"""
        self.print_stage(2, "AI 导演构思 - LLM → editing_dsl.json")
        
        print("\n🧠 调用 LLM 生成剪辑脚本...")
        try:
            director = LLMDirector()
            style_prompt = self.config.get("style", "抖音爆款风格：节奏快、文字多、强调关键词")
            
            self.print_info(f"风格: {style_prompt}")
            self.print_info("正在生成...")
            
            dsl_data = director.generate_editing_dsl(
                scenes=self.scenes,
                transcript=self.transcript,
                style_prompt=style_prompt
            )
            
            self.dsl = dsl_data
            
            # 保存 DSL
            self.dsl_path.write_text(
                json.dumps(dsl_data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            
            self.print_success("AI 生成成功！")
            
            # 显示剪辑计划
            timeline = dsl_data["editing_plan"]["timeline"]
            print(f"\n📋 剪辑计划（共 {len(timeline)} 个片段）:")
            for item in timeline[:5]:
                scene_id = item["scene_id"]
                trim = item["trim_frames"]
                purpose = item.get("purpose", "body")
                text = item.get("overlay_text", "")
                print(f"   {item['order']}. {scene_id} [{trim[0]}-{trim[1]}] ({purpose}) {text}")
            if len(timeline) > 5:
                print(f"   ... 共 {len(timeline)} 个片段")
            
            self.print_info(f"已保存: {self.dsl_path}")
            
        except Exception as e:
            self.print_error(f"LLM 生成失败: {e}")
            self.print_info("请检查 .env 中的 OPENAI_API_KEY 配置")
            return False
        
        # 验证 DSL
        print("\n🔍 验证 DSL 硬规则...")
        try:
            scenes_data = json.loads(self.scenes_path.read_text(encoding="utf-8"))
            errors = DSLValidator.validate_dsl_against_scenes(dsl_data, scenes_data)
            
            if errors:
                self.print_error("验证失败（AI 幻觉检测）:")
                for err in errors:
                    print(f"   - {err}")
                return False
            
            self.print_success("验证通过！AI 没有幻觉")
            
        except Exception as e:
            self.print_error(f"验证失败: {e}")
            return False
        
        return True
    
    async def stage_3_execute(self):
        """阶段 3: 执行剪辑"""
        self.print_stage(3, "DaVinci Resolve 执行 - DSL → Actions → 成片")
        
        print("\n🎬 转换 DSL 为执行动作...")
        try:
            actions = self._dsl_to_actions()
            self.print_success(f"生成 {len(actions)} 个执行动作")
            
        except Exception as e:
            self.print_error(f"DSL 转换失败: {e}")
            return False
        
        # 检查 Resolve
        print("\n🔌 连接 DaVinci Resolve...")
        self.print_info("请确保 DaVinci Resolve 正在运行")
        
        try:
            from app.executor.resolve_adapter import connect_resolve
            resolve, proj = connect_resolve()
            self.print_success("连接成功！")
            
        except Exception as e:
            self.print_error(f"连接失败: {e}")
            self.print_info("请启动 DaVinci Resolve 并打开项目")
            return False
        
        # 执行动作
        print("\n⚙️  执行剪辑动作...")
        try:
            self.trace = run_actions(actions, trace_path=str(self.trace_path))
            
            # 显示执行结果
            print("\n📊 执行结果:")
            for t in self.trace:
                status = "✅" if t["ok"] else "❌"
                print(f"   {status} {t['action']}: {t['detail']} ({t['took_ms']}ms)")
            
            # 检查是否全部成功
            all_ok = all(t["ok"] for t in self.trace)
            
            if all_ok:
                self.print_success("所有动作执行成功！")
            else:
                self.print_error("部分动作执行失败")
                return False
            
            self.print_info(f"执行日志: {self.trace_path}")
            
        except Exception as e:
            self.print_error(f"执行失败: {e}")
            return False
        
        return True
    
    def _dsl_to_actions(self):
        """将 DSL 转换为 Action 列表"""
        actions = []
        
        dsl = self.dsl
        scenes_data = json.loads(self.scenes_path.read_text(encoding="utf-8"))
        transcript_data = json.loads(self.transcript_path.read_text(encoding="utf-8"))
        
        fps = self.config.get("fps", 30)
        
        # 1. 创建时间线
        resolution_str = dsl["export"]["resolution"]  # "1080x1920"
        width, height = map(int, resolution_str.split("x"))
        
        actions.append(create_timeline(
            name=f"AutoCut_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            fps=fps,
            resolution={"width": width, "height": height}
        ))
        
        # 2. 添加视频片段
        primary_clip = self.config["primary_clip_path"]
        
        for item in dsl["editing_plan"]["timeline"]:
            scene_id = item["scene_id"]
            trim_frames = item["trim_frames"]
            
            actions.append(append_scene(
                scene_id=scene_id,
                in_frame=trim_frames[0],
                out_frame=trim_frames[1],
                source=primary_clip
            ))
        
        # 3. 添加文字叠加（如果有）
        text_items = []
        for item in dsl["editing_plan"]["timeline"]:
            if item.get("overlay_text"):
                text_items.append({
                    "content": item["overlay_text"],
                    "start_frame": item["trim_frames"][0],
                    "duration_frames": item["trim_frames"][1] - item["trim_frames"][0]
                })
        
        if text_items:
            actions.append(create_text_layer(
                text_items=text_items,
                track_index=3
            ))
        
        # 4. 渲染字幕
        if dsl["editing_plan"]["subtitles"]["mode"] == "from_transcript":
            style = dsl["editing_plan"]["subtitles"].get("style", "bold_yellow")
            actions.append(render_subtitles(
                transcript_segments=transcript_data["segments"],
                fps=fps,
                style=style
            ))
        
        # 5. 添加背景音乐（如果有）
        music = dsl["editing_plan"].get("music", {})
        if music.get("track_path"):
            actions.append(add_music(
                path=music["track_path"],
                volume_db=music.get("volume_db", -18)
            ))
        
        # 6. 导出
        output_path = self.config.get("output_path", "D:/Output/autocut_output.mp4")
        actions.append(export_mp4(
            path=output_path,
            resolution=resolution_str
        ))
        
        return actions
    
    async def run(self):
        """运行完整流水线"""
        print("\n" + "🎬" * 35)
        print("AutoCut Director - AI 驱动的自动视频剪辑系统")
        print("🎬" * 35)
        
        start_time = datetime.now()
        
        # 阶段 1: 分析素材
        if not await self.stage_1_analyze():
            self.print_error("流水线中断：分析素材失败")
            return False
        
        # 阶段 2: AI 生成
        if not await self.stage_2_generate_dsl():
            self.print_error("流水线中断：AI 生成失败")
            return False
        
        # 阶段 3: 执行剪辑
        if not await self.stage_3_execute():
            self.print_error("流水线中断：执行剪辑失败")
            return False
        
        # 完成
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 70)
        print("🎉 流水线执行完成！")
        print("=" * 70)
        
        print(f"\n⏱️  总耗时: {duration:.1f} 秒")
        print(f"\n📁 输出文件:")
        print(f"   - 场景: {self.scenes_path}")
        print(f"   - 转录: {self.transcript_path}")
        print(f"   - DSL: {self.dsl_path}")
        print(f"   - 执行日志: {self.trace_path}")
        print(f"   - 成片: {self.config.get('output_path', 'N/A')}")
        
        print(f"\n✨ 成片已生成，请在 DaVinci Resolve 中查看！")
        
        return True


async def main():
    """主函数"""
    # 配置
    config = {
        # 输入文件
        "edl_path": "examples/test.edl",
        "audio_path": "D:/Footage/input.mp4",  # 请替换为实际路径
        "primary_clip_path": "D:/Footage/input.mp4",  # 请替换为实际路径
        
        # 参数
        "fps": 30,
        "language": "zh",
        "whisper_model": "base",
        
        # 风格
        "style": "抖音爆款风格：节奏快、文字多、强调关键词",
        
        # 输出
        "output_path": "D:/Output/autocut_final.mp4",  # 请替换为实际路径
        "output_dir": "output"
    }
    
    # 从命令行参数读取配置（可选）
    if len(sys.argv) > 1:
        import argparse
        parser = argparse.ArgumentParser(description="AutoCut Director Pipeline")
        parser.add_argument("--edl", help="EDL 文件路径")
        parser.add_argument("--audio", help="音频文件路径")
        parser.add_argument("--clip", help="主视频片段路径")
        parser.add_argument("--fps", type=int, default=30, help="帧率")
        parser.add_argument("--style", help="剪辑风格")
        parser.add_argument("--output", help="输出文件路径")
        
        args = parser.parse_args()
        
        if args.edl:
            config["edl_path"] = args.edl
        if args.audio:
            config["audio_path"] = args.audio
        if args.clip:
            config["primary_clip_path"] = args.clip
        if args.fps:
            config["fps"] = args.fps
        if args.style:
            config["style"] = args.style
        if args.output:
            config["output_path"] = args.output
    
    # 运行流水线
    pipeline = Pipeline(config)
    success = await pipeline.run()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
