from config import LOG_LEVEL, LOG_FILE, LOG_FORMAT, LOG_CONSOLE, LOG_RETENTION_DAYS, ANALYZE_FILES
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import os

class AegisLogger:
    def __init__(self):
        self.logger = logging.getLogger('AegisLogger')
        self.logger.setLevel(LOG_LEVEL)
        
        # 设置日志格式
        formatter = logging.Formatter(LOG_FORMAT)
        
        # 控制台输出
        if LOG_CONSOLE:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 文件输出
        file_handler = TimedRotatingFileHandler(
            LOG_FILE,
            when='midnight',
            interval=1,
            backupCount=LOG_RETENTION_DAYS
        )
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
    def debug(self, msg):
        self.logger.debug(msg)
        
    def info(self, msg):
        self.logger.info(msg)
        
    def warning(self, msg):
        self.logger.warning(msg)
        
    def error(self, msg):
        self.logger.error(msg)
        
    def critical(self, msg):
        self.logger.critical(msg)
        