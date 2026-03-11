# -*- coding: utf-8 -*-
import json
import os
import sys
# sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ChatModels import Message

# 本地数据根目录
_DATA_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "data", "users")


def _chat_path(uid: str, target_id: str) -> str:
    return os.path.join(_DATA_ROOT, uid, "chat", f"{target_id}.json")

def _contacts_path(uid: str, kind: str) -> str:
    """kind: 'friends' 或 'groups'"""
    return os.path.join(_DATA_ROOT, uid, f"{kind}.json")


# ── 聊天记录 ──────────────────────────────────────────────────

def load_history(uid: str, target_id: str) -> list[Message]:
    """从本地读取与 target_id 的全部聊天记录。"""
    path = _chat_path(uid, target_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return [Message.dict_to_message(d) for d in json.load(f)]


def append_message(uid: str, target_id: str, msg: Message):
    """追加一条消息到本地文件（增量写入，不重写全部）。"""
    path = _chat_path(uid, target_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    # 读取已有内容再追加，保持文件是完整的 JSON 数组
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = []

    data.append(msg.message_to_dict())
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── 好友 / 群组列表本地缓存 ───────────────────────────────────

def save_contacts(uid: str, kind: str, contacts: list[dict]):
    """
    保存好友或群组列表到本地。
    kind = 'friends' 时 contacts 格式: [{"uid":..., "nickname":...}, ...]
    kind = 'groups'  时 contacts 格式: [{"gid":..., "name":...}, ...]
    """
    path = _contacts_path(uid, kind)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(contacts, f, ensure_ascii=False, indent=2)


def load_contacts(uid: str, kind: str) -> list[dict]:
    """读取本地缓存的好友或群组列表，服务器不可达时作为降级数据。"""
    path = _contacts_path(uid, kind)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
