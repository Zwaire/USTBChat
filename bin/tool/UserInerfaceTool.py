# -*- coding: utf-8 -*-
from datetime import datetime
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
