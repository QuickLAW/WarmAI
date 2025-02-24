import json
from typing import Dict

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
    
    def get_history(self, user_id: str) -> ConversationHistory:
        """
        获取用户的对话历史

        :param user_id: 用户ID
        :return: ConversationHistory对象
        """
        if user_id in self._conversations:
            return self._conversations[user_id]
        else:
            history = SQLiteManager().query(config.db_user_table_name, ["conversation_history"], "user_id", [user_id])
            if history:
                return ConversationHistory(**json.loads(history[0][0]))
            else:
                return ConversationHistory()
        

    def update_conversation(self, user_id: str, conversation: ConversationHistory):
        """
        保存对话至数据库
        ***（完全覆盖）***

        :param user_id: 用户ID
        :param conversation: 对话
        """
        SQLiteManager().upsert(config.db_user_table_name, {"conversation_history": conversation.to_json(), "user_id": user_id}, ["user_id"])

    def add_new_conversation(self, user_id: str, new_conversation: ConversationHistory):
        """
        添加新对话
        ***（仅添加新对话）***

        :param user_id: 用户ID
        :param new_conversation: 新的对话
        """
        history: ConversationHistory = self.get_history(user_id)
        history.add_message(new_conversation)
        SQLiteManager().upsert(config.db_user_table_name, {"conversation_history": history.to_json(), "user_id": user_id}, ["user_id"])

    def clear_conversation(self, user_id: str):
        """清除用户的对话"""
        if user_id in self._conversations:
            del self._conversations[user_id]