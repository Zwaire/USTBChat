# -*- coding: utf-8 -*-
import os
import sys
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

from bin.state.ChatModels import Message
from bin.ui.Login import LoginWindow
from bin.ui.Themes import Theme
from bin.ui.UserInterface import MainWindow
import bin.tool.ContactTool as ContactTool
from core.network_client import ChatClient


class NetworkSignals(QObject):
    msg_received = Signal(dict)


_main_window: Optional[MainWindow] = None


class USTBChatClient:
    def __init__(self, app: QApplication):
        self.app = app
        self.login_window: Optional[LoginWindow] = None
        self.chat_client: Optional[ChatClient] = None

        self.signals = NetworkSignals()
        self.signals.msg_received.connect(self.handle_server_response)

        # self.chat_client = ChatClient(callback=lambda msg: self.signals.msg_received.emit(msg))
        self.chat_client = ChatClient(callback=lambda msg: (self.signals.msg_received.emit(msg), print(f"收到消息: {msg}")))

        host = os.environ.get("USTBCHAT_CLIENT_SERVER_HOST") or os.environ.get("USTBCHAT_SERVER_HOST", "127.0.0.1")
        if host == "0.0.0.0":
            host = "127.0.0.1"
        port = int(os.environ.get("USTBCHAT_CLIENT_SERVER_PORT") or os.environ.get("USTBCHAT_SERVER_PORT", "8888"))

        ContactTool.on_login(self.chat_client, "", "", [], [])

        self.login_window = LoginWindow(default_server_host=host, default_server_port=port)
        self.login_window.iLoveLinux.connect(lambda uid, name: self._on_login_success(uid, name))

    def _on_login_success(self, uid: str, name: str):
        global _main_window

        if self.login_window:
            self.login_window.close()

        ContactTool.on_login(self.chat_client, uid, name, [], [])

        _main_window = MainWindow(uid, name)
        _main_window.show()

    def _convert_server_msg_to_model(self, msg: dict):
        msg_type = msg.get("type")

        if msg_type in ("message", "file_message"):
            chat_uid = msg.get("friendid") or msg.get("username") or msg.get("friendname")
            if not chat_uid:
                return None, None, False

            if msg_type == "file_message":
                filename = msg.get("filename") or "文件"
                content = msg.get("content") or ""
                text = f"[文件] {filename}\n{content}"
            else:
                text = msg.get("message") or ""

            model = Message(
                sender_uid=str(msg.get("friendid") or msg.get("username") or ""),
                sender_nickname=str(msg.get("username") or msg.get("friendname") or ""),
                content=str(text),
                time=str(msg.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                is_self=False,
            )
            return str(chat_uid), model, False

        if msg_type in ("group_message", "group_file_message"):
            chat_uid = msg.get("groupid") or msg.get("groupname")
            if not chat_uid:
                return None, None, True

            if msg_type == "group_file_message":
                filename = msg.get("filename") or "文件"
                content = msg.get("content") or ""
                text = f"[文件] {filename}\n{content}"
            else:
                text = msg.get("groupmessage") or msg.get("message") or ""

            model = Message(
                sender_uid=str(msg.get("username") or ""),
                sender_nickname=str(msg.get("username") or ""),
                content=str(text),
                time=str(msg.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                is_self=False,
            )
            return str(chat_uid), model, True

        return None, None, False

    def handle_server_response(self, msg: dict):
        if not msg or not isinstance(msg, dict):
            return

        if _main_window is None:
            return

        chat_uid, model, is_group = self._convert_server_msg_to_model(msg)
        if not chat_uid or model is None:
            return

        try:
            _main_window.onReceivedMessage(chat_uid, model, is_group)
        except Exception:
            pass

    def start(self):
        if self.login_window:
            self.login_window.show()
        self.app.aboutToQuit.connect(self._on_app_quit)
        sys.exit(self.app.exec())

    def _on_app_quit(self):
        if self.chat_client:
            self.chat_client.disconnect()
        print("Client Quit!")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Theme.Normal)
    client = USTBChatClient(app)
    client.start()
