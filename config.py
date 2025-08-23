# 日志配置
LOG_LEVEL = "INFO"                         # 日志级别 DEBUG/INFO/WARNING/ERROR
LOG_FILE = "./my_service.log"       # 程序输出日志路径
ANALYZE_FILES = "test_log1.log,test_log2.log"  # 需要分析的日志文件(逗号分隔)
LOG_RETENTION_DAYS = 7                     # 日志保留天数
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"  # 日志格式
LOG_CONSOLE = True                         # 是否输出到终端
CHECK_INTERVAL = 60                        # 每隔多少秒检测日志
BLACKLIST_MAX = 100                        # 最大黑名单条数
BATCH_SIZE = 2                            # 每次发送给 AI 的日志行数

# 日志文件读取优化配置
USE_TAIL_COMMAND = True                    # 是否使用tail命令优化大文件读取

# AI 接口配置
AI_API_URL = "https://api.deepseek.com/v1"           # AI 判定接口
AI_API_KEY = "-1234"           # AI 接口 key
CHAIN_NAME = "BLACKLIST"                   # iptables 黑名单链名

# AI 提示词
AI_PROMPT_COMMON = """
请分析以下日志，判定是否存在网络攻击行为。常见攻击类型包括：
- DDoS
- SYN Flood
- UDP Flood
- SQL Injection
- XSS
- Brute Force
- Scanning
- Malicious Crawler
- Unknown
如果日志中存在这些攻击，请返回 JSON: {"attack_ips": [{"ip": "ip1", "attack_type": "type1"}, {"ip": "ip2", "attack_type": "type2"}, ...]}，没有攻击返回 {"attack_ips": []}。
"""

AI_PROMPT_CUSTOM = """
自定义判定规则：
- 包含关键字 "malicious" 或 "hack" 认定为攻击
- 请求路径包含 "/admin" 且频繁访问认定为攻击
"""

AI_PROMPT_TEMPLATE = AI_PROMPT_COMMON + "\n" + AI_PROMPT_CUSTOM + "\n请分析日志内容并返回JSON格式的攻击信息。"

# 数据库配置
DB_PATH = "aegis_log.db"  # SQLite数据库文件路径

# 攻击类型定义
ATTACK_TYPES = [
    "DDoS",
    "SYN Flood",
    "UDP Flood",
    "SQL 注入",
    "XSS 攻击",
    "登录爆破",
    "Brute Force",
    "扫描探测",
    "恶意爬虫",
    "其他攻击"
]

# 攻击类型映射表 (数据库存储的英文类型 -> 界面显示的中文类型)
ATTACK_TYPE_MAPPING = {
    "DDoS": "DDoS",
    "SYN Flood": "SYN Flood",
    "UDP Flood": "UDP Flood",
    "SQL Injection": "SQL 注入",
    "XSS": "XSS 攻击",
    "Brute Force": "登录爆破",
    "Scanning": "扫描探测",
    "Malicious Crawler": "恶意爬虫",
    "Unknown": "其他攻击"
}