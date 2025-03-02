"""
模型处理器模块
功能：
- 实现不同大模型接口的调用适配
- 统一模型调用接口

包含：
- BaseModelHandler：模型处理器基类
- 各厂商模型的具体实现类

维护建议：
1. 新增模型时继承BaseModelHandler
2. API调用需包含错误处理
3. 注意不同模型的速率限制
"""

import aiohttp
import openai
from typing import List, Optional

from ..managers.user_manager import UserManager
from ..config import config, logger
from ..models import ConversationHistory

class BaseModelHandler:
    """模型处理器抽象基类"""
    async def generate(self, prompt: List, user_id: str) -> List:
        """
        生成回复的通用接口
        
        参数：
        - prompt: 完整提示词
        - history: 对话历史对象
        
        返回：
        - 模型生成的回复内容
        
        需子类实现具体逻辑
        """
        raise NotImplementedError("子类必须实现generate方法")

class OpenAIModelHandler(BaseModelHandler):
    """OpenAI系列模型处理器"""
    def __init__(self, model_name: str):
        self.client = openai.AsyncOpenAI(
            api_key=config.openai_api_key,
            base_url=config.openai_base_url
        )
        self.model_name = model_name

    async def generate(self, prompt: List, user_id: str) -> List:
        """调用OpenAI API生成回复"""
        try:
            temperature = UserManager().get_user_config(user_id)["temperature"]
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                temperature=temperature
            )
            return [response.choices[0].message.content, 1]
        except Exception as e:
            logger.error(f"OpenAI API错误: {str(e)}")
            return ["请求处理失败，请稍后再试", -1]

class DeepSeekModelHandler(BaseModelHandler):
    """DeepSeek模型处理器"""
    def __init__(self, model_name: str):
        self.client = openai.AsyncOpenAI(
            api_key=config.deepseek_api_key,
            base_url=config.deepseek_base_url
        )
        self.model_name = model_name

    async def generate(self, prompt: List, user_id: str) -> List:
        """调用DeepSeek API生成回复"""
        try:
            temperature = UserManager().get_user_config(user_id)["temperature"]
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=prompt,
                temperature=temperature
            )
            return [response.choices[0].message.content, 1]
        except Exception as e:
            logger.error(f"DeepSeek API错误: {str(e)}")
            return ["请求处理失败，请稍后再试", -1]

class DoubaoModelHandler(BaseModelHandler):
    """Doubao模型处理器（基于原生HTTP请求）"""
    def __init__(self, model_name: str):
        self.api_key = config.doubao_api_key
        self.model_name = model_name
        self.api_url = config.doubao_base_url

    async def generate(self, prompt: List, user_id: str) -> List:
        """调用Doubao原生API生成回复"""
        temperature = UserManager().get_user_config(user_id)["temperature"]
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model_name,
            "messages": prompt,
            "temperature": temperature
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        return [response_data['choices'][0]['message']['content'], 1]
                    else:
                        error_info = await response.text()
                        logger.error(f"API请求失败: {response.status} - {error_info}")
                        return ["服务暂时不可用，请稍后重试", -1]
        except aiohttp.ClientError as e:
            logger.error(f"网络请求异常: {str(e)}")
            return ["网络连接异常，请检查您的网络", -1]
        except Exception as e:
            logger.error(f"未知错误: {str(e)}")
            return ["服务处理异常，请联系管理员", -1]

# 示例：待实现的Claude处理器
class AnthropicModelHandler(BaseModelHandler):
    """Claude模型处理器（待实现）"""
    async def generate(self, prompt: str, history: ConversationHistory) -> List:
        # TODO: 实现具体逻辑
        return ["请求处理失败，请稍后再试", -1]