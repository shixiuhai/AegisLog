import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any
from config import DB_PATH

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 创建攻击记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attack_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source_ip TEXT NOT NULL,
                    attack_type TEXT NOT NULL,
                    log_content TEXT,
                    severity INTEGER DEFAULT 1,
                    is_blocked BOOLEAN DEFAULT FALSE,
                    block_timestamp DATETIME,
                    analyzed_by TEXT DEFAULT 'AI'
                )
            ''')
            
            # 创建封禁IP表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS blocked_ips (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ip_address TEXT UNIQUE NOT NULL,
                    first_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_detected DATETIME DEFAULT CURRENT_TIMESTAMP,
                    attack_count INTEGER DEFAULT 1,
                    attack_types TEXT,  -- JSON数组存储攻击类型
                    is_active BOOLEAN DEFAULT TRUE,
                    block_reason TEXT
                )
            ''')
            
            # 创建攻击类型统计表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attack_statistics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    attack_type TEXT NOT NULL,
                    count INTEGER DEFAULT 0,
                    UNIQUE(date, attack_type)
                )
            ''')
            
            # 创建系统状态表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    total_attacks INTEGER DEFAULT 0,
                    blocked_ips_count INTEGER DEFAULT 0,
                    active_attacks INTEGER DEFAULT 0,
                    memory_usage REAL,
                    cpu_usage REAL
                )
            ''')
            
            conn.commit()
    
    def add_attack_record(self, source_ip: str, attack_type: str, log_content: str, 
                         severity: int = 1, is_blocked: bool = False) -> int:
        """添加攻击记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO attack_records 
                (source_ip, attack_type, log_content, severity, is_blocked, block_timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (source_ip, attack_type, log_content, severity, is_blocked, 
                  datetime.now() if is_blocked else None))
            
            record_id = cursor.lastrowid
            
            # 更新攻击类型统计
            self._update_attack_statistics(attack_type)
            
            # 更新封禁IP信息
            if is_blocked:
                self._update_blocked_ip(source_ip, attack_type)
            
            conn.commit()
            return record_id
    
    def _update_attack_statistics(self, attack_type: str):
        """更新攻击类型统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            today = datetime.now().date().isoformat()
            
            cursor.execute('''
                INSERT INTO attack_statistics (date, attack_type, count)
                VALUES (?, ?, 1)
                ON CONFLICT(date, attack_type) 
                DO UPDATE SET count = count + 1
            ''', (today, attack_type))
    
    def _update_blocked_ip(self, ip_address: str, attack_type: str):
        """更新封禁IP信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查IP是否已存在
            cursor.execute('SELECT * FROM blocked_ips WHERE ip_address = ?', (ip_address,))
            existing = cursor.fetchone()
            
            if existing:
                # 更新现有记录
                attack_types = json.loads(existing[5] or '[]')
                if attack_type not in attack_types:
                    attack_types.append(attack_type)
                
                cursor.execute('''
                    UPDATE blocked_ips 
                    SET last_detected = ?, attack_count = attack_count + 1, 
                        attack_types = ?, is_active = TRUE
                    WHERE ip_address = ?
                ''', (datetime.now(), json.dumps(attack_types), ip_address))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO blocked_ips 
                    (ip_address, attack_types, block_reason)
                    VALUES (?, ?, ?)
                ''', (ip_address, json.dumps([attack_type]), f'Detected {attack_type} attack'))
    
    def get_attack_statistics(self, days: int = 7) -> Dict:
        """获取攻击统计数据"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 获取总体统计
            cursor.execute('SELECT COUNT(*) FROM attack_records')
            total_attacks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE is_active = TRUE')
            active_blocks = cursor.fetchone()[0]
            
            # 获取最近N天的攻击类型分布
            cursor.execute('''
                SELECT attack_type, SUM(count) as total
                FROM attack_statistics 
                WHERE date >= date('now', ?)
                GROUP BY attack_type
                ORDER BY total DESC
            ''', (f'-{days} days',))
            
            attack_type_distribution = {row[0]: row[1] for row in cursor.fetchall()}
            
            # 获取最近攻击记录
            cursor.execute('''
                SELECT timestamp, source_ip, attack_type, severity
                FROM attack_records 
                ORDER BY timestamp DESC 
                LIMIT 10
            ''')
            
            recent_attacks = [
                {
                    'timestamp': row[0],
                    'source_ip': row[1],
                    'attack_type': row[2],
                    'severity': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'total_attacks': total_attacks,
                'active_blocks': active_blocks,
                'attack_type_distribution': attack_type_distribution,
                'recent_attacks': recent_attacks
            }
    
    def get_attack_type_summary(self) -> Dict:
        """获取攻击类型分组统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 按攻击类型分组统计
            cursor.execute('''
                SELECT attack_type, COUNT(*) as count, 
                       AVG(severity) as avg_severity,
                       MAX(timestamp) as last_occurrence
                FROM attack_records 
                GROUP BY attack_type 
                ORDER BY count DESC
            ''')
            
            result = {}
            for row in cursor.fetchall():
                result[row[0]] = {
                    'count': row[1],
                    'avg_severity': round(row[2], 2) if row[2] else 0,
                    'last_occurrence': row[3]
                }
            
            return result
    
    def update_system_status(self, memory_usage: float = None, cpu_usage: float = None):
        """更新系统状态"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM attack_records')
            total_attacks = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE is_active = TRUE')
            blocked_ips_count = cursor.fetchone()[0]
            
            # 获取最近1小时内的攻击次数
            cursor.execute('''
                SELECT COUNT(*) FROM attack_records 
                WHERE timestamp >= datetime('now', '-1 hour')
            ''')
            active_attacks = cursor.fetchone()[0]
            
            cursor.execute('''
                INSERT INTO system_status 
                (total_attacks, blocked_ips_count, active_attacks, memory_usage, cpu_usage)
                VALUES (?, ?, ?, ?, ?)
            ''', (total_attacks, blocked_ips_count, active_attacks, memory_usage, cpu_usage))
            
            conn.commit()
    
    def get_attack_type_statistics(self) -> Dict[str, int]:
        """获取攻击类型统计"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT attack_type, COUNT(*) as count
                FROM attack_records
                GROUP BY attack_type
                ORDER BY count DESC
            ''')
            
            return {row[0]: row[1] for row in cursor.fetchall()}
    
    def get_recent_attacks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取最近攻击记录"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, source_ip, attack_type, severity, log_content, is_blocked
                FROM attack_records
                ORDER BY timestamp DESC
                LIMIT ?
            ''', (limit,))
            
            return [
                {
                    'timestamp': row[0],
                    'source_ip': row[1],
                    'attack_type': row[2],
                    'severity': row[3],
                    'log_content': row[4],
                    'is_blocked': bool(row[5])
                }
                for row in cursor.fetchall()
            ]
    
    def get_blocked_ips(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取被拦截IP列表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT ip_address, first_detected, last_detected,
                       attack_count, attack_types, block_reason
                FROM blocked_ips
                WHERE is_active = TRUE
                ORDER BY last_detected DESC
                LIMIT ?
            ''', (limit,))
            
            return [
                {
                    'ip_address': row[0],
                    'first_detected': row[1],
                    'last_detected': row[2],
                    'attack_count': row[3],
                    'attack_types': json.loads(row[4]) if row[4] else [],
                    'block_reason': row[5]
                }
                for row in cursor.fetchall()
            ]
    
    def get_total_attacks(self) -> int:
        """获取总攻击次数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM attack_records')
            return cursor.fetchone()[0]
    
    def get_today_attacks(self) -> int:
        """获取今日攻击次数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT COUNT(*) FROM attack_records
                WHERE date(timestamp) = date('now')
            ''')
            return cursor.fetchone()[0]
    
    def get_total_blocked_ips(self) -> int:
        """获取总被拦截IP数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM blocked_ips WHERE is_active = TRUE')
            return cursor.fetchone()[0]

# 单例模式
db_manager = DatabaseManager()