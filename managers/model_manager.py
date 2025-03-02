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

from datetime import datetime
from typing import Dict, Callable, List

from .user_manager import UserManager

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
        time: int
    ) -> str:
        """
        处理用户消息的完整流程
        
        参数：
        - user_id: 用户唯一标识
        - message: 用户消息内容
        
        返回：
        - 生成的回复内容
        """
        # 先保存消息至数据库
        try:
            # 保存消息至数据库
            ConversationManager().add_new_conversation(
                user_id=user_id,
                new_conversation=ConversationHistory(
                    user_id=user_id,
                    timestamp=time,
                    message_content=message,
                    is_recalled=False,
                    is_ai=False
                )
            )
        except Exception as e:
            logger.exception("消息保存流程异常")
        try:
            # 获取对话上下文
            history: List[ConversationHistory] = ConversationManager().get_history(user_id)
            user_config = UserManager().get_user_config(user_id)
            personality = user_config["personality"]
            
            # 构建提示词
            prompt = self._build_prompt(
                personality=personality,
                history=history
            )
            
            # 调用模型生成
            handler: BaseModelHandler = self._handlers[self._current_model]
            response_list = await handler.generate(prompt, user_id)
            
            if response_list[1] == -1:
                return response_list[0]

            response = response_list[0]
            
            return response
        except Exception as e:
            logger.exception("消息处理流程异常")
            return "服务暂时不可用，请稍后重试"

    def _build_prompt(self, personality: str, history: List[ConversationHistory]) -> List:
        """
        构建提示词
        
        参数：
        - personality: 性格模板内容
        - history: 对话历史记录列表
        
        返回：
        - 构建好的提示词
        可以直接作为json格式发送给模型
        """
        if not personality:
            personality = config.personality_default
        
        prompt = [{"role": "system", "content": datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n" + personality}]
        
        # 保留最近N条历史
        history = history[-min(config.max_history_length, len(history)) :]
        is_current = history[0].to_dict()["is_ai"]
        current_user_conversation = ""
        for msg in history[-config.max_history_length :]:
            if is_current != msg.to_dict()["is_ai"]:
                if is_current:
                    prompt.append({"role": "assistant", "content": current_user_conversation})
                else:
                    prompt.append({"role": "user", "content": current_user_conversation})
                current_user_conversation = ""
                is_current = msg.to_dict()["is_ai"]
            current_user_conversation += msg.to_conversation() + "\n\n"
        
        if history[0].to_dict()["is_ai"]:
            prompt.append({"role": "assistant", "content": current_user_conversation})
        else:
            prompt.append({"role": "user", "content": current_user_conversation})
            
        return prompt

    def update_history(self, history: ConversationHistory, message: str, response: str):
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