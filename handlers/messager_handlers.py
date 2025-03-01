"""
消息处理模块
功能：
- 处理私聊消息
- 调用核心管理模块生成回复

维护建议：
1. 保持与事件触发模块解耦
2. 确保处理逻辑清晰
"""

import json
from typing import List
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Message
from nonebot.matcher import Matcher
from ..managers.model_manager import ModelManager
from ..managers.sql_manager import SQLiteManager
from ..models import ConversationHistory
from ..config import config
from ..events.message_events import MessageSentEvent, MessageReceivedEvent

@MessageReceivedEvent.on()
async def handle_private_message(event: PrivateMessageEvent, matcher: Matcher):
    """
    处理私聊消息
    
    参数：
    - event: 私聊消息事件
    """
    # 获取用户ID和消息内容
    user_id = str(event.user_id)
    message = event.get_plaintext()

    # 触发消息处理前事件
    # await bus.event_before_process({"user_id": user_id, "message": message})

    # 调用核心管理模块处理消息
    response = await ModelManager().process_message(
        user_id=user_id,
        message=message,
    )

    # 触发消息处理后事件
    # await bus.event_after_process({"user_id": user_id, "message": message, "response": response})

    # 发送回复
    await MessageSentEvent().async_trigger(event=event, matcher=matcher)
    await matcher.finish(Message(response))