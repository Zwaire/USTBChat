# -*- coding: utf-8 -*-
import os
import sys
from typing import Optional
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bin.ui.Login import LoginWindow
from bin.ui.UserInterface import MainWindow
from core.network_client import ChatClient
import bin.tool.ContactTool as ContactTool
from bin.ui.Themes import Theme

class NetworkSignals(QObject):
    msg_received = Signal(dict)

# 全局主窗口引用：防止被Python垃圾回收销毁
_main_window: Optional[MainWindow] = None

class USTBChatClient:
    def __init__(self, app: QApplication):
        """类初始化：一次性完成网络、信号、界面、工具类的初始化"""
        self.app = app 
        self.running = False
        self.login_window: Optional[LoginWindow] = None  
        self.chat_client: Optional[ChatClient] = None    

        self.signals = NetworkSignals()
        self.signals.msg_received.connect(self.handle_server_response)
        self.chat_client = ChatClient(callback=lambda msg: self.signals.msg_received.emit(msg), t=self.handle_server_response)
        is_connected = self.chat_client.connect("127.0.0.1", 8888)
        if not is_connected:
            print("NetworkError")
        else:
            print("Connected!")
        ContactTool.on_login(self.chat_client, "", "", [], [])

        self.login_window = LoginWindow()
        self.login_window.iLoveLinux.connect(lambda uid, name: self._on_login_success(uid, name))
        # self.login_window.enterMainInterface = self._on_login_success

    def _on_login_success(self, uid: str, name: str):
        global _main_window
        # 关闭登录窗口，打开主界面
        if self.login_window:
            self.login_window.close()
        # print("UID: ", uid)
        ContactTool._nickname, ContactTool._uid = name, uid
        _main_window = MainWindow(uid, name)
        _main_window.show()

    # def recvServer(self, targetFunction):

    #     while self.running:
    #         try:
    #             self.chat_client.recv


    def handle_server_response(self, msg: dict):
        '''
        处理传递的消息，此处的消息类别只有Message和group_message两种
        '''

        print(msg)

        if not msg or not isinstance(msg, dict):
            return
        
        chat_uid = msg.get('friendid') or msg.get('groupid')
        if not chat_uid:
            print('Not Usefull ID, ignore ', msg)
            return 
        if _main_window is None:
            return 

        try:
            _main_window.onReceivedMessage(chat_uid, msg)
        except KeyError as e:
            print("KeyError")

    def start(self):
        if self.login_window:
            self.login_window.show()
        self.app.aboutToQuit.connect(self._on_app_quit)
        sys.exit(self.app.exec())

    def _on_app_quit(self):
        if self.chat_client:
            self.chat_client.disconnect()
        print("Client Quit!")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyleSheet(Theme.Normal)
    client = USTBChatClient(app)
    # 启动客户端
    client.start()