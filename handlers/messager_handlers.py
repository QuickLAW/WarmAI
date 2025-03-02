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

from ..managers.conversation_manager import ConversationManager
from ..managers.model_manager import ModelManager
from ..managers.sql_manager import SQLiteManager
from ..models import ConversationHistory
from ..config import config
from ..events.message_events import MessageSentEvent, MessageReceivedEvent

@MessageReceivedEvent.on(priority=5)
async def handle_private_message(event: PrivateMessageEvent, matcher: Matcher):
    """
    处理私聊消息
    
    参数：
    - event: 私聊消息事件
    """
    # 获取用户ID和消息内容
    user_id = str(event.user_id)
    message = event.get_plaintext()
    time = event.time
    print(time)

    print(message)

    # 触发消息处理前事件
    # await bus.event_before_process({"user_id": user_id, "message": message})

    # 调用核心管理模块处理消息
    response = await ModelManager().process_message(
        user_id=user_id,
        message=message,
        time=time,
    )

    # 触发消息处理后事件
    # await bus.event_after_process({"user_id": user_id, "message": message, "response": response})

    # 发送回复
    await MessageSentEvent().async_trigger(event=event, matcher=matcher, response=response)


@MessageReceivedEvent.on(priority=10)
async def create_user_conversations_table(event: PrivateMessageEvent, matcher: Matcher):
    """
    创建用户会话表，如果表不存在
    表名为：<user_id>_conversations

    参数：
    - event: 私聊消息事件
    """
    user_id = str(event.user_id)
    table_name = f'"{user_id}_conversations"'

    # 检查表是否存在
    if not SQLiteManager().check_table_exists(table_name):
        # 创建表
        SQLiteManager().create_table(table_name, config.db_user_conversations_table_columns)

@MessageSentEvent.on()
async def send_message(event: PrivateMessageEvent, matcher: Matcher, response: str):
    """
    发送消息

    参数：
    - event: 私聊消息事件
    """

    await matcher.finish(Message(response))

@MessageSentEvent.on()
async def update_user_conversations_table_for_ai_reply(event: PrivateMessageEvent, matcher: Matcher, response: str):
    """
    更新用户会话表

    参数：
    - event: 私聊消息事件
    """
    user_id = str(event.user_id)

    # 创建新的会话记录
    new_conversation = ConversationHistory(
        user_id=str(event.self_id),
        timestamp=event.time,
        message_content=response,
        is_recalled=False,
        is_ai=True 
    )
    
    # 更新用户会话表
    ConversationManager().add_new_conversation(user_id=user_id, new_conversation=new_conversation)