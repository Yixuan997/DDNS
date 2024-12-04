import gc
import os

import psutil
from loguru import logger


class MemoryTracker:
    """内存监控类"""

    @staticmethod
    def log_memory_usage():
        """记录当前内存使用情况"""
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            logger.debug(f"内存使用: {memory_mb:.2f} MB")
        except Exception as e:
            logger.error(f"获取内存使用信息失败: {str(e)}")

    @staticmethod
    def collect_garbage():
        """执行垃圾回收"""
        try:
            before_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            collected = gc.collect()
            after_mem = psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024
            saved = before_mem - after_mem

            if saved > 0:
                logger.debug(f"垃圾回收完成: 释放 {saved:.2f} MB 内存，回收 {collected} 个对象")
            else:
                logger.debug(f"垃圾回收完成: 回收 {collected} 个对象")

        except Exception as e:
            logger.error(f"执行垃圾回收失败: {str(e)}")
