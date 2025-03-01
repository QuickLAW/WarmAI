"""
插件入口文件
功能：
- 导出核心组件
- 提供快速访问接口

维护建议：
1. 保持最小化导出
2. 避免在此实现业务逻辑
"""
from .models import ConversationHistory
from .handlers import *
from .managers import conversation_manager, model_manager, sql_manager
from .protocal import init
from .service import *
from .triggers import *

from nonebot.plugin import PluginMetadata

from .config import PluginConfig

__all__ = ["model_manager", "ConversationHistory"]

__plugin_meta__ = PluginMetadata(
    name="WarmAI",
    description="这是一个AI聊天插件",
    usage="用来和AI聊天的插件",
    type="application",
    config=PluginConfig,
    extra={},
)