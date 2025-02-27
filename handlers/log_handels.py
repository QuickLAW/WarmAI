"""
日志处理模块
功能：
- 记录消息处理前后的日志
- 提供日志相关的辅助功能

维护建议：
1. 保持日志逻辑独立
2. 确保日志格式统一
"""

from nonebot.log import logger
from ..service.bus import bus

# 定义事件类型
EVENT_BEFORE_PROCESS = "before_process"  # 消息处理前事件
EVENT_AFTER_PROCESS = "after_process"    # 消息处理后事件

@bus.register(EVENT_BEFORE_PROCESS)
async def log_before_process(data: dict):
    """
    记录消息处理前的日志
    """
    user_id = data["user_id"]
    message = data["message"]
    logger.info(f"用户 {user_id} 发送消息：{message}")

@bus.register(EVENT_AFTER_PROCESS)
async def log_after_process(data: dict):
    """
    记录消息处理后的日志
    """
    user_id = data["user_id"]
    message = data["message"]
    response = data["response"]
    logger.info(f"用户 {user_id} 收到回复：{response}")