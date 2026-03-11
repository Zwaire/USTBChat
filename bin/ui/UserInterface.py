# -*- coding: utf-8 -*-

'''
用户界面
登录成功后的主界面
包括群聊、私信、文件传输等功能
'''

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLayout,
                               QSizePolicy, QLineEdit, QMessageBox, QMainWindow, QScrollArea, QPlainTextEdit)
from PySide6.QtCore import Qt, Slot
from CommonCouple import Section, Fonts, Button, ClassicLayout, Separator

class MainWindow(QWidget):
    '''
    主界面, 继承自QWidget

    * 外观
    整体分为左中右结构
    <————————————————左半边————————————————>
    分为上中下结构
    最上方为个人栏, 显示昵称与UID, 右键可实现诸多功能, 例如修改昵称、添加好友、发起群聊、加入群聊、查看消息
    中间为一行按钮, 用于选择聊天对象列表, 有消息列表、好友列表和群聊列表
    最下方为对应的聊天对象列表, 拥有滑块
    -------------
    |ID & UID   |
    -------------
    |  N  F  P  |
    -------------
    |TalkObject1|
    |TalkObject2|
    |TalkObject3|
    |...........|
    -------------

    <————————————————中间区————————————————>
    分为上下结构
    上方为消息显示区
    下方为消息输入区
    可能支持文件传输
    -------------
    |A: Hello   |
    |B: Hi      |
    |    Im C:Me|
    -------------
    |Message    |
    |SendWaiting|
    -------------

    <————————————————右半边————————————————>
    分情况显示
    若为私信模式, 则隐藏
    若为群聊模式, 则分为上下结构
    上为群聊信息
    下为群成员列表
    ------------
    |Party Info|
    ------------
    |Member A  |
    |Member B  |
    |..........|
    ------------

    '''

    def __init__(self):
        super().__init__()

        # 主窗口属性预设



        # 分三个部分初始化界面
        self.initUI()

    def initUI(self):

        self.mainLayout = ClassicLayout.Horizontal(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)

        self.creLeftWidgets()
        self.creMidWidgets()
        self.creRightWidgets()
        self.applyLeftLayout()
        self.applyMidLayout()
        self.applyRightLayout()

        self.mainLayout.addWidget(self.leftSideBarSection, 0)
        self.mainLayout.addWidget(Separator(Separator.Vertical, width=1))
        self.mainLayout.addWidget(self.middleArea, 0)
        self.mainLayout.addWidget(Separator(Separator.Vertical, width=1))
        self.mainLayout.addWidget(self.rightSideBarSection, 0)
        self.setLayout(self.mainLayout)

    def creLeftWidgets(self):
        '''
        创建左边区域的组件
        '''

        # 个人信息栏
        self.personalInfoSection = Section((200, 60))
        self.personalID = QLabel("ID")
        self.personalID.setFont(Fonts.UniversalPlainFont)
        self.personalUID = QLabel("UID:123456")
        self.personalUID.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))

        # 消息列表切换按钮栏
        self.switchButtonSection = Section((200, 20))
        self.newsButton = Button("N", "最新消息", (20, 20), Fonts.sizedFont(Fonts.UniversalPlainFont, 8))
        self.friendsButton = Button("F", "好友", (20, 20), Fonts.sizedFont(Fonts.UniversalPlainFont, 8))
        self.partiesButton = Button("P", "群聊", (20, 20), Fonts.sizedFont(Fonts.UniversalPlainFont, 8))

        # 消息列表区域
        self.newsListSection = Section((200, 538), Section.VExtendable)
        # 从本地读取已经存在的消息列表
        # <————————————————————————————————>
        # [NTC]
        # obtainLocalNewsList() -> Tuple[NewsBar, ...]
        # <————————————————————————————————>

    def creMidWidgets(self):
        '''
        创建中间区域的组件
        '''

        # 消息输入框
        self.messageInputer = QPlainTextEdit()
        self.messageInputer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.messageInputer.setFont(Fonts.UniversalPlainFont)

        # 消息发送按钮
        self.messageSendButton = Button("发送", '', (90, 30), Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
    
    def creRightWidgets(self):
        '''
        创建右边区域的组件
        '''

        # 群聊名称
        self.partyName = QLabel("Party Name")
        self.partyName.setFont(Fonts.UniversalPlainFont)
        self.partyUID = QLabel("PUID: 123456")
        self.partyUID.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))

        # 群聊信息区域
        self.partyInfoSection = Section((200, 60), Section.Fixed)

    def applyLeftLayout(self):
        '''
        创建并设置左边区域的布局
        '''

        # 个人信息栏布局
        self.personalInfoLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.Default, (20, 5, 20, 5), 5)
        self.personalInfoLayout.addWidget(self.personalID, 1)
        self.personalInfoLayout.addWidget(self.personalUID, 1)
        self.personalInfoSection.setLayout(self.personalInfoLayout)

        # 按钮栏布局
        self.switchButtonLayout = ClassicLayout.Horizontal(ClassicLayout.Center, ClassicLayout.Default, (20, 0, 20, 0), 10)
        self.switchButtonLayout.addWidget(self.newsButton, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.switchButtonLayout.addStretch(1)
        self.switchButtonLayout.addWidget(self.friendsButton, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.switchButtonLayout.addStretch(1)
        self.switchButtonLayout.addWidget(self.partiesButton, 0, alignment=Qt.AlignmentFlag.AlignCenter)
        self.switchButtonSection.setLayout(self.switchButtonLayout)

        # 消息列表区域
        self.scrollableNewsList = QScrollArea()
        self.scrollableNewsList.setWidgetResizable(True)
        self.newsListLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.newsListLayout.addStretch(1)
        self.newsListSection.setLayout(self.newsListLayout)

        # 整个左边栏区域
        self.leftSideBarSection = Section((200, 618), Section.VExtendable)
        self.leftSideBarLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.leftSideBarLayout.addWidget(self.personalInfoSection, 0)
        self.leftSideBarLayout.addWidget(Separator(width=1), 0)
        self.leftSideBarLayout.addWidget(self.switchButtonSection, 0)
        self.leftSideBarLayout.addWidget(Separator(width=1), 0)
        self.leftSideBarLayout.addWidget(self.newsListSection, 1)
        self.leftSideBarSection.setLayout(self.leftSideBarLayout)

    def applyMidLayout(self):
        '''
        创建中间区域的布局
        '''

        # 消息展示区域
        self.messageDisplaySection = Section((800, 418), Section.Extendable)

        # 消息输入区域
        self.messageInputSection = Section((800, 150), Section.Extendable)
        self.messageInputLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.Max, ClassicLayout.NoBorder, 0)
        self.messageInputLayout.addWidget(self.messageInputer, 1)
        self.messageInputSection.setLayout(self.messageInputLayout)

        # 消息发送按钮区域
        self.messageSendButtonSection = Section((800, 50), Section.HExtendable)
        self.messageSendButtonLayout = ClassicLayout.Horizontal(ClassicLayout.CRight, ClassicLayout.Default, (20, 0, 20, 20), 0)
        self.messageSendButtonLayout.addStretch(1)
        self.messageSendButtonLayout.addWidget(self.messageSendButton, 0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        self.messageSendButtonSection.setLayout(self.messageSendButtonLayout)

        # 整个中间区域
        self.middleArea = Section((800, 680), Section.Extendable)
        self.middleLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.middleLayout.addWidget(self.messageDisplaySection, 1)
        self.middleLayout.addWidget(Separator(width=1))
        self.middleLayout.addWidget(self.messageInputSection, 1)
        self.middleLayout.addWidget(self.messageSendButtonSection, 0)
        self.middleArea.setLayout(self.middleLayout)

    def applyRightLayout(self):
        '''
        创建并设置右边区域的布局
        '''

        # 群信息显示栏
        self.partyInfoLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.Default, (20, 5, 20, 5), 5)
        self.partyInfoLayout.addWidget(self.partyName, 1)
        self.partyInfoLayout.addWidget(self.partyUID, 1)
        self.partyInfoSection.setLayout(self.partyInfoLayout)

        # 群成员显示区域
        self.partyMemberSection = Section((200, 550), Section.Fixed)

        # 右边栏区域
        self.rightSideBarSection = Section((200, 618), Section.VExtendable)
        self.rightSideBarLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.rightSideBarLayout.addWidget(self.partyInfoSection, 0)
        self.rightSideBarLayout.addWidget(Separator(width=1))
        self.rightSideBarLayout.addWidget(self.partyMemberSection, 0)
        self.rightSideBarSection.setLayout(self.rightSideBarLayout)
        

if __name__ == '__main__':
    MMApp = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    MMApp.exec()


