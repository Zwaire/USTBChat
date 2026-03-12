def build_reply_prompt(chat_type: str, current_text: str, recent_text: str, max_chars: int = 80) -> str:
    scene = "私聊" if chat_type == "private" else "群聊"
    return f"""你是聊天系统中的智能助手。
当前场景：{scene}

要求：
1. 只回答用户当前提问
2. 去掉称呼后直接回答
3. 用中文简洁回答
4. 不要解释思考过程
5. 不要输出多余客套话
6. 不超过{max_chars}个中文字符
7. 如果信息不足，只输出：信息不足

最近消息：
{recent_text}

当前消息：
{current_text}
"""


def build_summary_prompt(chat_type: str, filename: str, content: str, max_chars: int = 140) -> str:
    scene = "私聊" if chat_type == "private" else "群聊"
    return f"""你是聊天系统中的智能助手。
当前场景：{scene}

请快速阅读文件并生成简短概要。

要求：
1. 只输出概要
2. 不加标题
3. 不解释过程
4. 不超过{max_chars}个中文字符
5. 优先概括主题、用途、核心内容
6. 如果内容过少，就尽量概括其主要信息

文件名：
{filename}

文件内容：
{content}
"""


def build_atmosphere_prompt(recent_text: str) -> str:
    return f"""请根据以下群聊最近消息判断当前群聊氛围。
只能从下面五个词中选择一个输出：

calm
angry
happy
sad
afraid

不要解释，不要输出其他内容。

最近消息：
{recent_text}
"""

