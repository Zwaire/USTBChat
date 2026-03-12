# -*- coding: utf-8 -*-
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bin.state.AppState import AppState
from bin.state.ChatModels import Contact, Message

def format_msg_time(time_str: str) -> str:
    """
    将消息时间字符串格式化为显示文本。
    输入格式: "2025-03-12 14:30:00"
    返回:
      - 今天  → "14:30"
      - 昨天  → "昨天"
      - 更早  → "3月12日"
    """
    try:
        msg_dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return time_str

    delta = (datetime.today().date() - msg_dt.date()).days
    if delta == 0:
        return msg_dt.strftime("%H:%M")
    elif delta == 1:
        return "昨天"
    else:
        return f"{msg_dt.month}月{msg_dt.day}日"


def get_formatted_last_time(target_id: str) -> str:
    """返回某个会话最后一条消息的格式化时间字符串，供列表条目显示。"""
    for c in AppState().contacts:
        if c.id == target_id:
            return format_msg_time(c.last_time)
    return ""

def get_contact_list() -> list[Contact]:
    """返回当前登录用户的会话列表（已按最后消息时间排序）。"""
    contacts = AppState().contacts
    def sort_key(c: Contact):
        try:
            return datetime.strptime(c.last_time, "%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            return datetime.min
    return sorted(contacts, key=sort_key, reverse=True)


def get_chat_history(target_id: str) -> list[Message]:
    """
    打开某个会话，从本地加载历史记录并清除未读计数。
    返回该会话的全部消息列表。
    """
    return AppState().open_chat(target_id)