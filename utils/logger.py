import sys
from pathlib import Path

from loguru import logger


class Logger:
    _instance = None
    _log_buffer = []  # 存储本次运行的日志

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.initialized = True
            self.setup_logger()

    def setup_logger(self):
        """配置日志记录器"""
        # 确保日志目录存在
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 移除默认的处理器
        logger.remove()

        # 添加控制台输出（仅INFO级别以上）
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            level="INFO",
            colorize=True
        )

        # 添加文件输出（按天）
        logger.add(
            "logs/ddns_{time:YYYY-MM-DD}.log",
            rotation="00:00",  # 每天轮换
            retention="30 days",  # 保留30天
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
            encoding="utf-8",
            level="DEBUG"
        )

        # 添加内存日志处理器
        logger.add(self._log_handler, level="DEBUG")

    def _log_handler(self, message):
        """处理内存日志"""
        self._log_buffer.append(message.record)

    def get_buffer(self):
        """获取内存中的日志"""
        return self._log_buffer

    def clear_buffer(self):
        """清除内存中的日志"""
        self._log_buffer.clear()

    def info(self, message):
        """记录信息日志"""
        logger.info(message)

    def error(self, message):
        """记录错误日志"""
        logger.error(message)

    def warning(self, message):
        """记录警告日志"""
        logger.warning(message)

    def debug(self, message):
        """记录调试日志"""
        logger.debug(message)

    def exception(self, message):
        """记录异常日志"""
        logger.exception(message)
