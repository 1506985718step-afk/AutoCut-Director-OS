"""
生产就绪检查脚本

快速检查系统是否准备好进行生产测试
"""
import sys
import subprocess
from pathlib import Path


def check_python():
    """检查 Python 版本"""
    print("\n1️⃣  检查 Python 版本...")
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python 版本过低: {version.major}.{version.minor}")
        print("   需要 Python 3.8+")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n2️⃣  检查依赖包...")
    
    required = [
        "fastapi",
        "pydantic",
        "openai",
        "uvicorn"
    ]
    
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} 未安装")
            missing.append(package)
    
    if missing:
        print(f"\n   请运行: pip install -r requirements.txt")
        return False
    
    return True


def check_ffmpeg():
    """检查 ffmpeg"""
    print("\n3️⃣  检查 ffmpeg...")
    
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ {version_line}")
            return True
        else:
            print("   ❌ ffmpeg 执行失败")
            return False
            
    except FileNotFoundError:
        print("   ❌ ffmpeg 未安装")
        print("   安装: choco install ffmpeg")
        return False


def check_env_file():
    """检查 .env 文件"""
    print("\n4️⃣  检查 .env 配置...")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print("   ⚠️  .env 文件不存在")
        print("   建议: 复制 .env.example 并配置")
        return False
    
    # 检查关键配置（使用 utf-8 编码）
    try:
        content = env_file.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        # 如果 utf-8 失败，尝试其他编码
        try:
            content = env_file.read_text(encoding='gbk')
        except:
            content = env_file.read_text(encoding='latin-1')
    
    checks = {
        "OPENAI_API_KEY": "OpenAI API Key" in content or "sk-" in content,
    }
    
    all_ok = True
    for key, exists in checks.items():
        if exists:
            print(f"   ✅ {key} 已配置")
        else:
            print(f"   ⚠️  {key} 未配置（AI 生成功能将不可用）")
            all_ok = False
    
    return all_ok


def check_resolve_env():
    """检查 Resolve 环境变量"""
    print("\n5️⃣  检查 Resolve 环境...")
    
    import os
    
    resolve_vars = [
        "RESOLVE_SCRIPT_API",
        "RESOLVE_SCRIPT_LIB"
    ]
    
    all_ok = True
    for var in resolve_vars:
        value = os.environ.get(var)
        if value:
            print(f"   ✅ {var}")
        else:
            print(f"   ❌ {var} 未设置")
            all_ok = False
    
    if not all_ok:
        print("\n   请运行: .\\scripts\\set_resolve_env.ps1")
    
    return all_ok


def check_test_files():
    """检查测试文件"""
    print("\n6️⃣  检查测试文件...")
    
    test_files = [
        "test_iron_rules.py",
        "test_edl_parser.py",
        "test_resolve_smoke.py",
        "test_minimal_dsl.py",
        "quick_start.py"
    ]
    
    all_ok = True
    for file in test_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} 不存在")
            all_ok = False
    
    return all_ok


def check_example_files():
    """检查示例文件"""
    print("\n7️⃣  检查示例文件...")
    
    example_files = [
        "examples/scenes.v1.json",
        "examples/minimal_dsl.v1.json",
        "examples/test.edl"
    ]
    
    all_ok = True
    for file in example_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ⚠️  {file} 不存在")
            all_ok = False
    
    return all_ok


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("🎬 AutoCut Director - 生产就绪检查")
    print("=" * 70)
    
    results = {
        "Python 版本": check_python(),
        "依赖包": check_dependencies(),
        "ffmpeg": check_ffmpeg(),
        ".env 配置": check_env_file(),
        "Resolve 环境": check_resolve_env(),
        "测试文件": check_test_files(),
        "示例文件": check_example_files()
    }
    
    print("\n" + "=" * 70)
    print("📊 检查结果")
    print("=" * 70)
    
    for name, ok in results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    
    # 统计
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n通过: {passed}/{total}")
    
    # 判断是否可以进行生产测试
    critical_checks = [
        "Python 版本",
        "依赖包",
        "测试文件"
    ]
    
    critical_passed = all(results[check] for check in critical_checks)
    
    print("\n" + "=" * 70)
    
    if critical_passed:
        print("✅ 可以进行生产测试")
        print("=" * 70)
        
        print("\n建议的测试顺序:")
        print("  1. python test_iron_rules.py")
        print("  2. python test_edl_parser.py")
        print("  3. python test_resolve_smoke.py  # 需要 Resolve")
        print("  4. python test_minimal_dsl.py    # 需要 Resolve")
        print("  5. python quick_start.py         # 完整流程")
        
        if not results["ffmpeg"]:
            print("\n⚠️  注意: ffmpeg 未安装，音频提取功能将不可用")
        
        if not results[".env 配置"]:
            print("⚠️  注意: .env 未配置，AI 生成功能将不可用")
        
        if not results["Resolve 环境"]:
            print("⚠️  注意: Resolve 环境未配置，需要运行:")
            print("   .\\scripts\\set_resolve_env.ps1")
        
        return True
    else:
        print("❌ 尚未准备好进行生产测试")
        print("=" * 70)
        
        print("\n请先解决以下问题:")
        for check in critical_checks:
            if not results[check]:
                print(f"  ❌ {check}")
        
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
