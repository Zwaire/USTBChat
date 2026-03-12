# -*- coding: utf-8 -*-
import os, sys, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bin.state.ChatModels import Contact, Friend, Group, Message

# ── 运行时状态 ────────────────────────────────────────────────
_client       = None          # ChatClient 实例
_uid: str     = ""
_nickname: str = ""
_friends:  dict[str, Friend]        = {}
_groups:   dict[str, Group]         = {}
_contacts: list[Contact]            = []
_chat_history: dict[str, list[Message]] = {}  # target_id -> 消息列表

# ── 状态访问 ──────────────────────────────────────────────────
def on_login(client, uid: str, nickname: str,
            friends: list[dict], groups: list[dict]):
    """
    登录成功后调用，初始化所有运行时状态。
    friends 格式: [{"uid": "10002", "nickname": "xjz"}, ...]
    groups  格式: [{"gid": "1",     "name": "group_1"}, ...]
    """
    global _client, _uid, _nickname
    _client   = client
    _uid      = uid
    _nickname = nickname
    _friends.clear()
    _groups.clear()
    _contacts.clear()
    _chat_history.clear()

    # for f in friends:
    #     _friends[f["uid"]] = Friend(f["uid"], f["nickname"])
    #     _contacts.append(Contact(id=f["uid"], name=f["nickname"], is_group=False))

    # for g in groups:
    #     _groups[g["gid"]] = Group(g["gid"], g["name"])
    #     _contacts.append(Contact(id=g["gid"], name=g["name"], is_group=True))

def get_client():
    return _client

def get_uid() -> str:
    return _uid

def get_nickname() -> str:
    return _nickname

def get_contacts() -> list[Contact]:
    return _contacts

def get_history(target_id: str) -> list[Message]:
    return _chat_history.get(target_id, [])

# ── 登录/登出 ─────────────────────────────────────────────────

def logout():
    global _client, _uid, _nickname
    _client   = None
    _uid      = ""
    _nickname = ""
    _friends.clear()
    _groups.clear()
    _contacts.clear()
    _chat_history.clear()

# ── 网络通信 ──────────────────────────────────────────────────

def _get_response(request: dict, timeout: float = 5.0) -> dict:
    """
    发送请求并阻塞等待第一条响应后返回。
    临时替换 client.callback 捕获响应，完成后恢复原回调。
    修复：获取原回调、健壮的回调恢复、严谨的客户端校验
    """
    # 严谨校验客户端：非空 + 运行中 + 存在callback属性
    if _client is None or not getattr(_client, "running", False) or not hasattr(_client, "callback"):
        return {}
    # 提前获取客户端原回调
    original_callback = _client.callback
    event = threading.Event()
    response_holder = {}

    def _temp_callback(msg: dict):
        """临时回调：捕获响应后触发事件，立即恢复原回调"""
        if isinstance(msg, dict):  # 防护：确保消息是字典格式
            response_holder.update(msg)
        event.set()
        # 回调内也做恢复：防止后续逻辑执行异常导致原回调未恢复
        if _client and _client.callback == _temp_callback:
            _client.callback = original_callback

    try:
        _client.callback = _temp_callback
        _client.send_data(request)
        event.wait(timeout)
    finally:
        if _client and _client.callback == _temp_callback:
            _client.callback = original_callback
    print(333333333)
    return response_holder

# ── 服务端请求接口 ────────────────────────────────────────────

def request_contacts_list() -> dict:
    """
    请求会话列表。 服务器应返回{ "type":"contacts_list","contacts":[...] # Contact 列表}
    """
    return dict(
        type="contacts_list",
        contacts=[Contact(id="1231", name="JohnDoe", is_group=False) ] +
                [Contact(id="g123", name="StudyGroup", is_group=True)]
    )
    # return _get_response({"type": "get_contacts_list", "username": _uid})

def request_friend_list() -> dict:
    """请求好友列表。服务器应返回 {"type":"friend_list","friends":[...] # Friend 列表}"""
    return dict(
        type="friend_list",
        friends=[Friend(uid="10001", nickname="Alice")] +
                [Friend(uid="10002", nickname="Bob")]
    )
    # return _get_response({"type": "get_friend_list", "username": _uid})

