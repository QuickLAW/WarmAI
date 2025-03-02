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