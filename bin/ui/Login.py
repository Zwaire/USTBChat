# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pathlib import Path
from PySide6.QtCore import Qt, Slot, QObject, Signal
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLayout, QSizePolicy, QLineEdit,
                               QStackedLayout, QMessageBox)
from PySide6.QtCore import Qt, Slot

from CommonCouple import TextInput, Button, ClassicLayout, Fonts
from bin.MessageFormat import LoginInfo
from bin.tool.LoginTool import LoginWindowTool as tool

# 导入改造好的 ChatClient ，引入全局状态单例
from core.network_client import ChatClient
from bin.state.AppState import AppState  # 【

# 定义一个信号类，用于安全地将子线程收到的网络消息抛给主线程 UI
class NetworkSignals(QObject):
    msg_received = Signal(dict)

class LoginWindow(QWidget):
    '''
    登录窗口, 继承自QWidget

    * 外观
    有登录和注册两种界面
    登录界面包含UID或昵称输入框和密码输入框
    注册界面包含昵称输入框、密码输入框和确认密码输入框
    包含登录注册模式切换按钮
    包含登录确认或注册确认按钮

    * 功能
    点击登录或注册按钮时按顺序执行以下操作:
    1. 获取所有输入框的内容并验证符号合法性(禁止非法字符、输入长度限制、字符种类要求)
    2. TCP连接服务器检查是否连接成功(是否超时)
    3. 打包用户输入的信息并向服务器发送请求
    4. 接收并处理服务器返回的信息
    5. 若要注册账户, 注册成功则提示并切换到登录界面, 注册失败仍要提示
    6. 若要登录账户, 登录成功则进入主界面, 否则提示错误
    '''

    def __init__(self):
        super().__init__()

        # 窗口属性设置
        self.setWindowTitle("登录")                # 窗口标题
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(600, 320)               # 窗口尺寸

        # 初始化网络模块
        self.signals = NetworkSignals()
        self.signals.msg_received.connect(self.handle_server_response)
        
        # 将ChatClient收到的消息通过信号发送到主线程
        self.client = ChatClient(callback=lambda msg: self.signals.msg_received.emit(msg))
        # 连接到服务器(用的本地服务器，这里写了本地回环地址)
        self.client.connect("127.0.0.1", 8888)

        self.initUI()

    def initUI(self):

        self.creWidgets()
        self.applyLayout()
        self.slotsConnect()

    def creWidgets(self):
        '''
        仅创建所有用到的组件, 不设置布局
        '''

        # UID或昵称(以下用ID代替)输入框-登录界面
        self.idInputerLogin = TextInput("账户: ", "请输入你的UID或昵称")
        self.idInputerLogin.setAlignment(ClassicLayout.Left)
        # ID输入框-注册界面
        self.idInputerRegister = TextInput("账       户: ", "请输入你的昵称")
        self.idInputerRegister.setAlignment(ClassicLayout.Left)

        # 密码输入框-登录界面
        self.pwdInputerLogin = TextInput("密码: ", "请输入密码", TextInput.Hidden)
        self.pwdInputerLogin.setAlignment(ClassicLayout.Left)
        # 密码输入框-注册界面
        self.pwdInputerRegister = TextInput("密       码: ", "请输入密码", TextInput.Hidden)
        self.pwdInputerRegister.setAlignment(ClassicLayout.Left)
        
        # 密码确认框
        self.pwdVerification = TextInput("确认密码: ", "再次输入相同的密码", TextInput.Hidden)
        self.pwdVerification.setAlignment(ClassicLayout.Left)

        # 大登录按钮
        self.loginButton = Button("登录", "信息填写完毕后, 点击该按钮即可登录")
        # 大注册按钮
        self.registerButton = Button("注册", "信息填写完毕后, 点击该按钮即可注册")
        # 小找回密码按钮-登录界面
        self.pwdFoundButtonLogin = Button("找回密码", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        # 小找回密码按钮-注册界面
        self.pwdFoundButtonRegister = Button("找回密码", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        # 小注册账户按钮
        self.regAccountButton = Button("注册账户", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        # 小登录账户按钮
        self.loginAccountButton = Button("登录账户", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))

        # 登录界面
        self.loginWindow = QWidget()
        self.loginWindow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.loginWindow.setFixedSize(600, 320)

        # 注册界面
        self.registerWindow = QWidget()
        self.registerWindow.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.registerWindow.setFixedSize(600, 320)

    def applyLayout(self):
        '''
        添加并设置布局
        '''

        # 主布局, 垂直布局
        self.mainLayout = ClassicLayout.Vertical(constr=ClassicLayout.Default, margins=ClassicLayout.NoBorder, spacing=10)

        # 找回密码与注册账户布局
        self.pnrLayout = ClassicLayout.Horizontal(constr=ClassicLayout.MinMax, margins=(80, 0, 80, 0), spacing=0)

        self.pnrLayout.addWidget(self.pwdFoundButtonLogin, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        self.pnrLayout.addStretch(1)
        self.pnrLayout.addWidget(self.regAccountButton, 0, alignment=Qt.AlignmentFlag.AlignRight)

        # 找回密码与登录账户布局
        self.pnlLayout = ClassicLayout.Horizontal(constr=ClassicLayout.MinMax, margins=(80, 0, 80, 0), spacing=0)

        self.pnlLayout.addWidget(self.pwdFoundButtonRegister, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        self.pnlLayout.addStretch(1)
        self.pnlLayout.addWidget(self.loginAccountButton, 0, alignment=Qt.AlignmentFlag.AlignRight)

        # 登录界面布局
        self.loginLayout = ClassicLayout.Vertical(align=ClassicLayout.CTop, constr=ClassicLayout.MinMax, margins=(80, 40, 80, 40), spacing=10)

        self.loginLayout.addLayout(self.idInputerLogin, 0)
        self.loginLayout.addLayout(self.pwdInputerLogin, 0)
        self.loginLayout.addLayout(self.pnrLayout, 0)
        self.loginLayout.addStretch(1)
        self.loginLayout.addWidget(self.loginButton, 0, alignment=ClassicLayout.CBottom)

        # 注册界面布局
        self.registerLayout = ClassicLayout.Vertical(align=ClassicLayout.CTop, constr=ClassicLayout.MinMax, margins=(60, 40, 60, 40), spacing=10)

        self.registerLayout.addLayout(self.idInputerRegister, 0)
        self.registerLayout.addLayout(self.pwdInputerRegister, 0)
        self.registerLayout.addLayout(self.pwdVerification, 0)
        self.registerLayout.addLayout(self.pnlLayout, 0)
        self.registerLayout.addStretch(1)
        self.registerLayout.addWidget(self.registerButton, 0, alignment=ClassicLayout.CBottom)

        # 切换布局, 用于切换登录界面和注册界面
        self.switchLayout = QStackedLayout()
        self.switchLayout.setSizeConstraint(ClassicLayout.MinMax)
        self.switchLayout.setContentsMargins(0, 0, 0, 0)
        self.switchLayout.setSpacing(0)
        
        self.loginWindow.setLayout(self.loginLayout)
        self.registerWindow.setLayout(self.registerLayout)

        self.switchLayout.addWidget(self.loginWindow)
        self.switchLayout.addWidget(self.registerWindow)

        # 应用至主布局
        self.mainLayout.addLayout(self.switchLayout, 1)

        self.setLayout(self.mainLayout)

    def slotsConnect(self):
        self.regAccountButton.clicked.connect(lambda checked: self.switchToRegister())
        self.loginAccountButton.clicked.connect(lambda checked: self.switchToLogin())
        self.pwdFoundButtonLogin.clicked.connect(lambda checked: self.findPassword())
        self.pwdFoundButtonRegister.clicked.connect(lambda checked: self.findPassword())
        self.loginButton.clicked.connect(lambda checked: self.loginAccount())
        self.registerButton.clicked.connect(lambda checked: self.registerAccount())

    def packLoginInfo(self) -> LoginInfo:
        '''
        打包当前界面用户输入的所有信息, 结果因
        '''

        mode = self.switchLayout.currentIndex()
        
        if mode == 0:
            # 登录界面
            id = self.idInputerLogin.getInput()
            password = self.pwdInputerLogin.getInput()
        
        else:
            # 注册界面
            id = self.idInputerRegister.getInput()
            password = self.pwdInputerRegister.getInput()
        
        return LoginInfo(mode, id, password)

    @Slot()
    def findPassword(self):
        '''
        找回密码按钮功能
        '''

        # 检查账号输入格式是否正确
        account = self.idInputerLogin.getInput() if self.switchLayout.currentIndex() == 0 else self.idInputerRegister.getInput()
        result = tool._validate_id(account)

        if result != True:
            #格式不正确, 警告
            self.warning(str(result))
            return

        # 获取ID, 向服务器发送找回密码请求
        try:
            serverReply =  tool._request_pwd_find(account)
        except:
            self.warning("网络错误")
            return
        
        # 解析服务器返回消息
        if serverReply['type'] != 'register':
            # 服务器出错， 返回的不是注册信息
            self.warning("服务器出错")
        
        if serverReply['status'] == 8:
            # 找回密码但用户名不存在
            self.warning("用户不存在")
        elif serverReply['status'] == 0:
            # 找回密码成功, 可直接登录
            self.warning("密码已重置, 可用任意密码登录")
        else:
            self.warning("服务器返回意料之外的状态码")
    
    def handle_server_response(self, msg: dict):
        '''
        用于处理从服务器返回的响应包 (此函数运行在主线程)
        '''
        msg_type = msg.get("type")
        status = msg.get("status")
        
        if msg_type == "register":
            if status == True:
                QMessageBox.information(self, "成功", "注册成功，请登录！")
                self.switchToLogin()
            else:
                self.warning(f"注册失败: {msg.get('warnings', '未知错误')}")
                
        elif msg_type == "login":
            if status == True:
                # 适配 AppState：登录成功后初始化全局状态和本地持久化目录
                uid = msg.get("uid", self.packLoginInfo().ID)
                nickname = msg.get("nickname", uid)
                friends = msg.get("friends", [])  # 服务器传来的好友列表
                groups = msg.get("groups", [])    # 服务器传来的群组列表
                
                # 初始化单例
                AppState().on_login(uid, nickname, friends, groups)

                QMessageBox.information(self, "成功", "登录成功！")
                self.enterMainInterface()
            else:
                self.warning(f"登录失败: {msg.get('warnings', '账号或密码错误')}")


    @Slot()
    def loginAccount(self) -> bool:
        '''
        点击登录按钮后的操作
        包括信息打包、输入验证、错误警告、密码加密、信息发送和服务器信息处理

        Returns:
            bool: 是否登录成功
        '''
        
        
        # 打包用户输入的信息
        info = self.packLoginInfo()

        # # 检查输入信息是否合法
        # result = tool._validate_id(info.ID)
        # if result != True:
        #     self.warning(str(result))
        #     return False
        
        # result = tool._validate_password(info.Password)
        # if result != True:
        #     self.warning(str(result))
        #     return False
        
        
        # 验证合法性
        if tool._validate_id(info.ID) != True or tool._validate_password(info.Password) != True:
            self.warning("账号或密码格式不正确")
            return False
            
        # 打包成 《通信接口.md》 规定的格式发送给服务器
        login_packet = {
            "type": "login",
            "username": info.ID,
            "code": info.Password,
            "ip": info.IP
        }
        
        if not self.client.send_data(login_packet):
            self.warning("无法连接到服务器！")
            return False
        return True
        
        # 向服务器发送登录信息
        # [CPD]
        # 添加了_send_login_info(info: LoginInfo) -> dict|bool函数接口，返回服务器的响应，目前正在等待传送实现，返回的是服务器的字典
        # <——————————————————————————————————————————————>
        # sendInfoToServer(info: LoginInfo) -> AnyType:
        # 提取LoginInfo类中的信息
        # 对密码进行加密
        # 将信息组合成可通过TCP传输的格式
        # 连接服务器, 发送信息
        # 接收服务器返回的消息
        # 返回值即服务器返回的消息， 若发送失败则返回False
        # <——————————————————————————————————————————————>

        # 服务器信息处理
        

    @Slot()
    def registerAccount(self):
        '''
        点击登录按钮后的操作
        包括密码验证、信息打包、输入验证、错误警告、信息发送和服务器消息处理
        '''

        # 检测两次输入的密码是否相同
        pwdF = self.pwdInputerRegister.getInput()
        pwdS = self.pwdVerification.getInput()

        if pwdF != pwdS:
            # 密码不同, 警告
            self.warning("两次密码输入不一致!")
            return False

        # 打包用户输入的信息
        info = self.packLoginInfo()

        # 检查输入信息是否合法
        result = tool._validate_id(info.ID)
        if result != True:
            self.warning(str(result))
            return
        
        if tool._is_uid(info.ID):
            self.warning("昵称不可为全数字")
            return
        
        result = tool._validate_password(info.Password)
        if result != True:
            self.warning(str(result))

        # 向服务器发送登录信息
        # sendInfoToServer()

        # 服务器信息处理

        # 构造注册报文并发送
        register_packet = {
            "type": "register",
            "username": info.ID,
            "code": info.Password,
            "ip": info.IP
        }
        
        if not self.client.send_data(register_packet):
            self.warning("无法连接到服务器！")
            return False

    def enterMainInterface(self):
        '''
        该函数仅在loginAccount函数返回True后执行
        实现登录成功后, 关闭登录界面, 打开主界面的功能
        '''

        # pass

        '''登录成功后，关闭登录界面，打开主界面'''
        # 注意：在此处实例化 MainWindow 时，应将 self.client 传递给它
        # 并在 MainWindow 中将 self.client.callback 重新指向 MainWindow 内部的方法
        # 以便在 MainWindow 中收到信息时调用 AppState().add_message()
        
        # 假设 MainWindow 已支持传入 client
        from bin.ui.UserInterface import MainWindow
        self.main_window = MainWindow(client=self.client) 
        self.main_window.show()
        self.close()

    def warning(self, text: str):
        '''
        输出警告信息

        Args:
            text(str): 警告信息内容

        Returns:
            None
        
        Raises:
            None
        '''

        QMessageBox.warning(self, "", text)
        return

    @Slot()
    def switchToRegister(self):
        self.switchLayout.setCurrentIndex(1)
        self.update()
    
    @Slot()
    def switchToLogin(self):
        self.switchLayout.setCurrentIndex(0)
        self.update()

if __name__ == '__main__':
    MMApp = QApplication(sys.argv)
    Window = LoginWindow()
    Window.show()
    MMApp.exec()

