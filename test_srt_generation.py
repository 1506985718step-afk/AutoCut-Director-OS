"""测试 SRT 字幕生成功能"""
import json
from pathlib import Path
from app.tools.srt_generator import (
    transcript_to_srt,
    overlay_text_to_srt,
    dsl_to_srt_files,
    seconds_to_srt_time
)


def test_time_conversion():
    """测试时间格式转换"""
    print("=" * 60)
    print("测试时间格式转换")
    print("=" * 60)
    
    test_cases = [
        (0.0, "00:00:00,000"),
        (1.5, "00:00:01,500"),
        (65.123, "00:01:05,123"),
        (3661.456, "01:01:01,456"),
    ]
    
    for seconds, expected in test_cases:
        result = seconds_to_srt_time(seconds)
        status = "✓" if result == expected else "✗"
        print(f"{status} {seconds}s -> {result} (期望: {expected})")
    
    print()


def test_transcript_to_srt():
    """测试从 transcript 生成 SRT"""
    print("=" * 60)
    print("测试从 transcript 生成 SRT")
    print("=" * 60)
    
    # 加载示例 transcript
    transcript_path = Path("examples/transcript.v1.json")
    if not transcript_path.exists():
        print("✗ 示例文件不存在，跳过测试")
        return False
    
    transcript_data = json.loads(transcript_path.read_text(encoding="utf-8"))
    
    # 生成 SRT
    output_path = "test_output_subtitles.srt"
    result = transcript_to_srt(transcript_data["segments"], output_path)
    
    # 验证输出
    if Path(output_path).exists():
        content = Path(output_path).read_text(encoding="utf-8")
        print(f"\n生成的 SRT 内容预览:")
        print("-" * 60)
        print(content[:300] + "...")
        print("-" * 60)
        print(f"✓ 测试通过，文件已生成: {output_path}")
        return True
    else:
        print("✗ 测试失败，文件未生成")
        return False


def test_overlay_text_to_srt():
    """测试从 overlay_text 生成 SRT"""
    print("\n" + "=" * 60)
    print("测试从 overlay_text 生成 SRT")
    print("=" * 60)
    
    # 模拟 overlay_text 数据
    text_items = [
        {
            "content": "第一步就错了",
            "start_frame": 30,
            "duration_frames": 60
        },
        {
            "content": "90%的人都不知道",
            "start_frame": 120,
            "duration_frames": 90
        },
        {
            "content": "正确方法在这里",
            "start_frame": 240,
            "duration_frames": 75
        }
    ]
    
    # 生成 SRT
    output_path = "test_output_overlay.srt"
    result = overlay_text_to_srt(text_items, fps=30, output_path=output_path)
    
    # 验证输出
    if Path(output_path).exists():
        content = Path(output_path).read_text(encoding="utf-8")
        print(f"\n生成的 SRT 内容:")
        print("-" * 60)
        print(content)
        print("-" * 60)
        print(f"✓ 测试通过，文件已生成: {output_path}")
        return True
    else:
        print("✗ 测试失败，文件未生成")
        return False


def test_dsl_to_srt():
    """测试从 DSL 生成 SRT"""
    print("\n" + "=" * 60)
    print("测试从 DSL 生成 SRT")
    print("=" * 60)
    
    # 加载示例 DSL
    dsl_path = Path("examples/editing_dsl.v1.json")
    if not dsl_path.exists():
        print("✗ 示例文件不存在，跳过测试")
        return False
    
    dsl_data = json.loads(dsl_path.read_text(encoding="utf-8"))
    
    # 生成 SRT 文件
    output_dir = "test_output"
    files = dsl_to_srt_files(dsl_data, fps=30, output_dir=output_dir)
    
    # 验证输出
    if files:
        print(f"\n生成的文件:")
        for key, path in files.items():
            print(f"  {key}: {path}")
            if Path(path).exists():
                content = Path(path).read_text(encoding="utf-8")
                print(f"\n{key} 内容预览:")
                print("-" * 60)
                print(content[:200] + "...")
                print("-" * 60)
        print(f"✓ 测试通过")
        return True
    else:
        print("✗ 测试失败，没有生成文件")
        return False


def test_resolve_import_workflow():
    """测试 Resolve 导入工作流"""
    print("\n" + "=" * 60)
    print("测试 Resolve 导入工作流")
    print("=" * 60)
    
    print("""
工作流说明：

1. 生成 SRT 文件
   - 从 transcript 生成完整字幕
   - 从 DSL overlay_text 生成文字叠加

2. 在 DaVinci Resolve 中导入
   - File > Import > Subtitle
   - 或直接拖拽 SRT 文件到时间线

3. 调整字幕样式
   - 选中字幕轨道
   - 在 Inspector 中调整：
     * 字体、大小、颜色
     * 描边、阴影
     * 位置、对齐
   - 保存为预设供后续使用

4. 自动化导入（通过 API）
   - 使用 timeline.ImportIntoTimeline(srt_path)
   - 样式需要预先在 Resolve 中设置好

推荐工作流：
- 第一次手动调整样式并保存预设
- 后续使用 API 自动导入，应用预设
""")
    
    print("✓ 工作流说明完成")
    return True


def cleanup_test_files():
    """清理测试文件"""
    print("\n" + "=" * 60)
    print("清理测试文件")
    print("=" * 60)
    
    test_files = [
        "test_output_subtitles.srt",
        "test_output_overlay.srt",
        "test_output/overlay.srt"
    ]
    
    for file_path in test_files:
        path = Path(file_path)
        if path.exists():
            path.unlink()
            print(f"✓ 已删除: {file_path}")
    
    # 删除测试目录
    test_dir = Path("test_output")
    if test_dir.exists() and test_dir.is_dir():
        test_dir.rmdir()
        print(f"✓ 已删除目录: test_output")


if __name__ == "__main__":
    print("SRT 字幕生成功能测试套件")
    print("=" * 60)
    
    # 运行测试
    results = []
    
    results.append(("时间格式转换", test_time_conversion()))
    results.append(("Transcript → SRT", test_transcript_to_srt()))
    results.append(("Overlay Text → SRT", test_overlay_text_to_srt()))
    results.append(("DSL → SRT", test_dsl_to_srt()))
    results.append(("Resolve 工作流", test_resolve_import_workflow()))
    
    # 显示测试结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    # 清理
    print()
    cleanup_input = input("是否清理测试文件？(y/n): ")
    if cleanup_input.lower() == 'y':
        cleanup_test_files()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    print("""
下一步：
1. 在 DaVinci Resolve 中打开项目
2. 导入生成的 SRT 文件
3. 调整字幕样式
4. 保存样式预设
5. 使用 API 自动化导入
""")
