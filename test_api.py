#!/usr/bin/env python3
"""
API 连接测试脚本
用于诊断 OpenAI API 配置问题
"""

import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

print("=" * 60)
print("OpenAI API 配置检查")
print("=" * 60)

# 检查 API Key
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    # 隐藏大部分密钥，只显示前后几位
    masked_key = api_key[:7] + "*" * (len(api_key) - 14) + api_key[-7:]
    print(f"✓ API Key 已设置: {masked_key}")
    print(f"  长度: {len(api_key)} 字符")
else:
    print("❌ API Key 未设置")

# 检查 API Base
api_base = os.getenv("OPENAI_API_BASE")
if api_base:
    print(f"✓ API Base 已设置: {api_base}")
else:
    print("  API Base 未设置（使用默认 OpenAI 端点）")

print("\n" + "=" * 60)
print("测试 API 连接")
print("=" * 60)

if api_key:
    try:
        from openai import OpenAI

        # 创建客户端
        client_kwargs = {"api_key": api_key}
        if api_base:
            client_kwargs["base_url"] = api_base

        client = OpenAI(**client_kwargs)

        print("\n正在测试 API 连接...")

        # 发送测试请求
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello"}
            ],
            max_tokens=10
        )

        print("✓ API 连接成功！")
        print(f"  响应内容: {response.choices[0].message.content}")

    except Exception as e:
        print(f"❌ API 连接失败: {e}")
        print("\n可能的原因：")
        print("  1. API Key 不正确")
        print("  2. API Base URL 格式错误")
        print("  3. 网络连接问题")
        print("  4. API 服务不可用")
else:
    print("❌ 无法测试：API Key 未设置")

print("\n" + "=" * 60)
