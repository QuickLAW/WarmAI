from nonebot import on_command
from nonebot.adapters.onebot.v11 import MessageEvent
from nonebot.rule import to_me
from nonebot.params import CommandArg, Arg
from nonebot.adapters import Message

from ..managers.user_manager import UserManager

# 注册ai命令处理器，响应格式：/ai <参数1> <参数2> ...
ai_matcher = on_command("warmai", aliases={"大鸽一号"}, priority=5, block=True)

@ai_matcher.handle()
async def ai_command_handler(
    event: MessageEvent,
    arg: Message = CommandArg(),
):
    user_id = event.get_user_id()
    # 提取纯文本参数并分割成列表
    args = arg.extract_plain_text().split()

    if args[0] == "personality" or args[0] == "system":
        """
        处理personality指令
        """
        user_config = UserManager().get_user_config(user_id)
        try:
            # 提取system指令的参数
            personality = args[1]
            new_config = user_config.copy()
            new_config["personality"] = personality
            UserManager().set_user_config(user_id, new_config)
            await ai_matcher.finish(f"已更新system指令参数为：{personality}")
            # 处理system指令的逻辑
        except IndexError:
            await ai_matcher.finish(f"当前的system指令参数为：{user_config["personality"]}")
    if args[0] == "clear":
        """
        处理clear指令
        """
        # 处理clear指令的逻辑
        UserManager().clear_user_conversation(user_id)
        await ai_matcher.finish("已清空你的对话历史")