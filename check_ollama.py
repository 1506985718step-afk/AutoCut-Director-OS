"""
检查 Ollama 安装和配置

快速诊断工具
"""
import requests
import subprocess
import sys
from pathlib import Path

def check_ollama_process():
    """检查 Ollama 进程"""
    print("\n[1/5] 检查 Ollama 进程...")
    try:
        import psutil
        for proc in psutil.process_iter(['name', 'exe']):
            if 'ollama' in proc.info['name'].lower():
                print(f"  ✓ 找到进程: {proc.info['name']}")
                print(f"    路径: {proc.info['exe']}")
                return True
        print("  ✗ 未找到 Ollama 进程")
        return False
    except ImportError:
        print("  ⚠️  psutil 未安装，跳过进程检查")
        return None

def check_ollama_api():
    """检查 Ollama API"""
    print("\n[2/5] 检查 Ollama API...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("  ✓ Ollama API 正常")
            return True
        else:
            print(f"  ✗ API 返回错误: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("  ✗ 无法连接到 Ollama API (http://localhost:11434)")
        print("    可能原因:")
        print("    1. Ollama 服务未启动")
        print("    2. 端口被占用")
        print("    3. 防火墙阻止")
        return False
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return False

def check_ollama_models():
    """检查已安装的模型"""
    print("\n[3/5] 检查已安装的模型...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            
            if models:
                print(f"  ✓ 找到 {len(models)} 个模型:")
                for model in models:
                    name = model.get("name", "")
                    size = model.get("size", 0) / (1024**3)
                    print(f"    - {name} ({size:.1f} GB)")
                
                # 检查推荐模型
                has_moondream = any("moondream" in m.get("name", "") for m in models)
                has_llava = any("llava-phi3" in m.get("name", "") for m in models)
                
                return {
                    "moondream": has_moondream,
                    "llava-phi3": has_llava,
                    "count": len(models)
                }
            else:
                print("  ⚠️  未安装任何模型")
                return {"moondream": False, "llava-phi3": False, "count": 0}
        else:
            print(f"  ✗ 获取模型列表失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"  ✗ 检查失败: {e}")
        return None

def check_env_config():
    """检查 .env 配置"""
    print("\n[4/5] 检查 .env 配置...")
    env_file = Path(".env")
    
    if not env_file.exists():
        print("  ⚠️  .env 文件不存在")
        print("    建议: 复制 .env.example 为 .env")
        return False
    
    content = env_file.read_text(encoding='utf-8')
    
    has_use_local = "USE_LOCAL_VISION" in content
    has_model = "LOCAL_VISION_MODEL" in content
    has_host = "OLLAMA_HOST" in content
    
    if has_use_local and has_model and has_host:
        print("  ✓ .env 配置完整")
        
        # 显示当前配置
        for line in content.split('\n'):
            if 'USE_LOCAL_VISION' in line or 'LOCAL_VISION_MODEL' in line or 'OLLAMA_HOST' in line:
                print(f"    {line.strip()}")
        
        return True
    else:
        print("  ⚠️  .env 配置不完整")
        if not has_use_local:
            print("    缺少: USE_LOCAL_VISION")
        if not has_model:
            print("    缺少: LOCAL_VISION_MODEL")
        if not has_host:
            print("    缺少: OLLAMA_HOST")
        return False

def provide_solutions(results):
    """提供解决方案"""
    print("\n[5/5] 诊断结果和建议")
    print("=" * 70)
    
    if not results['api']:
        print("\n❌ Ollama API 未响应")
        print("\n解决方案:")
        print("  1. 重启 Ollama:")
        print("     - 关闭 Ollama 应用")
        print("     - 从开始菜单重新启动 Ollama")
        print("     - 等待 5-10 秒")
        print("\n  2. 或者在命令行启动服务:")
        print('     ollama serve')
        print("\n  3. 检查端口占用:")
        print('     netstat -ano | findstr :11434')
        return
    
    if results['models'] and results['models']['count'] == 0:
        print("\n⚠️  未安装任何模型")
        print("\n解决方案:")
        print("  下载推荐模型:")
        print("    ollama pull moondream")
        print("\n  或下载备选模型:")
        print("    ollama pull llava-phi3")
        return
    
    if results['models']:
        if not results['models']['moondream'] and not results['models']['llava-phi3']:
            print("\n⚠️  未安装推荐的视觉模型")
            print("\n解决方案:")
            print("  下载 Moondream (推荐):")
            print("    ollama pull moondream")
            print("\n  或下载 LLaVA-Phi3:")
            print("    ollama pull llava-phi3")
            return
    
    if not results['env']:
        print("\n⚠️  .env 配置不完整")
        print("\n解决方案:")
        print("  1. 如果 .env 不存在:")
        print("     copy .env.example .env")
        print("\n  2. 添加以下配置到 .env:")
        print("     USE_LOCAL_VISION=True")
        print("     LOCAL_VISION_MODEL=moondream")
        print("     OLLAMA_HOST=http://localhost:11434")
        return
    
    print("\n✅ 所有检查通过！")
    print("\n下一步:")
    print("  1. 运行测试: python test_ollama_vision.py")
    print("  2. 启动服务: python run_server.py")
    print("  3. 开始使用本地视觉分析！")

def main():
    print("=" * 70)
    print("Ollama 安装和配置检查")
    print("=" * 70)
    
    results = {
        'process': check_ollama_process(),
        'api': check_ollama_api(),
        'models': check_ollama_models(),
        'env': check_env_config()
    }
    
    provide_solutions(results)
    
    print("\n" + "=" * 70)
    print("检查完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
