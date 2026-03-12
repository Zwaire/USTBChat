# 11-*- coding: utf-8 -*-
from dataclasses import dataclass, field


@dataclass
class Message:
    '''
    Message类表示一条消息，包含发送者信息、内容、时间等属性，如下所示
    sender_uid: str       # 发送者的用户ID，字符串类型
    sender_nickname: str  # 发送者的昵称，字符串类型
    content: str         # 消息内容，字符串类型
    time: str            # 消息发送时间，时间格式为"2025-03-12 14:30:00"这样的类似的字符串
    is_self: bool        # 是否是自己发的消息，布尔类型
    '''
    sender_uid: str
    sender_nickname: str
    content: str
    time: str           
    is_self: bool      

@dataclass
class Contact:
    """好友或群组的统一抽象，用于左侧会话列表"""
    id: str             # 好友uid 或 群组gid
    name: str           # 昵称或群名
    is_group: bool
    last_message: str = ""
    last_time: str = ""
    unread: int = 0
    
@dataclass
class Friend:
    uid: str
    nickname: str

@dataclass
class Group:
    gid: str
    name: str
    members: list = field(default_factory=list)  # list[str] uid列表，可选
