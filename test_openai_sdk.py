#!/usr/bin/env python3
"""测试OpenAI SDK调用DeepSeek API"""

import os
import sys
from openai import OpenAI
from config import AI_API_URL, AI_API_KEY

def test_openai_sdk():
    """测试OpenAI SDK调用"""
    print("测试OpenAI SDK调用DeepSeek API...")
    print(f"API URL: {AI_API_URL}")
    print(f"API Key: {AI_API_KEY[:10]}...")  # 只显示前10个字符
    
    try:
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=AI_API_KEY,
            base_url=AI_API_URL,
        )
        
        print("OpenAI客户端初始化成功")
        
        # 测试简单的聊天调用
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个测试助手，请回复'测试成功'"},
                {"role": "user", "content": "请说'测试成功'"}
            ],
            max_tokens=50
        )
        
        print("API调用成功！")
        print(f"响应内容: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"API调用失败: {e}")
        return False

if __name__ == "__main__":
    success = test_openai_sdk()
    sys.exit(0 if success else 1)