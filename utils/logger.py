import sys
import time
from pathlib import Path

from loguru import logger


class Logger:
    _instance = None
    _log_buffer = []  # 存储本次运行的日志
    _last_log = {}  # 存储最后一条日志的内容和时间，用于去重
    _max_buffer_size = 1000  # 最大缓存日志数量

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
        try:
            # 确保日志目录存在
            log_dir = Path("logs")
            log_dir.mkdir(exist_ok=True)

            # 移除默认的处理器
            logger.remove()

            # 在开发环境添加控制台输出
            if not getattr(sys, 'frozen', False):  # 不是打包环境
                logger.add(
                    sys.stderr,
                    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
                    level="DEBUG",
                    colorize=True,
                    filter=self._filter_repeated_logs
                )

            # 添加文件输出（按天）
            logger.add(
                str(log_dir / "ddns_{time:YYYY-MM-DD}.log"),
                rotation="00:00",  # 每天轮换
                retention="30 days",  # 保留30天
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
                encoding="utf-8",
                level="DEBUG",
                compression="zip"  # 压缩旧日志
            )

            # 添加内存日志处理器，用于界面显示
            def log_handler(message):
                self._log_buffer.append(message.record)
                # 限制缓存大小
                if len(self._log_buffer) > self._max_buffer_size:
                    self._log_buffer.pop(0)

            logger.add(log_handler, level="DEBUG")

        except Exception as e:
            print(f"日志系统初始化失败: {str(e)}")
            sys.exit(1)

    def _filter_repeated_logs(self, record):
        """过滤重复的日志"""
        message = record["message"]
        level = record["level"].name
        now = time.time()
        key = f"{level}:{message}"

        # 检查是否是重复日志且时间间隔小于3秒
        if key in self._last_log:
            last_time = self._last_log[key]
            if now - last_time < 3:  # 3秒内的相同日志不显示
                return False

        self._last_log[key] = now
        return True

    def get_buffer(self):
        """获取内存中的日志"""
        return self._log_buffer

    def clear_buffer(self):
        """清除内存中的日志"""
        self._log_buffer.clear()

    def info(self, message, *args, **kwargs):
        """记录信息日志"""
        logger.info(message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        """记录错误日志"""
        logger.error(message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        """记录警告日志"""
        logger.warning(message, *args, **kwargs)

    def debug(self, message, *args, **kwargs):
        """记录调试日志"""
        logger.debug(message, *args, **kwargs)

    def exception(self, message, *args, **kwargs):
        """记录异常日志"""
        logger.exception(message, *args, **kwargs)
