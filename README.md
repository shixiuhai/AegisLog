# AegisLog AI日志分析系统

## 概述
AegisLog是一个基于AI的智能日志分析系统，提供以下功能：
- 多级别日志记录(DEBUG/INFO/WARNING/ERROR/CRITICAL)
- AI驱动的日志内容分析和攻击类型识别
- SQLite数据库存储和分析
- 实时Web Dashboard可视化界面
- 攻击统计和态势感知
- 自动日志轮转和清理

## 系统架构

```
AegisLog System Architecture
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Log Input     │───▶│   AI Analysis    │───▶│  SQLite Database│
│ (AegisLogger)   │    │   (OpenAI API)   │    │   (models.py)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Console/File    │    │ Attack Type     │    │ Web Dashboard   │
│   Output        │    │ Classification  │    │   (Flask App)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 安装依赖

```bash
pip install openai flask sqlite3
```

## 配置文件 (config.py)

系统配置参数：

```python
# OpenAI API配置
OPENAI_API_KEY = "your-openai-api-key-here"
OPENAI_MODEL = "gpt-3.5-turbo"

# 日志配置
LOG_LEVEL = 'INFO'
LOG_FILE = 'aegis.log'
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_CONSOLE = True
LOG_RETENTION_DAYS = 7

# 数据库配置
DATABASE_FILE = 'aegis_log.db'

# 攻击类型配置
ATTACK_TYPES = [
    "SQL注入", "XSS攻击", "CSRF攻击", "文件上传漏洞",
    "命令注入", "目录遍历", "暴力破解", "DDoS攻击",
    "信息泄露", "权限提升", "会话劫持", "其他攻击"
]

# 攻击类型映射（数据库存储英文，界面显示中文）
ATTACK_TYPE_MAPPING = {
    "SQL Injection": "SQL注入",
    "XSS Attack": "XSS攻击", 
    "CSRF Attack": "CSRF攻击",
    "File Upload Vulnerability": "文件上传漏洞",
    "Command Injection": "命令注入",
    "Directory Traversal": "目录遍历",
    "Brute Force": "暴力破解",
    "DDoS Attack": "DDoS攻击",
    "Information Disclosure": "信息泄露",
    "Privilege Escalation": "权限提升",
    "Session Hijacking": "会话劫持",
    "Other Attack": "其他攻击"
}
```

## 核心组件

### 1. 数据库模型 (models.py)
- `DatabaseManager`: 数据库连接管理和操作
- 攻击记录表结构：
  - id: 主键
  - timestamp: 时间戳
  - log_level: 日志级别
  - message: 日志内容
  - attack_type: 攻击类型
  - source_ip: 源IP地址
  - is_blocked: 是否已阻断

### 2. Web Dashboard (app.py)
Flask应用提供以下API端点：
- `/`: Web Dashboard主界面
- `/api/stats`: 获取系统统计信息
- `/api/attack-types`: 获取攻击类型分布
- `/api/recent-attacks`: 获取最近攻击记录

### 3. 日志记录器 (logger.py)
增强的AegisLogger类，支持AI分析和数据库存储。

## 使用示例

### 基本日志记录
```python
from logger import AegisLogger

logger = AegisLogger()
logger.info("用户登录成功")
logger.warning("检测到可疑活动")
logger.error("SQL注入攻击尝试")
```

### 启动Web Dashboard
```bash
python3 app.py
```
访问 http://localhost:5000 查看实时监控界面

### API接口调用
```bash
# 获取系统统计
curl http://localhost:5000/api/stats

# 获取攻击类型分布  
curl http://localhost:5000/api/attack-types

# 获取最近攻击记录
curl http://localhost:5000/api/recent-attacks
```

## Web Dashboard功能

### 实时监控面板
- 总攻击次数统计
- 攻击类型分布饼图
- 最近攻击记录列表
- 已阻断IP地址显示
- 自动30秒刷新

### 数据可视化
- 使用ECharts绘制攻击类型分布图
- Bootstrap 5响应式界面设计
- 中文界面支持
- 移动端适配

## API参考

### GET /api/stats
返回系统统计信息：
```json
{
  "total_attacks": 150,
  "blocked_ips": 25,
  "attack_percentage": 15.8
}
```

### GET /api/attack-types  
返回攻击类型分布：
```json
[
  {"name": "SQL注入", "value": 45},
  {"name": "XSS攻击", "value": 32},
  {"name": "暴力破解", "value": 28}
]
```

### GET /api/recent-attacks
返回最近攻击记录：
```json
[
  {
    "timestamp": "2024-01-15 10:30:25",
    "attack_type": "SQL注入",
    "source_ip": "192.168.1.100",
    "is_blocked": true
  }
]
```

## 性能特性

- **实时分析**: AI即时分析日志内容
- **数据缓存**: 内存缓存提升查询性能
- **自动清理**: 定期清理旧日志记录
- **线程安全**: 多线程环境安全操作
- **错误恢复**: 数据库连接自动重连

## 部署说明

1. 配置OpenAI API密钥
2. 设置日志文件路径
3. 启动Flask应用
4. 配置反向代理（生产环境）
5. 设置系统服务（可选）

## 故障排除

### 常见问题
1. **OpenAI API错误**: 检查API密钥配置
2. **数据库连接失败**: 检查文件权限
3. **导入错误**: 确保所有依赖已安装

### 日志文件位置
- 应用日志: `aegis.log`
- 数据库文件: `aegis_log.db`
- Flask访问日志: 控制台输出

## 版本历史

### v2.0 (当前版本)
- 新增AI日志分析功能
- 添加SQLite数据库存储
- 实现Web Dashboard界面
- 支持攻击类型统计
- 添加实时监控功能

### v1.0 (初始版本)
- 基础日志记录功能
- 文件轮转支持
- 多级别日志输出

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 许可证

MIT License