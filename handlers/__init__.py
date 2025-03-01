'''
__init__.py

作用：
- 导出核心组件
- 提供快速访问接口

维护建议：
1. 保持最小化导出
2. 避免在此实现业务逻辑
'''

from .ai_handlers import *
from .command_handlers import *
from .log_handlers import *
from .messager_handlers import *

__all__ = ["ai_handlers", "command_handlers", "log_handlers", "messager_handlers"]
# 版本
__version__ = "0.1.0"

# 作者
__author__ = "落叶"