def request_group_list() -> dict:
    """
    请求群组列表。服务器应返回 
    {
        "type":"group_list",
        "groups":[...]  # Group 列表
    }
    """
    return dict(
        type="group_list",
        groups=[Group(gid="g123", name="Study Group")]
    )
    # return _get_response({"type": "get_group_list", "username": _uid})

def request_add_friend(target_uid: str) -> dict:
    """
    发送加好友请求。服务器应返回 
    {
        "type":"add_friend",
        "status":0 
    }
    """
    return _get_response({"type": "add_friend", "username": _uid, "target": target_uid})

def request_join_group(gid: str) -> dict:
    """
    发送加群请求。服务器应返回 
    {
        "type":"join_group",
        "status":0
    }
    """
    return _get_response({"type": "join_group", "username": _uid, "gid": gid})

def request_leave_group(gid: str) -> dict:
    """发送退群请求。服务器应返回 {"type":"leave_group","status":0}"""
    return _get_response({"type": "leave_group", "username": _uid, "gid": gid})

def request_group_members(gid: str) -> dict:
    """
    请求群成员列表。服务器应返回 
    {
        "type":"group_members",
        "gid":"...",
        "members":[...]
    }
    """
    return _get_response({"type": "get_group_members", "username": _uid, "gid": gid})

# ── 消息操作 ──────────────────────────────────────────────────

def fetch_history(target_id: str) -> list[Message]:
    """
    向服务器请求某个会话的全部历史记录，缓存到内存并返回。
    服务器应返回: {"type": "history", "target_id": "...", "messages": [...]}
    每条消息格式: {"sender_uid","sender_nickname","content","time","is_self"}
    """
    # 模拟数据
    return [
        Message(sender_uid="10002", sender_nickname="Bob", content="Hello!", time="2025-03-12 14:30:00", is_self=False),
        Message(sender_uid="10003", sender_nickname="Charlie", content="Hi Bob!", time="2025-03-12 14:31:00", is_self=True)
    ]

    # resp = _get_response({"type": "get_history", "target_id": target_id})
    # msgs = [_dict_to_message(d) for d in resp.get("messages", [])]
    # _chat_history[target_id] = msgs
    # _clear_unread(target_id)
    # return msgs

def send_message(target_id: str, content: str, is_group: bool = False) -> bool:
    """
    发送消息到服务器，同时追加到本地缓存。
    返回是否发送成功。
    """
    if _client is None or not _client.running:
        return False

    packet = {
        "type":    "group_message" if is_group else "message",
        "username":   _uid,
        "friendname": target_id,
        "message":    content,
    }
    ok = _client.send_data(packet)
    if ok:
        from datetime import datetime
        msg = Message(
            sender_uid=_uid,
            sender_nickname=_nickname,
            content=content,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_self=True,
        )
        _append_to_cache(target_id, msg)
    return ok

def on_message_received(msg_dict: dict):
    """
    网络层收到推送消息时调用（由 client.callback 触发）。
    msg_dict 格式: {"type":"message","username":"...","message":"...","time":"..."}
    """
    msg_type = msg_dict.get("type")
    if msg_type not in ("message", "group_message"):
        return

    target_id = msg_dict.get("username", "")
    msg = Message(
        sender_uid=target_id,
        sender_nickname=target_id,
        content=msg_dict.get("message", ""),
        time=msg_dict.get("time", ""),
        is_self=False,
    )
    _append_to_cache(target_id, msg)

# ── 内部工具 ──────────────────────────────────────────────────

def _append_to_cache(target_id: str, msg: Message):
    _chat_history.setdefault(target_id, []).append(msg)
    _update_contact(target_id, msg)

def _update_contact(target_id: str, msg: Message):
    for c in _contacts:
        if c.id == target_id:
            c.last_message = msg.content
            c.last_time    = msg.time
            if not msg.is_self:
                c.unread += 1
            break

def _clear_unread(target_id: str):
    for c in _contacts:
        if c.id == target_id:
            c.unread = 0
            break

def _dict_to_message(d: dict) -> Message:
    return Message(
        sender_uid=d["sender_uid"],
        sender_nickname=d["sender_nickname"],
        content=d["content"],
        time=d["time"],
        is_self=d["is_self"],
    )
