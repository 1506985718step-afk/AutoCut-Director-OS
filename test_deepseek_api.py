"""
测试 DeepSeek API 连接
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from openai import OpenAI


def test_deepseek_connection():
    """测试 DeepSeek API 连接"""
    print("\n" + "=" * 70)
    print("🤖 测试 DeepSeek API 连接")
    print("=" * 70)
    
    # 显示配置
    print(f"\n配置信息:")
    print(f"  API Key: {settings.OPENAI_API_KEY[:20]}...")
    print(f"  Model: {settings.OPENAI_MODEL}")
    print(f"  Base URL: {settings.OPENAI_BASE_URL}")
    
    # 创建客户端
    print(f"\n创建 OpenAI 客户端...")
    try:
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL
        )
        print("✅ 客户端创建成功")
    except Exception as e:
        print(f"❌ 客户端创建失败: {e}")
        return False
    
    # 测试简单对话
    print(f"\n测试简单对话...")
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个有帮助的助手。"},
                {"role": "user", "content": "请用一句话介绍你自己。"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        answer = response.choices[0].message.content
        print(f"✅ API 调用成功")
        print(f"\n回复内容:")
        print(f"  {answer}")
        
    except Exception as e:
        print(f"❌ API 调用失败: {e}")
        return False
    
    # 测试 JSON 模式
    print(f"\n测试 JSON 模式...")
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "你是一个 JSON 生成器。"},
                {"role": "user", "content": '生成一个简单的 JSON 对象，包含 name 和 age 字段。'}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
            max_tokens=100
        )
        
        json_result = response.choices[0].message.content
        print(f"✅ JSON 模式调用成功")
        print(f"\nJSON 结果:")
        print(f"  {json_result}")
        
        # 验证是否是有效的 JSON
        import json
        json.loads(json_result)
        print(f"✅ JSON 格式验证通过")
        
    except Exception as e:
        print(f"❌ JSON 模式调用失败: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("✅ DeepSeek API 测试完成")
    print("=" * 70)
    
    return True


if __name__ == "__main__":
    print("\n🎬 AutoCut Director - DeepSeek API 测试")
    
    success = test_deepseek_connection()
    
    if success:
        print("\n✅ 所有测试通过，可以使用 DeepSeek API")
        print("\n下一步:")
        print("  1. 测试 LLM Director: python test_llm_director.py")
        print("  2. 启动 API 服务: python run_server.py")
    else:
        print("\n❌ 测试失败，请检查配置")
        sys.exit(1)
