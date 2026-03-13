# -*- coding: utf-8 -*-
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from bin.state.ChatModels import Contact, Friend, Group, Message


_client = None
_uid: str = ""
_nickname: str = ""
_friends: dict[str, Friend] = {}
_groups: dict[str, Group] = {}
_contacts: list[Contact] = []
_chat_history: dict[str, list[Message]] = {}


def _history_key(target_id: str, is_group: bool | None = None) -> str:
    target_id = str(target_id or "")
    if is_group is None:
        return target_id
    return f"{'g' if is_group else 'u'}:{target_id}"


def on_login(client, uid: str, nickname: str, friends: list[dict], groups: list[dict]):
    global _client, _uid, _nickname
    _client = client
    _uid = str(uid or "")
    _nickname = str(nickname or "")

    _friends.clear()
    _groups.clear()
    _contacts.clear()
    _chat_history.clear()

    for f in friends or []:
        friend = Friend(uid=str(f.get("uid", "")), nickname=str(f.get("nickname", "")))
        _friends[friend.uid] = friend
        _contacts.append(Contact(id=friend.uid, name=friend.nickname, is_group=False))

    for g in groups or []:
        group = Group(gid=str(g.get("gid", "")), name=str(g.get("name", "")))
        _groups[group.gid] = group
        _contacts.append(Contact(id=group.gid, name=group.name, is_group=True))


def get_client():
    return _client


def get_uid() -> str:
    return _uid


def get_nickname() -> str:
    return _nickname


def get_contacts() -> list[Contact]:
    return _contacts


def get_history(target_id: str, is_group: bool | None = None) -> list[Message]:
    key = _history_key(target_id, is_group)
    return _chat_history.get(key, [])


def logout():
    global _client, _uid, _nickname
    _client = None
    _uid = ""
    _nickname = ""

    _friends.clear()
    _groups.clear()
    _contacts.clear()
    _chat_history.clear()


def _get_response(request: dict, timeout: float = 5.0) -> dict:
    if _client is None or not getattr(_client, "running", False) or not hasattr(_client, "callback"):
        return {}

    original_callback = _client.callback
    event = threading.Event()
    response_holder = {}

    async_push_types = {"message", "group_message", "file_message", "group_file_message", "system"}

    def _temp_callback(msg: dict):
        if not isinstance(msg, dict):
            return

        msg_type = msg.get("type")
        if msg_type in async_push_types:
            try:
                original_callback(msg)
            except Exception:
                pass
            return

        response_holder.update(msg)
        event.set()

    try:
        _client.callback = _temp_callback
        _client.send_data(request)
        event.wait(timeout)
    finally:
        if _client:
            _client.callback = original_callback

    return response_holder


def request_contacts_list() -> dict:
    return _get_response({"type": "get_contacts_list", "username": _nickname})


def request_friend_list() -> dict:
    return _get_response({"type": "get_friend_list", "username": _nickname})


def request_group_list() -> dict:
    return _get_response({"type": "get_group_list", "username": _nickname})


def request_add_friend(target_name: str) -> dict:
    return _get_response(
        {
            "type": "add_friend",
            "username": _nickname,
            "friendname": str(target_name),
            "target": str(target_name),
        }
    )


def request_join_group(gid: str) -> dict:
    return _get_response(
        {
            "type": "join_group",
            "username": _nickname,
            "gid": str(gid),
            "groupname": str(gid),
        }
    )


def request_leave_group(gid: str) -> dict:
    return _get_response(
        {
            "type": "leave_group",
            "username": _nickname,
            "gid": str(gid),
            "groupname": str(gid),
        }
    )


def request_group_members(gid: str) -> dict:
    return _get_response(
        {
            "type": "get_group_members",
            "username": _nickname,
            "gid": str(gid),
            "groupname": str(gid),
        }
    )


def request_group_atmosphere(gid: str) -> dict:
    return _get_response(
        {
            "type": "get_group_atmosphere",
            "username": _nickname,
            "gid": str(gid),
            "groupname": str(gid),
        }
    )


def request_create_group(group_name: str, uids: list[str], with_ai: bool = False) -> dict:
    group_name = str(group_name or "").strip()
    if not group_name:
        return {"type": "create_group", "status": -1, "msg": "群名不能为空"}

    payload = {
        "type": "create_group",
        "username": _nickname,
        "groupname": group_name,
        "group_name": group_name,
        "uids": [str(x) for x in (uids or []) if str(x).strip()],
        "with_ai": bool(with_ai),
    }
    return _get_response(payload)


def fetch_history(target_id: str, is_group: bool | None = None) -> list[Message]:
    target_id = str(target_id)
    key = _history_key(target_id, is_group)
    resp = _get_response(
        {
            "type": "get_history",
            "username": _nickname,
            "target": target_id,
            "target_id": target_id,
            "is_group": is_group,
        }
    )

    msgs = [_dict_to_message(d) for d in resp.get("messages", [])]
    _chat_history[key] = msgs
    _clear_unread(target_id, is_group)
    return msgs


def send_message(target_id: str, content: str, is_group: bool = False) -> bool:
    if _client is None or not getattr(_client, "running", False):
        return False

    target_id = str(target_id)
    content = str(content)

    if is_group:
        packet = {
            "type": "group_message",
            "username": _nickname,
            "groupname": target_id,
            "groupid": target_id,
            "groupmessage": content,
            "message": content,
        }
    else:
        packet = {
            "type": "message",
            "username": _nickname,
            "friendname": target_id,
            "friendid": target_id,
            "message": content,
        }

    return _client.send_data(packet)


def _append_to_cache(target_id: str, msg: Message, is_group: bool | None = None):
    target_id = str(target_id)
    key = _history_key(target_id, is_group)
    _chat_history.setdefault(key, []).append(msg)
    _update_contact(target_id, msg, is_group)


def _update_contact(target_id: str, msg: Message, is_group: bool | None = None):
    for c in _contacts:
        if c.id == target_id and (is_group is None or c.is_group == bool(is_group)):
            c.last_message = msg.content
            c.last_time = msg.time
            if not msg.is_self:
                c.unread += 1
            break


def _clear_unread(target_id: str, is_group: bool | None = None):
    for c in _contacts:
        if c.id == target_id and (is_group is None or c.is_group == bool(is_group)):
            c.unread = 0
            break


def _dict_to_message(d: dict) -> Message:
    sender_uid = str(d.get("sender_uid") or d.get("username") or d.get("sender_name") or "")
    sender_nickname = str(
        d.get("sender_nickname")
        or d.get("sender_name")
        or d.get("username")
        or sender_uid
    )
    content = str(d.get("content") or d.get("message") or d.get("groupmessage") or "")
    time = str(d.get("time") or "")

    raw_is_self = d.get("is_self")
    if isinstance(raw_is_self, bool):
        is_self = raw_is_self
    else:
        is_self = sender_uid == _uid or sender_nickname == _nickname

    return Message(
        sender_uid=sender_uid,
        sender_nickname=sender_nickname,
        content=content,
        time=time,
        is_self=is_self,
    )
