"""DaVinci Resolve Scripting API 封装（增强版 - 带智能重试）"""
import os
import sys
import time
from typing import Dict, Any, List, Optional, Tuple


def connect_resolve(retry_interval: int = 2, timeout: int = 60):
    """
    连接到 DaVinci Resolve（带智能重试机制）
    
    Args:
        retry_interval: 重试间隔（秒）
        timeout: 总超时时间（秒）
    
    Returns:
        tuple: (resolve, project)
        
    Raises:
        RuntimeError: 连接失败
    """
    # 确保 RESOLVE_SCRIPT_DIR 在 sys.path 中
    script_dir = os.environ.get("RESOLVE_SCRIPT_DIR")
    if script_dir and script_dir not in sys.path:
        sys.path.append(script_dir)
    
    try:
        import DaVinciResolveScript as dvr_script  # noqa
    except ImportError:
        raise RuntimeError(
            "无法导入 DaVinciResolveScript 模块。\n"
            "请检查环境变量 RESOLVE_SCRIPT_DIR 是否正确设置。\n"
            "运行: python scripts/set_resolve_env_auto.ps1"
        )
    
    print(f"🔌 正在尝试连接 DaVinci Resolve API (超时: {timeout}s)...")
    start_time = time.time()
    resolve = None
    
    # --- 阶段 1: 等待 API 响应（带重试） ---
    while time.time() - start_time < timeout:
        try:
            # 尝试连接
            resolve = dvr_script.scriptapp("Resolve")
            if resolve:
                print("✓ API 连接成功！")
                break
        except Exception:
            pass
        
        # 打印进度
        elapsed = int(time.time() - start_time)
        print(f"   ⏳ 等待 Resolve 启动中... ({elapsed}s)", end="\r")
        time.sleep(retry_interval)
    
    print("")  # 换行
    
    if not resolve:
        raise RuntimeError(
            "无法连接到 DaVinci Resolve API。\n"
            "可能原因：\n"
            "1. Resolve 软件未启动或正在启动画面卡住\n"
            "2. 软件未开启 '外部脚本使用' 权限\n"
            "   (偏好设置 -> 系统 -> 常规 -> 外部脚本使用)\n"
            "3. 启动超时（需要更长时间）\n"
            f"4. 已等待 {timeout}s 仍无响应"
        )
    
    # --- 阶段 2: 获取/创建项目 ---
    project_manager = resolve.GetProjectManager()
    project = project_manager.GetCurrentProject()
    
    # 如果没有打开的项目（通常刚启动时会卡在项目管理器界面）
    if not project:
        print("📂 Resolve 位于项目管理器界面，正在创建新项目...")
        
        from datetime import datetime
        project_name = f"AutoCut_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # 创建并自动加载项目
            project = project_manager.CreateProject(project_name)
            
            if not project:
                # 创建失败，可能是重名，尝试加载现有项目
                print("⚠️ 创建失败，尝试加载列表中的第一个项目...")
                projects = project_manager.GetProjectListInCurrentFolder()
                
                if projects:
                    project_manager.LoadProject(projects[0])
                    project = project_manager.GetCurrentProject()
                    
                    if project:
                        print(f"✓ 已加载项目: {project.GetName()}")
            else:
                print(f"✓ 已创建新项目: {project_name}")
                
        except Exception as e:
            print(f"❌ 创建项目时发生错误: {e}")
    
    if not project:
        raise RuntimeError(
            "无法创建或加载项目。\n"
            "请手动在 DaVinci Resolve 中双击打开一个项目，然后重试。"
        )
    
    print(f"🎬 当前项目: {project.GetName()}")
    return resolve, project


