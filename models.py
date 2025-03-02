from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import List
import json

class ConversationHistory(BaseModel):
    """
    严格手动初始化的对话消息模型
    
    属性（全部必须显式指定）：
    user_id: str = 用户标识（1-64字符）
    timestamp: int = 秒级时间戳（2000-2038年间）
    message_content: str = 消息内容（1-2000字符）
    is_recalled: bool = 是否撤回
    """
    user_id: str = Field(
        ..., 
        min_length=1,
        max_length=64,
        description="必须提供用户ID"
    )
    timestamp: int = Field(
        ...,
        ge=946684800,  # 2000-01-01
        le=2147483647,  # 2038年上限
        description="必须提供有效时间戳"
    )
    message_content: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="必须提供消息内容"
    )
    is_recalled: bool = Field(
        ...,
        description="必须明确指定撤回状态"
    )
    is_ai: bool = Field(
       ...,
        description="必须明确指定是否为AI消息" 
    )

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v: int) -> int:
        """二次验证时间戳合理性"""
        if v > int(datetime.now().timestamp()) + 86400:
            raise ValueError("时间戳不能超过未来24小时")
        return v

    def to_dict(self) -> dict:
        """转换为数据库存储格式"""
        return self.model_dump()

    def to_conversation(self) -> str:
        """转换为对话格式"""
        strftime = datetime.fromtimestamp(self.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        is_recalled = "此条消息已撤回" if self.is_recalled else ""
        return f"{strftime}, {is_recalled}: {self.message_content}"
    
    def to_db_dict(self) -> dict:
        """转换为数据库存储格式"""
        export_dict = self.model_dump()
        export_dict["is_recalled"] = int(export_dict["is_recalled"])
        export_dict["is_ai"] = int(export_dict["is_ai"])
        return export_dict
    
    def from_db_dict(self, db_dict: dict):
        """从数据库字典加载数据"""
        self.user_id = db_dict["user_id"]
        self.timestamp = db_dict["timestamp"]
        self.message_content = db_dict["message_content"]
        self.is_recalled = bool(db_dict["is_recalled"])
        self.is_ai = bool(db_dict["is_ai"])

        

# 使用示例
if __name__ == "__main__":
    # 正确的手动初始化
    msg1 = ConversationHistory(
        user_id="u123",
        timestamp=1695100000,
        message_content="手动指定内容",
        is_recalled=False,
        is_ai=False
    )


    # 从数据库记录加载
    db_data = {
        "user_id": "u456",
        "timestamp": 1695200000,
        "message_content": "数据库加载内容",
        "is_recalled": True,
        "is_ai": False
    }
    print(msg1.to_dict())