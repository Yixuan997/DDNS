import gc
import os

import psutil
from utils.logger import Logger


class MemoryTracker:
    """内存监控类"""
    _last_memory_usage = 0  # 上次内存使用量
    _memory_threshold = 100  # 内存变化阈值（MB）

    @staticmethod
    def log_memory_usage():
        """记录当前内存使用情况"""
        logger = Logger()
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024

            # 只在内存变化超过阈值时记录
            if abs(memory_mb - MemoryTracker._last_memory_usage) > MemoryTracker._memory_threshold:
                logger.debug(f"内存使用: {memory_mb:.2f} MB (变化: {memory_mb - MemoryTracker._last_memory_usage:+.2f} MB)")
                MemoryTracker._last_memory_usage = memory_mb

        except Exception as e:
            logger.error(f"获取内存使用信息失败: {str(e)}")

    @staticmethod
    def collect_garbage():
        """执行垃圾回收"""
        logger = Logger()
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
