# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from pathlib import Path
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLayout, QSizePolicy, QLineEdit,
                               QStackedLayout, QMessageBox)
from PySide6.QtCore import Qt, Slot

from CommonCouple import TextInput, Button, ClassicLayout, Fonts
from bin.Message import LoginInfo

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
        # isValid()

        # 获取ID, 向服务器发送找回密码请求
        # [NTC]
        # <————————————————————————————————————>
        # requestPasswordRetrieve(id: str) -> AnyType:
        # 发送密码找回请求, 返回值是服务器的返回消息
        # <————————————————————————————————————>

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

        # 检查输入信息是否合法
        # [NTC]
        # <——————————————————————————————————————————————>
        # isValid(info: LoginInfo) -> bool:
        # LoginInfo类含有三个属性: Mode, ID, Password
        # Mode有0(代表登录), 1(代表注册)
        # 首先登录模式下ID可为UID或昵称
        # 注册模式下ID仅可为昵称, 昵称不能由纯数字组成(防止与UID混淆)
        # 检测密码格式是否合格
        # 返回一个布尔值, 表示输入信息是否有效
        # <——————————————————————————————————————————————>


        # 向服务器发送登录信息
        # [NTC]
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
        return False

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
        # isValid()

        # 向服务器发送登录信息
        # sendInfoToServer()

        # 服务器信息处理

    def enterMainInterface(self):
        '''
        该函数仅在loginAccount函数返回True后执行
        实现登录成功后, 关闭登录界面, 打开主界面的功能
        '''

        pass

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

