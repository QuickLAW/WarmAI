# 项目文档

---

## 概述
基于事件驱动的聊天机器人系统，支持多模型集成（OpenAI、DeepSeek、Doubao等）。核心模块包括对话管理、模型调度、数据库操作、用户配置管理，通过事件总线实现模块解耦。

---

## 核心模块说明

### 1. 对话管理 (`conversation_manager.py`)
- **类**: `ConversationManager`（单例）
- **功能**:
  - `get_history(user_id)`: 获取用户对话历史（返回`ConversationHistory`对象列表）
  - `add_new_conversation(user_id, new_conversation)`: 新增对话记录（SQL插入）
  - `update_conversation()`: 覆盖式更新对话（暂未完全实现）
  - `clear_conversation()`: 清空内存中的对话缓存
- **依赖**: `SQLiteManager`、`ConversationHistory`模型

---

### 2. 模型管理 (`model_manager.py`)
- **类**: `ModelManager`（单例）
- **功能**:
  - `process_message(user_id, message, time)`: 消息处理主流程（保存消息→构建提示词→调用模型→返回回复）
  - `_build_prompt()`: 构建带性格模板的提示词（保留最近N条历史）
- **模型处理器**:
  - 支持`gpt-3.5-turbo`、`gpt-4`、`deepseek`、`doubao`、`claude`（需配置API）
- **依赖**: `ConversationManager`、`UserManager`、`BaseModelHandler`

---

### 3. 数据库管理 (`sql_manager.py`)
- **类**: `SQLiteManager`（单例）
- **核心方法**:
  ```python
  create_table(table_name, columns)  # 建表
  insert(table_name, data)          # 插入数据
  query(table_name, where, params)  # 条件查询（返回字典列表）
  upsert()                          # 存在更新，不存在插入
  check_table_exists(table_name)    # 表存在性检查
  ```
- **特性**: 自动处理连接池，支持事务回滚

---

### 4. 用户管理 (`user_manager.py`)
- **类**: `UserManager`（单例）
- **方法**:
  - `get_user_config(user_id)`: 获取用户配置（不存在时创建默认配置）
- **默认配置字段**: `personality`（性格模板）、`temperature`（随机性）、`max_history_length`

---

### 5. 数据模型 (`models.py`)
- **核心模型**: `ConversationHistory`（对话历史）
  ```python
  user_id: str           # 用户ID (1-64字符)
  timestamp: int         # 时间戳（2000-2038年）
  message_content: str   # 消息内容（1-2000字符）
  is_recalled: bool      # 是否撤回
  is_ai: bool            # 是否为AI生成
  ```
- **方法**:
  - `to_dict()`: 转为普通字典
  - `to_db_dict()`: 转为数据库存储格式（布尔转0/1）

---

### 6. 事件总线 (`bus.py`)
- **核心类**:
  - `Event`: 事件基类（需继承使用）
  - `HandlerList`: 带优先级的事件处理器容器
- **关键装饰器**:
  ```python
  @Event.on(priority=数字)  # 注册事件处理器（优先级越高越早执行）
  ```
- **触发方式**:
  - `event.trigger()`: 同步触发
  - `event.async_trigger()`: 异步触发

---

### 7. 消息处理模块 (`messager_handlers.py`)
- **功能链**:
  1. `create_user_conversations_table`: 用户首次发言时自动建表
  2. `handle_private_message`: 调用`ModelManager`生成回复
  3. `update_user_conversations_table_for_ai_reply`: 保存AI回复到数据库
  4. `send_message`: 通过Matcher发送消息
- **事件绑定**:
  - `MessageReceivedEvent`: 消息接收事件（优先级5和10）
  - `MessageSentEvent`: 消息发送事件

---

### 8. 模型适配器 (`ai_handlers.py`)
- **基类**: `BaseModelHandler`
- **已实现处理器**:
  - `OpenAIModelHandler`: 支持GPT全系列模型
  - `DeepSeekModelHandler`: 深度求索模型
  - `DoubaoModelHandler`: 字节豆包模型（原生HTTP实现）
  - `AnthropicModelHandler`: Claude模型（待实现）
- **统一接口**:
  ```python
  async def generate(prompt, user_id) -> [response_str, status_code]
  ```

---

## 数据表结构
| 表名                    | 字段                          | 说明                |
|-------------------------|-------------------------------|--------------------|
| `<user_id>_conversations` | user_id, timestamp, message_content, is_recalled, is_ai | 用户对话历史表      |
| `user_config`           | user_id, personality, temperature, max_history_length   | 用户配置表（需配置）|

---

## 关键配置项 (`config.py`)
```python
# 数据库
db_path = "data/chatbot.db"  
db_user_conversations_table_columns = [
    "user_id TEXT NOT NULL",
    "timestamp INTEGER NOT NULL",
    "message_content TEXT NOT NULL",
    "is_recalled INTEGER DEFAULT 0",
    "is_ai INTEGER DEFAULT 0"
]

# 模型默认值
default_model = "gpt-3.5-turbo"
personality_default = "你是一个乐于助人的AI助手"
temperature = 0.7
max_history_length = 10

# API密钥（需外部注入）
openai_api_key = os.getenv("OPENAI_KEY")
deepseek_api_key = os.getenv("DEEPSEEK_KEY")
```

---

## 扩展指南
1. **新增模型**:
   - 继承`BaseModelHandler`，实现`generate()`方法
   - 在`ModelManager._init_handlers()`注册处理器

2. **新增事件**:
   - 创建继承自`Event`的子类（如`PaymentReceivedEvent`）
   - 使用`@YourEvent.on()`装饰器绑定处理函数

3. **修改对话逻辑**:
   - 调整`_build_prompt()`中的提示词构建策略
   - 修改`ConversationHistory`模型字段（需同步数据库迁移）