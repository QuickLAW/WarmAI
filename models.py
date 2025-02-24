"""
数据模型定义
包含：
- ConversationHistory：用户对话历史数据结构
- 其他数据实体定义

维护建议：
1. 数据结构变更时需同步更新数据库结构
2. 保持与业务逻辑解耦
"""

import json
from pydantic import BaseModel, model_validator
from typing import List, Dict, Any, Optional, Union

class ConversationHistory(BaseModel):
    """
    用户对话历史记录模型（支持字符串初始化）
    
    属性：
    - messages: 消息列表，格式为 [{"role": "user/assistant", "content": "消息内容"}, ...]
    - personality: 当前使用的性格模板名称
    
    使用方式：
    1. 常规初始化：ConversationHistory(messages=[...], personality="...")
    2. 字符串初始化：ConversationHistory("包含完整数据的JSON字符串")
    """
    messages: List[Dict[str, str]] = []
    personality: str = "default"

    @model_validator(mode='before')
    @classmethod
    def validate_string_init(cls, data: Any) -> dict:
        """支持字符串初始化验证器"""
        if isinstance(data, str):
            try:
                # 尝试解析字符串为字典
                parsed = json.loads(data)
                if isinstance(parsed, dict):
                    return parsed
                # 兼容旧版纯消息列表格式
                if isinstance(parsed, list):
                    return {"messages": parsed, "personality": "default"}
            except json.JSONDecodeError:
                pass
        return data

    def add_message(
        self,
        message: Union['ConversationHistory', str, Dict[str, str]],
        content: Optional[str] = None
    ):
        """
        添加消息的增强方法（支持三种入参形式）
        
        参数形式：
        1. 添加单个消息（兼容旧版）: add_message(role, content)
        2. 添加消息字典: add_message({"role": "...", "content": "..."})
        3. 合并其他对话历史对象: add_message(other_conversation)
        """
        # 类型判断分支
        if isinstance(message, ConversationHistory):
            # 合并对话历史对象
            self._merge_conversation(message)
        elif isinstance(message, dict):
            # 添加消息字典
            self._add_message_dict(message)
        elif content is not None:
            # 添加角色+内容（旧版方式）
            self._add_single_message(str(message), content)
        else:
            raise TypeError("不支持的参数类型")

    def _add_single_message(self, role: str, content: str):
        """添加单个消息（原始实现）"""
        self.messages.append({"role": role, "content": content})

    def _add_message_dict(self, message_dict: Dict[str, str]):
        """添加消息字典"""
        if not all(k in message_dict for k in ("role", "content")):
            raise ValueError("消息字典必须包含 role 和 content 字段")
        self.messages.append(message_dict)

    def _merge_conversation(self, other: 'ConversationHistory'):
        """合并其他对话历史"""
        self.messages.extend(other.messages)
        # 可选：更新性格模板（根据业务需求）
        # self.personality = other.personality  

    def to_json(self) -> str:
        """
        序列化为完整JSON字符串（包含元数据）
        
        :return: 完整JSON字符串
        """
        return self.model_dump_json()

    def to_message_string(self) -> str:
        """
        仅序列化消息列表（兼容旧格式）
        
        :return: 消息列表的JSON字符串
        """
        return json.dumps(self.messages, ensure_ascii=False)
    
    def update(self, messages: List[Dict[str, str]], personality: str):
        """
        更新完整对话记录
        
        :param messages: 消息列表
        :param personality: 性格模板名称
        """
        self.messages = messages
        self.personality = personality

    def update_from_json(self, data: str):
        """
        从JSON字符串更新数据
        
        :param data: 完整JSON字符串
        """
        parsed = json.loads(data)
        # 使用Pydantic的模型验证机制
        new_obj = self.model_validate(parsed)
        self.messages = new_obj.messages
        self.personality = new_obj.personality