from ..managers.sql_manager import SQLiteManager
from ..managers.conversation_manager import ConversationManager
from ..managers.model_manager import ModelManager
from ..config import config

# 初始化数据库
SQLiteManager().create_table(config.db_user_config_table_name, config.db_user_config_table_columns)

