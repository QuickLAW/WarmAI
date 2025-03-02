"""
配置文件
功能：
- 插件配置管理
- 日志配置
- 全局参数定义

包含：
- PluginConfig：配置数据结构类
- 配置加载逻辑
- 日志记录器初始化

维护建议：
1. 新增配置项时需同步更新PluginConfig类
2. 敏感配置项建议通过.env文件加载
"""

import logging
from typing import List
from pydantic_settings import BaseSettings
from nonebot import get_driver

class PluginConfig(BaseSettings):
    """插件配置类"""


    # OpenAI相关配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model_name: str = "gpt-3.5-turbo"
    
    # DeepSeek配置
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model_name: str = "deepseek-chat"
    
    # 豆包配置
    doubao_api_key: str = ""
    doubao_base_url: str = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    doubao_model_name: str = "doubao-1-5-lite-32k-250115"

    # 通用配置
    default_model: str = "doubao"
    max_history_length: int = 20  # 最大对话历史长度
    temperature: float = 0.7  # 模型温度参数
    
    personality_default: str = "你叫落叶，是一位抽象玩梗的网友"

    # 数据库配置
    db_path: str = "./data/warmai/data.db"

    db_user_conversations_table_columns: List[str] = ["id INTEGER PRIMARY KEY AUTOINCREMENT", "user_id TEXT", "timestamp INTEGER", "message_content TEXT", "sender TEXT", "is_recalled INTEGER", "is_ai INTEGER"]

    db_user_config_table_name: str = "user_config"
    db_user_config_table_columns: List[str] = ["user_id INTEGER PRIMARY KEY", "personality TEXT", "temperature REAL", "max_history_length INTEGER"] 


    # 管理员用户ID列表
    admin_user_ids: List[int] = []

    class Config:
        extra = "ignore"  # 忽略未定义配置项

# 加载配置
config = PluginConfig(**get_driver().config.model_dump())

# 初始化日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
))
logger.addHandler(handler)