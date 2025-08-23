#!/usr/bin/env python3
"""
测试脚本 - 验证AegisLogger功能
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import AegisLogger

def test_logger():
    """测试日志功能"""
    print("开始测试AegisLogger...")
    
    # 创建日志目录（如果不存在）
    log_dir = os.path.dirname("/var/log/my_service.log")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
        print(f"创建日志目录: {log_dir}")
    
    # 初始化日志器
    logger = AegisLogger()
    
    # 测试所有日志级别
    print("测试所有日志级别...")
    logger.debug("这是一条DEBUG级别的日志")
    logger.info("这是一条INFO级别的日志")
    logger.warning("这是一条WARNING级别的日志")
    logger.error("这是一条ERROR级别的日志")
    logger.critical("这是一条CRITICAL级别的日志")
    
    # 测试带变量的日志
    ip_address = "192.168.1.100"
    attack_type = "SQL注入"
    logger.info(f"检测到攻击: IP={ip_address}, 类型={attack_type}")
    
    print("日志测试完成！")
    print(f"日志文件路径: /var/log/my_service.log")
    print("请检查日志文件和控制台输出是否正常")
    


if __name__ == "__main__":
    test_logger()