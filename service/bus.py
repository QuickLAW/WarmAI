import asyncio
import inspect
import contextvars
from typing import (
    Any, Awaitable, Callable, ClassVar, Generic, Optional, Type, TypeVar, Union
)

# 上下文变量用于访问当前事件
current_event = contextvars.ContextVar('current_event')

E = TypeVar('E', bound='Event')
EventHandler = Union[
    Callable[..., Optional[Any]],
    Callable[..., Awaitable[Optional[Any]]]
]

class HandlerList(Generic[E]):
    """带优先级的事件处理器容器"""
    def __init__(self) -> None:
        self._handlers: list[tuple[int, Callable[..., Any]]] = []

    def add(self, handler: Callable[..., Any], priority: int = 0) -> None:
        """添加带优先级的处理器"""
        if not callable(handler):
            raise TypeError("Handler must be callable")
        self._handlers.append((priority, handler))
        self._handlers.sort(key=lambda x: (-x[0], id(x[1])))  # 稳定排序

    async def invoke(self, *args: Any, **kwargs: Any) -> bool:
        """执行所有处理器"""
        event = current_event.get()
        
        for _, handler in self._handlers:
            if event.is_cancelled:
                return True

            try:
                result = handler(*args, **kwargs)
                if inspect.isawaitable(result):
                    await result
            except Exception as e:
                if not event.handle_exception(e):
                    raise

        return event.is_cancelled

def priority(p: int) -> Callable[[EventHandler], EventHandler]:
    """优先级装饰器"""
    def decorator(func: EventHandler) -> EventHandler:
        setattr(func, "__event_priority__", p)
        return func
    return decorator

class EventMeta(type):
    """事件类的元类"""
    def __new__(cls, name: str, bases: tuple[type, ...], attrs: dict):
        new_class = super().__new__(cls, name, bases, attrs)
        new_class.handlers = HandlerList[new_class]()  # type: ignore
        return new_class

class Event(metaclass=EventMeta):
    """事件基类"""
    handlers: ClassVar[HandlerList]
    is_cancelled: bool = False

    @classmethod
    def on(cls: Type[E], priority: int = 0) -> Callable[[EventHandler], EventHandler]:
        """事件注册装饰器工厂"""
        def decorator(func: EventHandler) -> EventHandler:
            cls.handlers.add(func, priority)
            return func
        return decorator

    async def _invoke(self, *args: Any, **kwargs: Any) -> bool:
        """触发事件的实际实现"""
        self.is_cancelled = False  # 重置取消状态
        token = current_event.set(self)
        try:
            return await self.__class__.handlers.invoke(*args, **kwargs)
        finally:
            current_event.reset(token)

    def trigger(self, *args: Any, **kwargs: Any) -> None:
        """同步触发入口（仅限非异步环境使用）"""
        try:
            # 检测是否在运行中的事件循环
            asyncio.get_running_loop()
            raise RuntimeError("Cannot use trigger() in async context. Use async_trigger() instead.")
        except RuntimeError:
            # 没有运行中的事件循环
            asyncio.run(self._invoke(*args, **kwargs))

    async def async_trigger(self, *args: Any, **kwargs: Any) -> None:
        """异步触发入口"""
        await self._invoke(*args, **kwargs)

    def cancel(self) -> None:
        """
        取消事件传播
        
        注意：
        - 此方法仅在事件处理过程中有效。
        - 取消事件后，后续的处理器将不再执行。
        """
        self.is_cancelled = True

    def handle_exception(self, exc: Exception) -> bool:
        """异常处理（子类可重写）"""
        return False

# 使用示例
class LoginEvent(Event):
    def handle_exception(self, exc: Exception) -> bool:
        print(f"处理事件异常: {exc}")
        return True

class User:
    def __init__(self, username: str):
        self.username = username

        
@LoginEvent.on(priority=2)
def security_check(var1: User, var2: Any):
    event: LoginEvent = current_event.get()
    if "admin" in var1.username:
        print("安全检测通过")
    else:
        event.cancel()
        print("安全检测失败!")



async def main():

    user = User("admin")
    event = LoginEvent()
    
    # 正确的异步触发方式
    await event.async_trigger(user, "192.168.1.1", log_prefix="调试信息")

if __name__ == "__main__":
    # 正确的同步触发示例
    user = User("admin")
    login_event = LoginEvent()
    login_event.trigger(user, "10.0.0.1")  # 在同步环境中使用
    
    # 正确的异步入口
    asyncio.run(main())