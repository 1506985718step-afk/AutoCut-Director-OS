"""
快速测试达芬奇连接
"""
import sys
import os

# 设置环境变量
resolve_script_dir = r"C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules"
sys.path.insert(0, resolve_script_dir)

print("=" * 60)
print("达芬奇连接快速测试")
print("=" * 60)

# 1. 检查模块路径
print(f"\n[1] 检查模块路径")
print(f"  路径: {resolve_script_dir}")
print(f"  存在: {os.path.exists(resolve_script_dir)}")

# 2. 尝试导入模块
print(f"\n[2] 尝试导入 DaVinciResolveScript")
try:
    import DaVinciResolveScript as dvr
    print(f"  ✓ 模块导入成功")
except Exception as e:
    print(f"  ✗ 模块导入失败: {e}")
    print(f"\n  详细错误信息:")
    import traceback
    traceback.print_exc()
    print(f"\n  可能原因:")
    print(f"  1. 达芬奇未完全启动（请等待启动完成）")
    print(f"  2. 达芬奇版本不支持脚本 API（需要 16+ 版本）")
    print(f"  3. Python 版本不兼容（当前: {sys.version}）")
    sys.exit(1)

# 3. 尝试连接达芬奇
print(f"\n[3] 尝试连接达芬奇")
try:
    resolve = dvr.scriptapp("Resolve")
    if resolve:
        print(f"  ✓ 连接成功")
        
        # 获取版本
        try:
            version = resolve.GetVersion()
            print(f"  版本: {version}")
        except:
            print(f"  版本: 无法获取")
        
        # 获取项目管理器
        try:
            pm = resolve.GetProjectManager()
            if pm:
                print(f"  ✓ 项目管理器可用")
                
                # 获取当前项目
                current_project = pm.GetCurrentProject()
                if current_project:
                    print(f"  ✓ 当前项目: {current_project.GetName()}")
                else:
                    print(f"  ⚠️  没有打开的项目")
                    print(f"  提示: 请在达芬奇中创建或打开一个项目")
            else:
                print(f"  ✗ 项目管理器不可用")
        except Exception as e:
            print(f"  ✗ 项目管理器错误: {e}")
    else:
        print(f"  ✗ 连接失败")
        print(f"\n  可能原因:")
        print(f"  1. 达芬奇未启动")
        print(f"  2. 达芬奇版本不支持脚本 API")
        print(f"  3. 需要在达芬奇中启用外部脚本")
        sys.exit(1)
        
except Exception as e:
    print(f"  ✗ 连接失败: {e}")
    print(f"\n  可能原因:")
    print(f"  1. 达芬奇未启动")
    print(f"  2. 达芬奇版本不支持脚本 API")
    sys.exit(1)

print(f"\n" + "=" * 60)
print(f"✓ 测试完成")
print(f"=" * 60)
