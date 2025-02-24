class EventSystem:
    def __init__(self):
        self.listeners = {}

    def on(self, event_name, callback):
        """注册事件监听器"""
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(callback)

    def off(self, event_name, callback):
        """移除事件监听器"""
        if event_name in self.listeners:
            self.listeners[event_name].remove(callback)
            if not self.listeners[event_name]:
                del self.listeners[event_name]

    def emit(self, event_name, *args, **kwargs):
        """触发事件"""
        if event_name in self.listeners:
            for callback in self.listeners[event_name]:
                callback(*args, **kwargs)

# 示例用法
def greet(name):
    print(f"Hello, {name}!")

def farewell(name):
    print(f"Goodbye, {name}!")

event_system = EventSystem()

# 注册事件监听器
event_system.on('greet', greet)
event_system.on('farewell', farewell)

# 触发事件
event_system.emit('greet', name='Alice')
event_system.emit('farewell', name='Bob')

# 移除事件监听器
event_system.off('greet', greet)

# 再次触发事件
event_system.emit('greet', name='Charlie')  # 这次不会有任何输出