class ResolveAdapter:
    """DaVinci Resolve API 适配器"""
    
    def __init__(self):
        self.resolve = None
        self.project = None
        self.media_pool = None
        self.current_timeline = None
        
    def connect(self):
        """连接到 DaVinci Resolve"""
        self.resolve, self.project = connect_resolve()
        self.media_pool = self.project.GetMediaPool()
        return True
    
    def create_smart_bins(self, scenes_data: 'ScenesJSON') -> Dict[str, Any]:
        """
        创建智能 Bins - 根据视觉分析自动归类素材
        
        这是一个极好的辅助工具，即使不剪辑，也能帮助用户整理素材。
        
        Args:
            scenes_data: 包含 visual 信息的场景数据
        
        Returns:
            {
                "success": True,
                "bins_created": {
                    "人物": ["S0001", "S0003"],
                    "风景": ["S0002", "S0005"],
                    "特写": ["S0001", "S0004"]
                },
                "metadata_set": 10
            }
        """
        if not self.media_pool:
            raise RuntimeError("Media pool not initialized")
        
        print("\n📁 创建智能 Bins...")
        
        bins_created = {}
        metadata_count = 0
        
        # 获取 root folder
        root_folder = self.media_pool.GetRootFolder()
        
        # 创建主分类 Bin
        autocut_bin = self._get_or_create_bin(root_folder, "AutoCut_智能分类")
        
        # 按内容分类
        content_bins = {}
        content_groups = {"人物": [], "风景": [], "物品": [], "其他": []}
        
        # 按景别分类
        shot_bins = {}
        shot_groups = {"特写": [], "近景": [], "中景": [], "全景": [], "远景": []}
        
        # 按情绪分类
        mood_bins = {}
        mood_groups = {}
        
        # 按质量分类
        quality_bins = {}
        quality_groups = {"高质量(8-10)": [], "中等(5-7)": [], "低质量(1-4)": []}
        
        # 遍历场景，分类
        for scene in scenes_data.scenes:
            if not scene.visual:
                continue
            
            scene_id = scene.scene_id
            
            # 内容分类
            if scene.visual.subjects:
                has_person = any('人' in s for s in scene.visual.subjects)
                has_nature = any(
                    keyword in ' '.join(scene.visual.subjects)
                    for keyword in ['天空', '海', '山', '树', '花', '云', '日落', '风景']
                )
                
                if has_person:
                    content_groups["人物"].append(scene_id)
                elif has_nature:
                    content_groups["风景"].append(scene_id)
                else:
                    content_groups["物品"].append(scene_id)
            else:
                content_groups["其他"].append(scene_id)
            
            # 景别分类
            shot_type = scene.visual.shot_type
            if shot_type in shot_groups:
                shot_groups[shot_type].append(scene_id)
            
            # 情绪分类
            mood = scene.visual.mood
            if mood:
                if mood not in mood_groups:
                    mood_groups[mood] = []
                mood_groups[mood].append(scene_id)
            
            # 质量分类
            quality = scene.visual.quality_score
            if quality >= 8:
                quality_groups["高质量(8-10)"].append(scene_id)
            elif quality >= 5:
                quality_groups["中等(5-7)"].append(scene_id)
            else:
                quality_groups["低质量(1-4)"].append(scene_id)
        
        # 创建内容分类 Bins
        content_folder = self._get_or_create_bin(autocut_bin, "按内容分类")
        for category, scenes in content_groups.items():
            if scenes:
                bin_obj = self._get_or_create_bin(content_folder, category)
                content_bins[category] = scenes
                print(f"  ✓ {category}: {len(scenes)} 个镜头")
        
        # 创建景别分类 Bins
        shot_folder = self._get_or_create_bin(autocut_bin, "按景别分类")
        for shot_type, scenes in shot_groups.items():
            if scenes:
                bin_obj = self._get_or_create_bin(shot_folder, shot_type)
                shot_bins[shot_type] = scenes
                print(f"  ✓ {shot_type}: {len(scenes)} 个镜头")
        
        # 创建情绪分类 Bins
        if mood_groups:
            mood_folder = self._get_or_create_bin(autocut_bin, "按情绪分类")
            for mood, scenes in mood_groups.items():
                if scenes:
                    bin_obj = self._get_or_create_bin(mood_folder, mood)
                    mood_bins[mood] = scenes
                    print(f"  ✓ {mood}: {len(scenes)} 个镜头")
        
        # 创建质量分类 Bins
        quality_folder = self._get_or_create_bin(autocut_bin, "按质量分类")
        for quality_level, scenes in quality_groups.items():
            if scenes:
                bin_obj = self._get_or_create_bin(quality_folder, quality_level)
                quality_bins[quality_level] = scenes
                print(f"  ✓ {quality_level}: {len(scenes)} 个镜头")
        
        # 设置元数据（如果 API 支持）
        # 注意：Resolve API 对元数据的支持有限
        # 这里提供一个框架，实际效果取决于 Resolve 版本
        try:
            clips = root_folder.GetClipList()
            if clips:
                for clip in clips:
                    # 尝试设置元数据
                    # 注意：这可能不会在所有版本中工作
                    try:
                        clip.SetMetadata("AutoCut_Analyzed", "True")
                        metadata_count += 1
                    except:
                        pass
        except:
            pass
        
        bins_created.update({
            "内容分类": content_bins,
            "景别分类": shot_bins,
            "情绪分类": mood_bins,
            "质量分类": quality_bins
        })
        
        print(f"\n✅ 智能 Bins 创建完成")
        print(f"  - 总分类: {len(content_bins) + len(shot_bins) + len(mood_bins) + len(quality_bins)}")
        print(f"  - 元数据标记: {metadata_count}")
        
        return {
            "success": True,
            "bins_created": bins_created,
            "metadata_set": metadata_count
        }
    
    def _get_or_create_bin(self, parent_folder, bin_name: str):
        """
        获取或创建 Bin
        
        Args:
            parent_folder: 父文件夹
            bin_name: Bin 名称
        
        Returns:
            Bin 对象
        """
        try:
            # 尝试获取现有 Bin
            subfolders = parent_folder.GetSubFolderList()
            if subfolders:
                for folder in subfolders:
                    if folder.GetName() == bin_name:
                        return folder
            
            # 创建新 Bin
            new_bin = self.media_pool.AddSubFolder(parent_folder, bin_name)
            return new_bin
        except Exception as e:
            print(f"  ⚠️ 创建 Bin 失败 ({bin_name}): {e}")
            return parent_folder
    
    def create_timeline(self, name: str, framerate: float, resolution: dict):
        """
        创建新时间线
        
        Args:
            name: 时间线名称
            framerate: 帧率
            resolution: 分辨率字典 {"width": 1920, "height": 1080}
        """
        if not self.media_pool:
            raise RuntimeError("Media pool not initialized")
        
        self.current_timeline = self.media_pool.CreateEmptyTimeline(name)
        
        if not self.current_timeline:
            raise RuntimeError(f"Failed to create timeline: {name}")
        
        # 设置时间线属性
        self.current_timeline.SetSetting("timelineFrameRate", str(framerate))
        self.current_timeline.SetSetting("timelineResolutionWidth", str(resolution["width"]))
        self.current_timeline.SetSetting("timelineResolutionHeight", str(resolution["height"]))
        
        return self.current_timeline
    
    def append_clip(self, source: str, start: float, end: float, track: int = 1):
        """
        添加片段到时间线末尾
        
        Args:
            source: 媒体文件路径
            start: 开始时间（秒）
            end: 结束时间（秒）
            track: 轨道编号（默认 1）
        """
        if not self.current_timeline:
            raise RuntimeError("No active timeline")
        
        # 导入媒体到媒体池
        media_storage = self.resolve.GetMediaStorage()
        clips = media_storage.AddItemListToMediaPool([source])
        
        if not clips:
            raise RuntimeError(f"Failed to import media: {source}")
        
        clip = clips[0]
        fps = float(self.current_timeline.GetSetting("timelineFrameRate"))
        
        # 构建片段信息
        clip_info = {
            "mediaPoolItem": clip,
            "startFrame": int(start * fps) if start > 0 else 0,
            "endFrame": int(end * fps) if end > 0 else 0,
            "trackIndex": track
        }
        
        result = self.media_pool.AppendToTimeline([clip_info])
        
        if not result:
            raise RuntimeError(f"Failed to append clip: {source}")
        
        return result
    
    def import_srt(self, srt_path: str, track: int = 2):
        """
        导入 SRT 字幕文件
        
        Args:
            srt_path: SRT 文件路径
            track: 字幕轨道编号（默认 2）
        """
        if not self.current_timeline:
            raise RuntimeError("No active timeline")
        
        # Resolve 支持直接导入 SRT
        result = self.current_timeline.ImportIntoTimeline(srt_path)
        
        if not result:
            raise RuntimeError(f"Failed to import SRT: {srt_path}")
        
        return result
    
    def add_audio(self, audio_path: str, start: float = 0, volume: float = 1.0):
        """
        添加音频轨道
        
        Args:
            audio_path: 音频文件路径
            start: 开始时间（秒）
            volume: 音量（线性，1.0 = 100%）
        
        Returns:
            添加的 TimelineItem 列表
        """
        if not self.current_timeline:
            raise RuntimeError("No active timeline")
        
        # 导入音频到媒体池
        media_storage = self.resolve.GetMediaStorage()
        audio_clips = media_storage.AddItemListToMediaPool([audio_path])
        
        if not audio_clips:
            raise RuntimeError(f"Failed to import audio: {audio_path}")
        
        # 添加到音频轨道
        # AppendToTimeline 返回的是 Append 进去的 clips 列表
        appended_items = self.media_pool.AppendToTimeline(audio_clips)
        
        if not appended_items:
            raise RuntimeError(f"Failed to append audio: {audio_path}")
        
        # 设置音量
        if volume != 1.0:
            for item in appended_items:
                # Resolve API 中设置音量通常需要 SetProperty
                # 注意：不同版本 API 键名可能不同，通常是 "AudioVolume" 或 "AudioLevel"
                # 这是一个 MVP 妥协，如果没有 SetProperty，可能需要手动调节
                
                # 尝试多个可能的属性名
                success = False
                
                # 尝试 1: AudioLevel (Resolve 19+)
                try:
                    success = item.SetProperty("AudioLevel", volume)
                    if success:
                        print(f"✓ 音量设置成功: {volume} (AudioLevel)")
                        break
                except:
                    pass
                
                # 尝试 2: Volume (某些版本)
                if not success:
                    try:
                        success = item.SetProperty("Volume", volume)
                        if success:
                            print(f"✓ 音量设置成功: {volume} (Volume)")
                            break
                    except:
                        pass
                
                # 尝试 3: AudioVolume (早期版本)
                if not success:
                    try:
                        success = item.SetProperty("AudioVolume", volume)
                        if success:
                            print(f"✓ 音量设置成功: {volume} (AudioVolume)")
                            break
                    except:
                        pass
                
                # 如果所有尝试都失败
                if not success:
                    print(f"⚠️ Warning: Could not set volume for {audio_path}")
                    print(f"   请在 Resolve Inspector 中手动调整音量")
        
        return appended_items
    
    def add_text_overlay(
        self, 
        text: str, 
        start_frame: int, 
        duration_frames: int,
        track: int = 2,
        style: dict = None
    ):
        """
        添加文字叠加层（overlay_text）- 爆款视频的关键
        
        实现策略：
        1. 优先使用 SRT 字幕（最稳定，兼容性好）
        2. 备选使用 Fusion Title（高级功能）
        
        Args:
            text: 文字内容
            start_frame: 开始帧
            duration_frames: 持续帧数
            track: 视频轨道（默认 2，叠加在主视频上方）
            style: 文字样式字典（可选）
        """
        if not self.current_timeline:
            raise RuntimeError("No active timeline")
        
        # 获取帧率
        fps = float(self.current_timeline.GetSetting("timelineFrameRate"))
        start_sec = start_frame / fps
        duration_sec = duration_frames / fps
        
        # 方法 1: 使用 SRT 字幕（最稳定）
        try:
            self._add_text_via_srt(text, start_sec, duration_sec, style)
        except Exception as e:
            print(f"SRT method failed: {e}, trying Fusion title...")
            # 方法 2: 使用 Fusion Title（备选）
            try:
                self._add_fusion_title(text, start_frame, duration_frames, track, style)
            except Exception as e2:
                print(f"Fusion title also failed: {e2}")
                raise RuntimeError(f"Failed to add text overlay: {e}, {e2}")
    
    def _add_text_via_srt(self, text: str, start_sec: float, duration_sec: float, style: dict = None):
        """
        使用 SRT 字幕添加文字（最稳定的方案）
        
        优点：
        - Resolve 原生支持 SRT
        - 稳定可靠
        - 可以在 Resolve 中手动调整样式
        
        缺点：
        - 样式控制有限（需要在 Resolve 中手动设置）
        """
        import tempfile
        import os
        
        # 生成 SRT 内容
        srt_content = self._generate_srt_entry(1, text, start_sec, start_sec + duration_sec)
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.srt', 
            delete=False, 
            encoding='utf-8'
        ) as tmp:
            tmp.write(srt_content)
            tmp_path = tmp.name
        
        try:
            # 导入 SRT 到时间线
            result = self.current_timeline.ImportIntoTimeline(tmp_path)
            
            if not result:
                raise RuntimeError("Failed to import SRT")
            
            return result
            
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def _add_fusion_title(self, text: str, start_frame: int, duration: int, track: int, style: dict):
        """
        使用 Fusion Title 添加文字（高级方案）
        
        优点：
        - 完全控制样式
        - 支持动画效果
        
        缺点：
        - API 支持有限
        - 需要 Resolve Studio 版本
        """
        # 注意：Resolve API 对 Fusion Title 的支持有限
        # 这里提供一个简化的实现框架
        
        # 尝试从 Effects 库中获取 Title 生成器
        # 实际实现需要根据 Resolve 版本调整
        
        # 临时方案：创建一个简单的 Title
        # 在实际使用中，建议预先在 Resolve 中创建 Title 模板
        # 然后通过 API 导入并修改参数
        
        raise NotImplementedError(
            "Fusion Title support is limited in Resolve API. "
            "Please use SRT method or create Title templates manually."
        )
    
    def _generate_srt_entry(self, index: int, text: str, start_sec: float, end_sec: float) -> str:
        """
        生成单个 SRT 字幕条目
        
        格式：
        1
        00:00:01,000 --> 00:00:03,000
        字幕内容
        """
        start_time = self._seconds_to_srt_time(start_sec)
        end_time = self._seconds_to_srt_time(end_sec)
        
        return f"{index}\n{start_time} --> {end_time}\n{text}\n\n"
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """
        将秒数转换为 SRT 时间格式
        
        格式: HH:MM:SS,mmm
        例如: 00:00:01,500
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def create_text_layer_from_dsl(self, text_items: list, track_index: int = 3):
        """
        从 DSL 中的文字列表批量生成字幕轨道
        
        这是处理 overlay_text 的推荐方法：
        将所有文字叠加合并为一个 SRT 文件，一次性导入
        
        Args:
            text_items: 文字列表，格式：[
                {
                    "content": "第一步就错了",
                    "start_frame": 30,
                    "duration_frames": 60
                },
                ...
            ]
            track_index: 字幕轨道索引
        
        Returns:
            导入结果
        """
        if not text_items:
            return None
        
        import tempfile
        import os
        
        # 获取帧率
        fps = float(self.current_timeline.GetSetting("timelineFrameRate"))
        
        # 生成完整的 SRT 内容
        srt_content = ""
        for i, item in enumerate(text_items, start=1):
            start_sec = item['start_frame'] / fps
            duration_sec = item['duration_frames'] / fps
            end_sec = start_sec + duration_sec
            
            srt_content += self._generate_srt_entry(
                index=i,
                text=item['content'],
                start_sec=start_sec,
                end_sec=end_sec
            )
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.srt',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write(srt_content)
            tmp_path = tmp.name
        
        try:
            # 导入到时间线
            result = self.current_timeline.ImportIntoTimeline(tmp_path)
            
            if not result:
                raise RuntimeError("Failed to import text layer SRT")
            
            print(f"✓ 成功导入 {len(text_items)} 个文字叠加")
            return result
            
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def render_subtitles_from_transcript(
        self, 
        transcript_segments: list,
        fps: float,
        style: str = "bold_yellow"
    ):
        """
        从 transcript 渲染字幕到时间线（使用 SRT 方案）
        
        这是最稳定的字幕渲染方案：
        1. 将 transcript 转换为 SRT 格式
        2. 导入到 Resolve 时间线
        3. 在 Resolve 中手动调整样式（或使用预设）
        
        Args:
            transcript_segments: transcript.json 中的 segments 列表
            fps: 时间线帧率
            style: 字幕样式预设（用于文档说明，实际样式在 Resolve 中设置）
        
        样式预设说明：
        - bold_yellow: 抖音风格（粗体黄字黑边）- 需在 Resolve 中手动设置
        - clean_white: 简洁白字
        - elegant_black: 优雅黑字
        
        注意：由于 Resolve API 限制，样式需要在 Resolve 中手动设置：
        1. 导入字幕后，在 Edit 页面选中字幕轨道
        2. 在 Inspector 中调整字体、颜色、描边等
        3. 可以保存为预设供后续使用
        """
        if not transcript_segments:
            print("Warning: No transcript segments to render")
            return None
        
        import tempfile
        import os
        
        # 生成完整的 SRT 内容
        srt_content = ""
        for i, segment in enumerate(transcript_segments, start=1):
            start_sec = segment["start"]
            end_sec = segment["end"]
            text = segment["text"]
            
            srt_content += self._generate_srt_entry(
                index=i,
                text=text,
                start_sec=start_sec,
                end_sec=end_sec
            )
        
        # 写入临时文件
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.srt',
            delete=False,
            encoding='utf-8'
        ) as tmp:
            tmp.write(srt_content)
            tmp_path = tmp.name
        
        try:
            # 导入到时间线
            result = self.current_timeline.ImportIntoTimeline(tmp_path)
            
            if not result:
                raise RuntimeError("Failed to import subtitles")
            
            print(f"✓ 成功导入 {len(transcript_segments)} 段字幕")
            print(f"  样式建议: {style}")
            print(f"  请在 Resolve Inspector 中调整字幕样式")
            
            return result
            
        finally:
            # 清理临时文件
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    def export_transcript_to_srt(self, transcript_segments: list, output_path: str):
        """
        将 transcript 导出为 SRT 文件（独立工具函数）
        
        可以先导出 SRT，然后在 Resolve 中手动导入并调整样式
        
        Args:
            transcript_segments: transcript.json 中的 segments 列表
            output_path: 输出 SRT 文件路径
        """
        srt_content = ""
        for i, segment in enumerate(transcript_segments, start=1):
            srt_content += self._generate_srt_entry(
                index=i,
                text=segment["text"],
                start_sec=segment["start"],
                end_sec=segment["end"]
            )
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        print(f"✓ SRT 文件已导出: {output_path}")
        return output_path
    
    def export(self, output_path: str, preset: str = "H.264", quality: str = "high"):
        """
        导出时间线
        
        Args:
            output_path: 输出文件路径
            preset: 渲染预设名称
            quality: 质量设置（low, medium, high）
        """
        if not self.current_timeline:
            raise RuntimeError("No active timeline")
        
        from pathlib import Path
        
        # 设置当前时间线
        self.project.SetCurrentTimeline(self.current_timeline)
        
        # 设置渲染参数
        output_dir = str(Path(output_path).parent)
        output_name = Path(output_path).stem
        
        render_settings = {
            "SelectAllFrames": 1,
            "TargetDir": output_dir,
            "CustomName": output_name,
            "ExportVideo": 1,
            "ExportAudio": 1
        }
        
        self.project.SetRenderSettings(render_settings)
        
        # 加载预设
        if preset:
            preset_loaded = self.project.LoadRenderPreset(preset)
            if not preset_loaded:
                print(f"Warning: Failed to load preset '{preset}', using default")
        
        # 添加到渲染队列
        job_id = self.project.AddRenderJob()
        if not job_id:
            raise RuntimeError("Failed to add render job")
        
        # 开始渲染
        render_started = self.project.StartRendering(job_id)
        if not render_started:
            raise RuntimeError("Failed to start rendering")
        
        return job_id
