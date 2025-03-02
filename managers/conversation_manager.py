import json
from typing import Dict, List

from ..config import config
from ..models import ConversationHistory
from .sql_manager import SQLiteManager


class ConversationManager:
    _instance = None  # 类属性用于存储单例

    def __new__(cls):
        if cls._instance is None:
            # 如果尚未实例化，则初始化新实例
            cls._instance = super(ConversationManager, cls).__new__(cls)
            cls._conversations: Dict[str, ConversationHistory] = {}
        return cls._instance
    
    def get_history(self, user_id: str) -> List[ConversationHistory]:
        """
        获取用户的对话历史

        :param user_id: 用户ID
        :return: ConversationHistory对象
        """
        history = SQLiteManager().query(table_name=f'"{user_id}_conversations"', dump=True)

        if history:
            return [ConversationHistory(
                user_id=h["user_id"],
                timestamp=h["timestamp"],
                message_content=h["message_content"],
                is_recalled=h["is_recalled"],
                is_ai=h["is_ai"]
                ) for h in history]
        else:
            return []

    def update_conversation(self, user_id: str, new_conversation: ConversationHistory):
        """
        保存对话至数据库
        ***（完全覆盖）***

        :param user_id: 用户ID
        :param conversation: 对话
        """
        SQLiteManager().insert(table_name=f'"{user_id}_conversations"', data=new_conversation.to_dict())

    def add_new_conversation(self, user_id: str, new_conversation: ConversationHistory):
        """
        添加新对话
        ***（仅添加新对话）***

        :param user_id: 用户ID
        :param new_conversation: 新的对话
        """

        SQLiteManager().insert(table_name=f'"{user_id}_conversations"', data=new_conversation.to_db_dict())

    def clear_conversation(self, user_id: str):
        """清除用户的对话"""
        if user_id in self._conversations:
            del self._conversations[user_id]