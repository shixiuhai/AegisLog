#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试优化后的 AI 分析功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aegis_log import analyze_lines_ai
from config import AI_API_KEY, AI_API_URL

def test_optimized_ai():
    """测试优化后的 AI 分析功能"""
    
    # 检查 API 配置
    if not AI_API_KEY or AI_API_KEY == "your_deepseek_api_key_here":
        print("❌ 请先在 config.py 中配置 DeepSeek API Key")
        return False
    
    if not AI_API_URL:
        print("❌ 请先在 config.py 中配置 DeepSeek API URL")
        return False
    
    print("✅ API 配置检查通过")
    
    # 测试日志数据
    test_logs = [
        "2024-01-01 12:00:00 [WARNING] Failed login attempt from 192.168.1.100",
        "2024-01-01 12:00:01 [ERROR] Invalid password for user admin from 192.168.1.100",
        "2024-01-01 12:00:02 [CRITICAL] Multiple failed login attempts from 192.168.1.100"
    ]
    
    print(f"📋 测试日志内容:")
    for i, log in enumerate(test_logs, 1):
        print(f"  {i}. {log}")
    
    try:
        print("\n🚀 开始调用 AI 分析...")
        result = analyze_lines_ai(test_logs)
        
        print(f"✅ AI 分析完成!")
        print(f"📊 分析结果: {result}")
        
        # 检查返回结果格式
        if isinstance(result, dict):
            print("✅ 返回格式正确 (字典格式)")
            if 'attack_ips' in result:
                print(f"🔍 检测到的攻击IP: {result['attack_ips']}")
            if 'attack_types' in result:
                print(f"🔍 检测到的攻击类型: {result['attack_types']}")
        else:
            print("⚠️  返回格式不是字典，可能需要调整")
            
        return True
        
    except Exception as e:
        print(f"❌ AI 分析失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 开始测试优化后的 AI 分析功能")
    print("=" * 50)
    
    success = test_optimized_ai()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试完成! 优化后的 AI 分析功能正常工作")
    else:
        print("💥 测试失败! 请检查配置和代码")