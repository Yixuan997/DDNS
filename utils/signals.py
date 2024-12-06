from threading import Lock
from typing import Callable, List, Type, Optional, TypeVar, Generic

T = TypeVar('T')


class Signal(Generic[T]):
    """
    一个支持类型提示的信号实现，用于事件处理
    可以指定信号参数的类型，例如：Signal(int) 表示这个信号会发送整数类型的数据
    """

    def __init__(self, type_hint: Optional[Type[T]] = None):
        """
        初始化信号实例

        Args:
            type_hint: 可选的类型提示，用于指定信号将发送的数据类型
        """
        self._handlers: List[Callable] = []
        self._lock = Lock()
        self._type_hint = type_hint

    def connect(self, handler: Callable[..., None]) -> None:
        """
        连接一个处理函数到这个信号

        Args:
            handler: 当信号发出时要调用的回调函数
        """
        with self._lock:
            if handler not in self._handlers:
                self._handlers.append(handler)

    def disconnect(self, handler: Callable[..., None]) -> None:
        """
        断开处理函数与信号的连接

        Args:
            handler: 要移除的回调函数
        """
        with self._lock:
            if handler in self._handlers:
                self._handlers.remove(handler)

    def emit(self, *args, **kwargs) -> None:
        """
        发出信号，调用所有已连接的处理函数

        Args:
            *args: 要传递给处理函数的位置参数
            **kwargs: 要传递给处理函数的关键字参数
        """
        with self._lock:
            handlers = self._handlers.copy()

        for handler in handlers:
            try:
                handler(*args, **kwargs)
            except Exception as e:
                print(f"信号处理器 {handler} 发生错误: {str(e)}")

    def clear(self) -> None:
        """清除所有已连接的处理函数"""
        with self._lock:
            self._handlers.clear()

    @property
    def type_hint(self) -> Optional[Type[T]]:
        """获取信号的类型提示"""
        return self._type_hint
