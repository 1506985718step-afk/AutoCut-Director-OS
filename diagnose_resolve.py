"""
DaVinci Resolve 连接诊断工具
快速检查 Resolve 连接状态和项目创建问题
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

print("\n" + "=" * 70)
print("DaVinci Resolve 连接诊断工具")
print("=" * 70)

# 步骤 1: 检查环境变量
print("\n[1/5] 检查环境变量...")
import os

env_vars = {
    "RESOLVE_SCRIPT_API": os.environ.get("RESOLVE_SCRIPT_API"),
    "RESOLVE_SCRIPT_LIB": os.environ.get("RESOLVE_SCRIPT_LIB"),
    "PYTHONPATH": os.environ.get("PYTHONPATH"),
    "RESOLVE_SCRIPT_DIR": os.environ.get("RESOLVE_SCRIPT_DIR")
}

all_set = True
for key, value in env_vars.items():
    if value:
        print(f"  ✓ {key}: {value[:50]}...")
    else:
        print(f"  ✗ {key}: 未设置")
        all_set = False

if not all_set:
    print("\n  ⚠️ 环境变量未完全设置")
    print("  请运行: .\\scripts\\set_resolve_env.ps1")
else:
    print("  ✓ 环境变量已设置")

# 步骤 2: 尝试导入 Resolve 模块
print("\n[2/5] 检查 Resolve 模块...")
try:
    import DaVinciResolveScript as dvr_script
    print("  ✓ DaVinciResolveScript 模块导入成功")
except ImportError as e:
    print(f"  ✗ 无法导入 DaVinciResolveScript: {e}")
    print("\n  故障排除:")
    print("  1. 确保 DaVinci Resolve 已安装")
    print("  2. 运行环境变量设置脚本")
    print("  3. 重启终端")
    sys.exit(1)

# 步骤 3: 尝试连接 Resolve
print("\n[3/5] 连接到 DaVinci Resolve...")
try:
    resolve = dvr_script.scriptapp("Resolve")
    if resolve:
        print("  ✓ 成功连接到 DaVinci Resolve")
    else:
        print("  ✗ 连接失败（Resolve 返回 None）")
        print("\n  故障排除:")
        print("  1. 确保 DaVinci Resolve 已启动")
        print("  2. 检查 Resolve 设置 -> 系统 -> 常规 -> 外部脚本使用")
        print("     - 确保 '网络' 和 '本地' 都已启用")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ 连接异常: {e}")
    sys.exit(1)

# 步骤 4: 检查项目管理器
print("\n[4/5] 检查项目管理器...")
try:
    pm = resolve.GetProjectManager()
    if pm:
        print("  ✓ 项目管理器可用")
        
        # 获取当前数据库
        current_db = pm.GetCurrentDatabase()
        print(f"  - 当前数据库: {current_db}")
        
        # 获取项目列表
        projects = pm.GetProjectListInCurrentFolder()
        if projects:
            print(f"  - 数据库中有 {len(projects)} 个项目:")
            for i, proj_name in enumerate(projects[:5], 1):
                print(f"    {i}. {proj_name}")
            if len(projects) > 5:
                print(f"    ... 还有 {len(projects) - 5} 个项目")
        else:
            print("  - 数据库中没有项目")
    else:
        print("  ✗ 无法获取项目管理器")
        sys.exit(1)
except Exception as e:
    print(f"  ✗ 项目管理器异常: {e}")
    sys.exit(1)

# 步骤 5: 检查当前项目
print("\n[5/5] 检查当前项目...")
try:
    current_project = pm.GetCurrentProject()
    
    if current_project:
        project_name = current_project.GetName()
        print(f"  ✓ 当前有打开的项目: {project_name}")
        
        # 检查 Media Pool
        media_pool = current_project.GetMediaPool()
        if media_pool:
            root_folder = media_pool.GetRootFolder()
            clips = root_folder.GetClipList()
            clip_count = len(clips) if clips else 0
            print(f"  - Media Pool 中有 {clip_count} 个素材")
        
        print("\n" + "=" * 70)
        print("✅ 诊断完成 - 一切正常！")
        print("=" * 70)
        print("\n您可以直接使用 AutoCut Director 了")
        
    else:
        print("  ⚠️ 当前没有打开的项目")
        print("\n  这是最常见的问题！")
        print("\n  解决方案（选择一个）:")
        print("\n  方案 A: 手动创建项目（推荐）")
        print("    1. 在 DaVinci Resolve 项目管理器中")
        print("    2. 点击 '新建项目'")
        print("    3. 输入项目名称（例如：AutoCut_Main）")
        print("    4. 双击项目打开（重要！）")
        print("    5. 确保看到编辑界面，不是项目管理器")
        print("\n  方案 B: 自动创建项目")
        print("    运行: python autocut-director/test_resolve_project_creation.py")
        
        # 尝试自动创建
        print("\n  是否尝试自动创建项目？(y/n): ", end="")
        try:
            response = input().strip().lower()
            if response == 'y':
                print("\n  正在创建项目...")
                from datetime import datetime
                project_name = f"AutoCut_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                new_project = pm.CreateProject(project_name)
                
                if new_project:
                    print(f"  ✓ 成功创建项目: {project_name}")
                    print("\n  ⚠️ 重要：请在 Resolve 中双击打开这个项目！")
                    print("  然后重新运行此诊断工具验证")
                else:
                    print("  ✗ 创建失败")
                    print("  请手动在 Resolve 中创建项目")
        except:
            pass
        
        print("\n" + "=" * 70)
        print("⚠️ 诊断完成 - 需要创建/打开项目")
        print("=" * 70)

except Exception as e:
    print(f"  ✗ 检查项目异常: {e}")
    sys.exit(1)
