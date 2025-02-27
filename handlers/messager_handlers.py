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
from ..managers.model_manager import ModelManager
from ..managers.sql_manager import SQLiteManager
from ..models import ConversationHistory
from ..config import config
from ..service.bus import bus

# 定义事件类型
EVENT_BEFORE_PROCESS = "before_process"  # 消息处理前事件
EVENT_AFTER_PROCESS = "after_process"    # 消息处理后事件

@bus.register("private_message")
async def handle_private_message(event: PrivateMessageEvent):
    """
    处理私聊消息
    
    参数：
    - event: 私聊消息事件
    """
    # 获取用户ID和消息内容
    user_id = str(event.user_id)
    message = event.get_plaintext()

    # 触发消息处理前事件
    await bus.dispatch(EVENT_BEFORE_PROCESS, {"user_id": user_id, "message": message})

    # 模拟数据库方法
    async def db_get_history(uid: str):
        """
        获取对话历史记录
        """
        conversations: List[ConversationHistory] = SQLiteManager().query_data(
            config.db_user_table_name, ["conversation_history"], ["user_id"], [uid]
        )
        conversations = conversations[0][0] if conversations else None
        conversations = json.loads(conversations) if conversations else None
        return {"messages": conversations['messages'], "personality": "default"}

    async def db_save_history(uid: str, data: dict):
        """
        保存对话历史记录
        """
        SQLiteManager().add_conversation_message(config.db_user_table_name, uid, data)
        return True

    # 调用核心管理模块处理消息
    response = await ModelManager().process_message(
        user_id=user_id,
        message=message,
    )

    # 触发消息处理后事件
    await bus.dispatch(EVENT_AFTER_PROCESS, {
        "user_id": user_id,
        "message": message,
        "response": response
    })

    # 发送回复
    await event.finish(Message(response))