#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
AegisLog Web Dashboard - 态势感知大屏界面
提供实时攻击统计、最近攻击记录、被拦截IP列表和系统状态监控
"""

from flask import Flask, render_template, jsonify
import sqlite3
import json
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Any

from config import DB_PATH, ATTACK_TYPES, CHECK_INTERVAL, ATTACK_TYPE_MAPPING
from models import DatabaseManager
from logger import AegisLogger

# 初始化日志记录器
logger = AegisLogger()

app = Flask(__name__)

# 全局缓存变量，减少数据库查询频率
cached_stats = {
    'attack_types': {},
    'recent_attacks': [],
    'blocked_ips': [],
    'system_status': {},
    'last_update': None
}

def get_attack_type_stats() -> Dict[str, int]:
    """获取攻击类型统计"""
    try:
        db_manager = DatabaseManager()
        return db_manager.get_attack_type_statistics()
    except Exception as e:
        logger.error(f"获取攻击类型统计失败: {e}")
        return {}

def get_recent_attacks(limit: int = 20) -> List[Dict[str, Any]]:
    """获取最近攻击记录"""
    try:
        db_manager = DatabaseManager()
        return db_manager.get_recent_attacks(limit)
    except Exception as e:
        logger.error(f"获取最近攻击记录失败: {e}")
        return []

def get_blocked_ips(limit: int = 50) -> List[Dict[str, Any]]:
    """获取被拦截IP列表"""
    try:
        db_manager = DatabaseManager()
        return db_manager.get_blocked_ips(limit)
    except Exception as e:
        logger.error(f"获取被拦截IP列表失败: {e}")
        return []

def get_system_status() -> Dict[str, Any]:
    """获取系统状态信息"""
    try:
        db_manager = DatabaseManager()
        total_attacks = db_manager.get_total_attacks()
        today_attacks = db_manager.get_today_attacks()
        blocked_count = db_manager.get_total_blocked_ips()
        
        return {
            'total_attacks': total_attacks,
            'today_attacks': today_attacks,
            'blocked_count': blocked_count,
            'uptime': get_uptime(),
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {e}")
        return {}

def get_uptime() -> str:
    """获取系统运行时间（模拟）"""
    # 这里可以扩展为实际的系统运行时间监控
    return "24小时"

def update_cache():
    """更新缓存数据"""
    global cached_stats
    try:
        cached_stats = {
            'attack_types': get_attack_type_stats(),
            'recent_attacks': get_recent_attacks(),
            'blocked_ips': get_blocked_ips(),
            'system_status': get_system_status(),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        logger.info("缓存数据更新成功")
    except Exception as e:
        logger.error(f"更新缓存失败: {e}")

def cache_updater():
    """缓存更新线程"""
    while True:
        update_cache()
        time.sleep(CHECK_INTERVAL)  # 使用配置中的检查间隔

@app.route('/')
def dashboard():
    """主仪表板页面"""
    return render_template('dashboard.html', 
                         attack_types=ATTACK_TYPES,
                         last_update=cached_stats['last_update'])

@app.route('/api/stats')
def get_stats():
    """获取统计数据的API接口"""
    return jsonify(cached_stats)

@app.route('/api/attack-types')
def get_attack_types_data():
    """获取攻击类型数据的API接口"""
    try:
        db_manager = DatabaseManager()
        stats = db_manager.get_attack_type_statistics()
        
        # 格式化数据用于图表显示 - 使用映射表转换数据库中的英文类型到中文显示
        chart_data = []
        total_count = sum(stats.values())
        
        # 首先处理映射表中定义的类型
        for db_type, display_name in ATTACK_TYPE_MAPPING.items():
            count = stats.get(db_type, 0)
            chart_data.append({
                'name': display_name,
                'value': count,
                'percentage': calculate_percentage(count, total_count) if total_count > 0 else 0
            })
        
        # 处理其他未映射的类型（如果有）
        for db_type, count in stats.items():
            if db_type not in ATTACK_TYPE_MAPPING:
                chart_data.append({
                    'name': db_type,  # 直接使用数据库中的名称
                    'value': count,
                    'percentage': calculate_percentage(count, total_count) if total_count > 0 else 0
                })
        
        return jsonify({
            'data': chart_data,
            'total': sum(stats.values())
        })
    except Exception as e:
        logger.error(f"获取攻击类型数据失败: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/recent-attacks')
def get_recent_attacks_api():
    """获取最近攻击记录的API接口"""
    try:
        db_manager = DatabaseManager()
        attacks = db_manager.get_recent_attacks(50)
        return jsonify(attacks)
    except Exception as e:
        logger.error(f"获取最近攻击记录失败: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_percentage(part: int, total: int) -> float:
    """计算百分比"""
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)

# 启动时初始化缓存
def initialize():
    """应用启动初始化"""
    logger.info("AegisLog Web Dashboard 启动中...")
    update_cache()
    
    # 启动缓存更新线程
    thread = threading.Thread(target=cache_updater, daemon=True)
    thread.start()
    logger.info("缓存更新线程已启动")

# 在应用启动时立即初始化
initialize()

if __name__ == '__main__':
    logger.info("启动 Flask 开发服务器...")
    app.run(host='0.0.0.0', port=5000, debug=True)