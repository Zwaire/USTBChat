def build_reply_prompt(scene: str, current_text: str, recent_text: str, max_chars: int = 80) -> str:
    return f"""你是聊天系统中的智能助手。
当前场景：{scene}

要求：
1. 只回答用户当前提问
2. 去掉称呼后直接回答
3. 用中文简洁回答
4. 不要解释思考过程
5. 不要输出多余客套话
6. 不超过{max_chars}个中文字符
7. 优先使用通用常识直接回答；仅在问题本身不完整时才说“我不确定”

最近消息：
{recent_text}

当前消息：
{current_text}
"""


def build_reply_rescue_prompt(current_text: str, max_chars: int = 80) -> str:
    return f"""你是聊天助手lulu。
请直接回答下面问题，尽量给出可执行建议。

要求：
1. 不要输出“信息不足”
2. 只输出答案本身
3. 中文回答
4. 不超过{max_chars}个中文字符

问题：
{current_text}
"""


def build_summary_prompt(scene: str, filename: str, content: str, max_chars: int = 140) -> str:
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
