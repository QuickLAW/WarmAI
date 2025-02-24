"""
测试模块
功能：
- 捕获私聊消息
- 调用核心管理模块处理对话

维护建议：
1. 此模块仅用于测试，正式环境建议移除
2. 保持与核心模块的解耦
"""

import json
from typing import List
from nonebot import on_message
from nonebot.adapters.onebot.v11 import PrivateMessageEvent, Message
from ..managers.model_manager import ModelManager
from ..managers.conversation_manager import ConversationManager
from ..managers.sql_manager import SQLiteManager 
from ..models import ConversationHistory
from ..config import config

# 初始化测试功能
test_handler = on_message(priority=10, block=False)

@test_handler.handle()
async def handle_private_message(event: PrivateMessageEvent):
    """
    处理私聊消息
    
    参数：
    - event: 私聊消息事件
    """

    # 获取用户ID和消息内容
    user_id = str(event.user_id)
    message = event.get_plaintext()

    # 模拟数据库方法
    async def db_get_history(uid: str):
        """
        获取对话历史记录

        参数：
        - uid: 用户ID

        返回：
        - 对话历史记录
        """
        conversations: List[ConversationHistory] = SQLiteManager().query_data(config.db_user_table_name, ["conversation_history"], ["user_id"], [uid])
        conversations = conversations[0][0] if conversations else None
        conversations = json.loads(conversations) if conversations else None
        return {"messages": conversations['messages'], "personality": "default"}

    async def db_save_history(uid: str, data: dict):
        """
        保存对话历史记录

        参数：
        - uid: 用户ID
        - data: 对话历史记录
        """
        SQLiteManager().add_conversation_message(config.db_user_table_name, uid, data)
        return True

    # 调用核心管理模块处理消息
    response = await ModelManager().process_message(
        user_id=user_id,
        message=message,
    )

    await test_handler.finish(Message(response))