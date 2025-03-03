from typing import Any, Dict

from .sql_manager import SQLiteManager
from ..config import config, logger

class UserManager:
    _instance = None  # 类属性用于存储单例

    def __new__(cls):
        """
        单例模式
        
        返回:
        - ModelManager类的实例
        """
        if cls._instance is None:
            # 如果尚未实例化，则初始化新实例
            cls._instance = super(UserManager, cls).__new__(cls)
            cls._current_model = config.default_model
        return cls._instance
    
    def get_user_config(self, user_id: str) -> Dict:
        """
        获取用户配置

        参数:
        - user_id: 用户ID

        返回:
        - 用户配置字典
        """
        # 从数据库获取用户配置
        # 如果用户配置不存在，则创建一个默认配置
        if not SQLiteManager().query(table_name=config.db_user_config_table_name, where="user_id", params=[user_id], dump=True):
            SQLiteManager().insert(table_name=config.db_user_config_table_name, data={
                "user_id": user_id, 
                "personality": config.personality_default, 
                "temperature": config.temperature,
                "max_history_length": config.max_history_length
                })

        user_config = SQLiteManager().query(table_name=config.db_user_config_table_name, where="user_id", params=[user_id], dump=True)
        return user_config[0]

    def set_user_config(self, user_id: str, user_config: Dict) -> None:
        """
        设置用户配置

        参数:
        - user_id: 用户ID
        - config: 用户配置字典
        """
        # 更新数据库中的用户配置
        SQLiteManager().update(table_name=config.db_user_config_table_name, data=user_config, where="user_id = ?", where_params=[user_id])

    def clear_user_conversation(self, user_id: str) -> None:
        """
        清空用户对话历史

        参数:
        - user_id: 用户ID
        """
        conversation_table_name = f'"{user_id}_conversations"'
        # 清空数据库中的用户对话历史
        SQLiteManager().delete(table_name=conversation_table_name)