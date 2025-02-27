"""
事件总线模块（单例模式）
功能：
- 提供事件分发机制
- 支持动态注册/移除处理器
- 统一管理事件处理逻辑

维护建议：
1. 保持总线与具体业务逻辑解耦
2. 确保事件类型定义清晰
3. 注意线程安全问题（如果涉及异步）
"""

from typing import Callable, Dict, List, Any
from nonebot.log import logger

class Bus:
    """
    事件总线类（单例模式）
    功能：
    - 管理事件处理器
    - 分发事件到对应的处理器
    """

    _instance = None  # 单例实例

    def __new__(cls, *args, **kwargs):
        """确保只有一个实例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """初始化单例实例"""
        if self._initialized:
            return
        self._handlers: Dict[str, List[Callable]] = {}  # 存储事件类型与处理器的映射
        self._initialized = True

    def register(self, event_type: str, handler: Callable):
        """
        注册事件处理器
        
        参数：
        - event_type: 事件类型（如 "private_message"）
        - handler: 处理函数，需接受事件数据作为参数
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"注册处理器：{event_type} -> {handler.__name__}")

    def unregister(self, event_type: str, handler: Callable):
        """
        移除事件处理器
        
        参数：
        - event_type: 事件类型
        - handler: 要移除的处理函数
        """
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]
            logger.info(f"移除处理器：{event_type} -> {handler.__name__}")

    async def dispatch(self, event_type: str, data: Any):
        """
        分发事件
        
        参数：
        - event_type: 事件类型
        - data: 事件数据
        """
        if event_type not in self._handlers:
            logger.warning(f"未找到 {event_type} 的处理器")
            return

        for handler in self._handlers[event_type]:
            try:
                await handler(data)  # 异步调用处理器
            except Exception as e:
                logger.error(f"处理器 {handler.__name__} 执行失败: {str(e)}")

# 全局单例实例
bus = Bus()