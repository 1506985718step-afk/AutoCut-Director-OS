"""
测试 DaVinci Resolve 项目创建和素材导入
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.tools.resolve_importer import get_importer


def test_resolve_connection():
    """测试 Resolve 连接"""
    print("\n" + "=" * 60)
    print("测试 1: 连接到 DaVinci Resolve")
    print("=" * 60)
    
    importer = get_importer()
    
    # 尝试连接
    connected = importer.connect()
    
    if connected:
        print("✅ 成功连接到 DaVinci Resolve")
        
        # 获取项目信息
        status = importer.check_resolve_status()
        print(f"\n项目信息:")
        print(f"  - 项目名称: {status['project_name']}")
        print(f"  - Media Pool 素材数: {status['media_pool_items']}")
        print(f"  - 状态: {status['message']}")
        
        return True
    else:
        print("❌ 连接失败")
        print("\n请检查:")
        print("  1. DaVinci Resolve 是否已启动")
        print("  2. 环境变量 RESOLVE_SCRIPT_API 是否设置正确")
        print("  3. 是否有打开的项目（如果没有，系统会自动创建）")
        
        return False


def test_import_media():
    """测试导入素材"""
    print("\n" + "=" * 60)
    print("测试 2: 导入测试素材")
    print("=" * 60)
    
    importer = get_importer()
    
    if not importer.connected:
        print("⚠️ 未连接到 Resolve，跳过测试")
        return False
    
    # 查找测试视频
    test_videos = []
    
    # 检查常见位置
    possible_paths = [
        Path("test_video.mp4"),
        Path("examples/test.mp4"),
        Path.home() / "Videos" / "test.mp4",
    ]
    
    for path in possible_paths:
        if path.exists():
            test_videos.append(str(path))
            break
    
    if not test_videos:
        print("⚠️ 没有找到测试视频文件")
        print("\n提示：创建一个 test_video.mp4 文件来测试导入功能")
        return False
    
    print(f"找到测试视频: {test_videos[0]}")
    
    # 导入素材
    result = importer.import_media(test_videos)
    
    if result["success"]:
        print(f"✅ 成功导入 {len(result['imported'])} 个文件")
        
        for item in result["imported"]:
            print(f"  - {Path(item['path']).name}")
        
        if result["failed"]:
            print(f"\n⚠️ {len(result['failed'])} 个文件导入失败:")
            for item in result["failed"]:
                print(f"  - {Path(item['path']).name}: {item['error']}")
        
        return True
    else:
        print(f"❌ 导入失败: {result['message']}")
        return False


def test_create_bin():
    """测试创建 bin"""
    print("\n" + "=" * 60)
    print("测试 3: 创建 Bin（文件夹）")
    print("=" * 60)
    
    importer = get_importer()
    
    if not importer.connected:
        print("⚠️ 未连接到 Resolve，跳过测试")
        return False
    
    # 创建测试 bin
    bin_name = "AutoCut_Test"
    bin_folder = importer.create_bin(bin_name)
    
    if bin_folder:
        print(f"✅ 成功创建 bin: {bin_name}")
        return True
    else:
        print(f"❌ 创建 bin 失败")
        return False


def test_import_from_manifest():
    """测试从清单导入"""
    print("\n" + "=" * 60)
    print("测试 4: 从素材清单导入")
    print("=" * 60)
    
    importer = get_importer()
    
    if not importer.connected:
        print("⚠️ 未连接到 Resolve，跳过测试")
        return False
    
    # 检查示例清单
    manifest_path = Path("examples/assets_manifest.json")
    
    if not manifest_path.exists():
        print("⚠️ 示例清单文件不存在，跳过测试")
        return False
    
    print(f"使用清单: {manifest_path}")
    
    # 从清单导入
    result = importer.import_from_manifest(str(manifest_path))
    
    if result["success"]:
        print(f"✅ 成功导入 {len(result['imported'])} 个素材")
        
        if "asset_mapping" in result:
            print("\nAsset ID 映射:")
            for asset_id, media_item in result["asset_mapping"].items():
                print(f"  - {asset_id}: {media_item}")
        
        return True
    else:
        print(f"❌ 导入失败: {result['message']}")
        
        if result["failed"]:
            print("\n失败的文件:")
            for item in result["failed"]:
                print(f"  - {item.get('path', 'unknown')}: {item.get('error', 'unknown')}")
        
        return False


def main():
    """主测试流程"""
    print("\n" + "=" * 60)
    print("DaVinci Resolve 项目创建和素材导入测试")
    print("=" * 60)
    
    results = {
        "连接测试": False,
        "导入素材": False,
        "创建 Bin": False,
        "清单导入": False
    }
    
    # 测试 1: 连接
    results["连接测试"] = test_resolve_connection()
    
    if results["连接测试"]:
        # 测试 2: 导入素材
        results["导入素材"] = test_import_media()
        
        # 测试 3: 创建 bin
        results["创建 Bin"] = test_create_bin()
        
        # 测试 4: 从清单导入
        results["清单导入"] = test_import_from_manifest()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
    elif passed > 0:
        print("\n⚠️ 部分测试通过")
    else:
        print("\n❌ 所有测试失败")
        print("\n故障排除:")
        print("1. 确保 DaVinci Resolve 已启动")
        print("2. 运行环境变量设置脚本:")
        print("   PowerShell: .\\scripts\\set_resolve_env.ps1")
        print("3. 在 Resolve 中手动创建一个项目")
        print("4. 检查 Resolve 设置 -> 系统 -> 常规 -> 外部脚本使用")


if __name__ == "__main__":
    main()
