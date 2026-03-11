# -*- coding: utf-8 -*-
from dataclasses import dataclass, field


@dataclass
class Message:
    sender_uid: str
    sender_nickname: str
    content: str
    time: str           # 格式由服务器决定，直接存字符串
    is_self: bool       # 是否是自己发的

    def message_to_dict(self) -> dict:
        return {
            "sender_uid":       self.sender_uid,
            "sender_nickname":  self.sender_nickname,
            "content":          self.content,
            "time":             self.time,
            "is_self":          self.is_self,
        }

    @staticmethod
    def dict_to_message(d: dict) -> "Message":
        return Message(
            sender_uid=d["sender_uid"],
            sender_nickname=d["sender_nickname"],
            content=d["content"],
            time=d["time"],
            is_self=d["is_self"],
        )


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
