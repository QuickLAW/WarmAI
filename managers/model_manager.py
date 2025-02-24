"""
核心管理模块
功能：
- 模型切换管理
- 对话流程控制
- 性格模板管理

包含：
- ModelManager：核心管理类

维护建议：
1. 保持与具体模型实现的解耦
2. 核心业务流程修改需谨慎
"""

from typing import Dict, Callable

from .conversation_manager import ConversationManager
from .sql_manager import SQLiteManager
from ..config import config, logger
from ..models import ConversationHistory
from ..handlers.ai_handlers import (
    BaseModelHandler,
    OpenAIModelHandler,
    DeepSeekModelHandler,
    AnthropicModelHandler,
    DoubaoModelHandler
)

class ModelManager:
    _instance = None  # 类属性用于存储单例

    def __new__(cls):
        """
        单例模式
        
        返回:
        - ModelManager类的实例
        """
        if cls._instance is None:
            # 如果尚未实例化，则初始化新实例
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._handlers: Dict[str, Callable] = {}
            cls._current_model = config.default_model
            cls._personality_templates = config.personality_templates
            cls._instance._init_handlers()
        return cls._instance

    def _init_handlers(self):
        """
        初始化模型处理器
        
        此方法用于初始化模型处理器的实例，并将其存储在 _handlers 属性中。
        """
        self._handlers = {
            "gpt-3.5-turbo": OpenAIModelHandler(config.openai_model_name),
            "gpt-4": OpenAIModelHandler("gpt-4"),
            "deepseek": DeepSeekModelHandler(config.deepseek_model_name),
            "doubao": DoubaoModelHandler(config.doubao_model_name),
            "claude": AnthropicModelHandler()
        }

    @property
    def available_models(self) -> list:
        """
        获取可用的模型列表
        
        返回:
        - 可用的模型列表
        """
        return list(self._handlers.keys())

    async def process_message(
        self,
        user_id: str,
        message: str,
    ) -> str:
        """
        处理用户消息的完整流程
        
        参数：
        - user_id: 用户唯一标识
        - message: 用户消息内容
        - db_get_history: 获取历史记录的函数
        - db_save_history: 保存历史记录的函数
        
        返回：
        - 生成的回复内容
        """
        try:
            # 获取对话上下文
            history: ConversationHistory = ConversationManager().get_history(user_id)
            
            # 构建提示词
            prompt = self._build_prompt(
                message=message,
                personality=history.personality,
                history=history.messages
            )
            
            # 调用模型生成
            handler: BaseModelHandler = self._handlers[self._current_model]
            response_list = await handler.generate(prompt, history)
            
            if response_list[1] == -1:
                return response_list[0]

            response = response_list[0]
            # 更新对话历史
            self._update_history(history, message, response)
            ConversationManager().update_conversation(user_id, history)
            
            return response
        except Exception as e:
            logger.exception("消息处理流程异常")
            return "服务暂时不可用，请稍后重试"

    def _build_prompt(self, message: str, personality: str, history: list) -> str:
        """
        构建提示词
        
        参数：
        - message: 用户消息内容
        - personality: 性格模板名称
        - history: 对话历史记录
        
        返回：
        - 构建好的提示词
        """
        template = self._personality_templates.get(
            personality,
            self._personality_templates["default"]
        )
        
        prompt = [
            f"系统角色：{template}",
            "\n对话历史："
        ]
        
        # 保留最近N条历史
        for msg in history[-config.max_history_length :]:
            prompt.append(f"{msg['role']}: {msg['content']}")
            
        prompt.append(f"\n当前消息：{message}")
        return "\n".join(prompt)

    def _update_history(self, history: ConversationHistory, message: str, response: str):
        """
        更新对话历史
        
        参数：
        - history: 对话历史记录对象
        - message: 用户消息内容
        - response: 模型生成的回复内容
        """
        history.messages.extend([
            {"role": "user", "content": message},
            {"role": "assistant", "content": response}
        ])
        
        # 控制历史记录长度
        if len(history.messages) > config.max_history_length * 2:
            history.messages = history.messages[-(config.max_history_length * 2) :]