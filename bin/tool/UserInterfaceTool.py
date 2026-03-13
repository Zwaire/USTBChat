# -*- coding: utf-8 -*-
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import bin.tool.ContactTool as ct
from bin.state.ChatModels import Contact, Friend, Group, Message


class UserInterfaceTool:
    """
    负责处理与用户界面相关的逻辑，如格式化消息时间、获取会话列表、打开聊天等。
    这些函数通常会被UI层调用，以获取需要显示的数据或执行某些操作。
    """

    @classmethod
    def format_msg_time(cls,time_str: str) -> str:
        """
        将消息时间字符串格式化为显示文本。
        输入格式: "2025-03-12 14:30:00"
        返回: 今天→"14:30"  昨天→"昨天"  更早→"3月12日"
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

    # @classmethod
    # def get_contact_list(cls) -> list[Contact]:
    #     """返回当前登录用户的会话列表（按最后消息时间降序）。"""
    #     def sort_key(c: Contact):
    #         try:
    #             return datetime.strptime(c.last_time, "%Y-%m-%d %H:%M:%S")
    #         except (ValueError, TypeError):
    #             return datetime.min
    #     return sorted(ct.get_contacts(), key=sort_key, reverse=True)

    @classmethod
    def get_formatted_last_time(cls, target_id: str) -> str:
        """返回某个会话最后一条消息的格式化时间字符串。"""
        for c in ct.get_contacts():
            if c.id == target_id:
                return cls.format_msg_time(c.last_time)
        return ""


    @classmethod
    def open_chat(cls, target_id: str, is_group: bool | None = None) -> list[Message]:
        """
        打开某个会话：若内存中无历史则向服务器拉取，清除未读计数，返回消息列表。
        """
        history = ct.get_history(target_id, is_group)
        if not history:
            history = ct.fetch_history(target_id, is_group)
        else:
            ct._clear_unread(target_id, is_group)
        return history
