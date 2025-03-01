"""
私聊消息触发模块
功能：
- 捕获私聊消息并分发到事件总线
- 定义私聊消息相关的事件类型

维护建议：
1. 保持与具体业务逻辑解耦
2. 确保事件类型定义清晰
"""

from nonebot import on_message
from nonebot.matcher import Matcher
from nonebot.adapters.onebot.v11 import PrivateMessageEvent
from ..events.message_events import MessageSentEvent, MessageReceivedEvent

# 初始化消息捕获器
private_message_matcher = on_message(priority=10, block=False)

@private_message_matcher.handle()
async def capture_private_message(event: PrivateMessageEvent, matcher: Matcher):
    """
    捕获私聊消息并分发到事件总线
    """
    await MessageReceivedEvent().async_trigger(event=event, matcher=matcher)