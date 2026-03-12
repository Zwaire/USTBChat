# -*- coding: utf-8 -*-
from dataclasses import dataclass, field


@dataclass
class Message:
    '''
    Message类表示一条消息，包含发送者信息、内容、时间等属性，如下所示
    sender_uid: str       # 发送者的用户ID，字符串类型
    sender_nickname: str  # 发送者的昵称，字符串类型
    content: str         # 消息内容，字符串类型
    time: str            # 消息发送时间，字符串类型，格式由服务器决定
    is_self: bool        # 是否是自己发的消息，布尔类型
    '''
    sender_uid: str
    sender_nickname: str
    content: str
    time: str           # 格式由服务器决定，直接存字符串
    is_self: bool       # 是否是自己发的

@dataclass
class Contact:
    """好友或群组的统一抽象，用于左侧会话列表"""
    id: str             # 好友uid 或 群组gid
    name: str           # 昵称或群名
    is_group: bool
    last_message: str = ""
    last_time: str = ""
    unread: int = 0

class ChatTool:

    @staticmethod
    def message_to_dict(m: Message) -> dict:
        return {
            "sender_uid":       m.sender_uid,
            "sender_nickname":  m.sender_nickname,
            "content":          m.content,
            "time":             m.time,
            "is_self":          m.is_self,
        }

    @staticmethod
    def dict_to_message(d: dict) -> Message:
        return Message(
            sender_uid=d["sender_uid"],
            sender_nickname=d["sender_nickname"],
            content=d["content"],
            time=d["time"],
            is_self=d["is_self"],
        )

    @staticmethod
    def contact_to_dict(c: Contact) ->dict:
        return {
            'id': c.id,
            'name': c.name,
            'is_group': c.is_group,
            'last_message': c.last_message,
            'last_time': c.last_time,
            'unread': c.unread
        }

    @staticmethod
    def dict_to_contact(d: dict) -> Contact:
        return Contact(
            id=d['id'],
            name=d['name'],
            is_group=d['is_group'],
            last_message=d['last_message'],
            last_time=d['last_time'],
            unread=d['unread']
        )
    
@dataclass
class Friend:
    uid: str
    nickname: str


@dataclass
class Group:
    gid: str
    name: str
    members: list = field(default_factory=list)  # list[str] uid列表，可选
