from ..service.bus import Event

class MessageReceivedEvent(Event):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance
    
    def handle_exception(self, exc: Exception) -> bool:
        print(f"处理事件异常: {exc}")
        return True

class MessageSentEvent(Event):
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super().__new__(cls)
        return cls.instance
    
    def handle_exception(self, exc: Exception) -> bool:
        print(f"处理事件异常: {exc}")
        return True