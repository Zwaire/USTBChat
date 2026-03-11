# -*- coding: utf-8 -*-
from bin.state.models import Friend, Group, Message, Contact
import bin.state.MessageStore as store


class AppState:
    """
    全局运行时状态单例。
    登录成功后由网络层填充，UI层只读取，不直接修改。
    聊天记录持久化到本地 JSON 文件，好友/群组列表内存+本地双份。

    类实现了登录状态的管理，提供了登录后初始化、消息操作、好友/群组操作等方法。
    其中消息操作包括打开聊天窗口加载历史记录、添加新消息（更新本地和内存）、获取历史记录等；好友/群组操作包括添加好友/群组、更新会话列表预览等。
    内部工具方法用于获取最后一条消息更新会话预览等
    """

    _instance: "AppState | None" = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        self.uid: str = ""
        self.nickname: str = ""
        self.friends: dict[str, Friend] = {}
        self.groups: dict[str, Group] = {}
        self.chat_history: dict[str, list[Message]] = {}   # 内存缓存
        self.contacts: list[Contact] = []
        self.server_ip: str = ""
        self.server_port: int = 0

    # ── 登录后初始化 ──────────────────────────────────────────

    def on_login(self, uid: str, nickname: str,
                 friends: list[dict], groups: list[dict]):
        """
        登录成功后由网络层调用。
        同时将好友/群组列表缓存到本地，并从本地加载各会话最后一条消息。

        friends 格式: [{"uid": "10002", "nickname": "xjz"}, ...]
        groups  格式: [{"gid": "1",     "name": "group_1"}, ...]
        """
        self.uid = uid
        self.nickname = nickname
        self.friends.clear()
        self.groups.clear()
        self.contacts.clear()

        for f in friends:
            self.friends[f["uid"]] = Friend(f["uid"], f["nickname"])
            last = self._last_message(f["uid"])
            self.contacts.append(Contact(
                id=f["uid"], name=f["nickname"], is_group=False,
                last_message=last.content if last else "",
                last_time=last.time if last else "",
            ))

        for g in groups:
            self.groups[g["gid"]] = Group(g["gid"], g["name"])
            last = self._last_message(g["gid"])
            self.contacts.append(Contact(
                id=g["gid"], name=g["name"], is_group=True,
                last_message=last.content if last else "",
                last_time=last.time if last else "",
            ))

        # 本地持久化好友/群组列表（断线时可降级使用）
        store.save_contacts(uid, "friends", friends)
        store.save_contacts(uid, "groups", groups)

    # ── 消息操作 ──────────────────────────────────────────────

    def open_chat(self, target_id: str) -> list[Message]:
        """
        打开某个聊天窗口时调用，从本地加载历史记录到内存缓存并返回。
        """
        if target_id not in self.chat_history:
            self.chat_history[target_id] = store.load_history(self.uid, target_id)
        self.clear_unread(target_id)
        return self.chat_history[target_id]

    def add_message(self, target_id: str, msg: Message):
        """
        收到或发出新消息时调用：写入本地文件 + 更新内存缓存 + 刷新会话列表。
        """
        # 持久化
        store.append_message(self.uid, target_id, msg)

        # 内存缓存（仅在已打开该会话时才维护，避免无谓占用内存）
        if target_id in self.chat_history:
            self.chat_history[target_id].append(msg)

        self._update_contact(target_id, msg)

    def get_history(self, target_id: str) -> list[Message]:
        """返回内存中的历史记录，需先调用 open_chat 加载。"""
        return self.chat_history.get(target_id, [])

    # ── 好友/群组操作 ─────────────────────────────────────────

    def add_friend(self, uid: str, nickname: str):
        self.friends[uid] = Friend(uid, nickname)
        self.contacts.append(Contact(id=uid, name=nickname, is_group=False))
        store.save_contacts(self.uid, "friends",
                            [{"uid": f.uid, "nickname": f.nickname}
                             for f in self.friends.values()])

    def add_group(self, gid: str, name: str):
        self.groups[gid] = Group(gid, name)
        self.contacts.append(Contact(id=gid, name=name, is_group=True))
        store.save_contacts(self.uid, "groups",
                            [{"gid": g.gid, "name": g.name}
                             for g in self.groups.values()])

    # ── 内部工具 ──────────────────────────────────────────────

    def _last_message(self, target_id: str) -> "Message | None":
        """从本地文件读取最后一条消息，用于填充会话列表预览。"""
        history = store.load_history(self.uid, target_id)
        return history[-1] if history else None

    def _update_contact(self, target_id: str, msg: Message):
        for c in self.contacts:
            if c.id == target_id:
                c.last_message = msg.content
                c.last_time = msg.time
                if not msg.is_self:
                    c.unread += 1
                break
    
    def clear_unread(self, target_id: str):
        for c in self.contacts:
            if c.id == target_id:
                c.unread = 0
                break

    def logout(self):
        self._init()
