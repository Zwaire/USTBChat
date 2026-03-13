# -*- coding: utf-8 -*-

'''
用户界面
登录成功后的主界面
包括群聊、私信、文件传输等功能
'''

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List
from PySide6.QtWidgets import (QApplication, QLayoutItem, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLayout,
                               QSizePolicy, QLineEdit, QMessageBox, QMainWindow, QScrollArea, QPlainTextEdit,
                               QStackedLayout)
from PySide6.QtGui import QMouseEvent, QTextOption
from PySide6.QtCore import Qt, Slot, QObject, Signal
from CommonCouple import Section, Fonts, Button, ClassicLayout, Separator

# 新增引入状态管理和消息模型
# from bin.state.AppState import AppState
from bin.state.ChatModels import Message, Contact, Friend, Group
from bin.tool.LoginTool import LoginWindowTool as tool
from bin.tool.UserInterfaceTool import UserInterfaceTool as UITool
import bin.tool.ContactTool as CT

# 新增一个信号类，用于安全地将子线程收到的网络消息抛给主线程 UI
class MainSignals(QObject):
    msg_received = Signal(dict)

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

    class ContactBar(QWidget):

        hasBeenClicked = Signal(str)
        
        Party = True
        Friend = False

        def __init__(self, type: bool, UID: str, ID: str = "DefaultID", isRead: bool = True, lastTime: str = "00:00", lastChat: str = "DefaultChat", hasRead: bool = False):
            '''
            初始化聊天列表对象

            Args:
                type(bool): 该聊天列表对象是否为群聊
                UID(str): 群组或私聊UID
                ID(str): 对象的名称
                isRead(bool): 是否已读
                lastTime(str): 最新消息时间
                lastChat(str): 最新消息
            '''
            super().__init__()

            self.Type = type
            self.UID = UID
            self.isRead = isRead
            self.hasRead = hasRead      # 登录之后是否点击过
            self.initUI()
            self.setStyleSheet("border: 2px solid blue;")
            self.modifyID(ID)
            self.modifyLastTime(lastTime)
            self.modifyLastChat(lastChat)

        def initUI(self):
            
            self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            self.setFixedHeight(50)

            self.creWidgets()
            self.applyLayout()

        def creWidgets(self):
            '''
            创建聊天列表对象的组件
            '''

            # 群聊或好友名称
            self.objNameBar = QLabel()
            self.objNameBar.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
            self.objNameBar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.objNameBar.setFixedHeight(30)

            # 最新消息
            self.objLastChatBar = QLabel()
            self.objLastChatBar.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
            self.objLastChatBar.setStyleSheet("color: gray;")
            self.objLastChatBar.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.objLastChatBar.setFixedHeight(20)

            # 最新消息时间
            self.objLastTimeBar = QLabel()   # 非本日为日期, 本日为时期
            self.objLastTimeBar.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 8))
            self.objLastTimeBar.setStyleSheet("color: gray;")
            self.objLastTimeBar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.objLastTimeBar.setFixedSize(40, 30)

        def applyLayout(self):
            '''
            创建并设置聊天列表对象的布局
            '''

            # 第一行, 包括名称和时间
            self.nameTimeLayout = ClassicLayout.Horizontal(ClassicLayout.CLeft, ClassicLayout.Default, ClassicLayout.NoBorder, 2)
            self.nameTimeLayout.addWidget(self.objNameBar, 0, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.nameTimeLayout.addStretch(1)
            self.nameTimeLayout.addWidget(self.objLastTimeBar, 0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            # 整体布局
            self.contactBarLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, (2, 2, 2, 2), 2)
            self.contactBarLayout.addLayout(self.nameTimeLayout, 0)
            self.contactBarLayout.addStretch(1)
            self.contactBarLayout.addWidget(self.objLastChatBar, 0, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom)

            self.setLayout(self.contactBarLayout)

        def modifyID(self, newID: str) -> bool:
            '''
            修改对象名称

            Args:
                newID(str): 新的ID
            
            Returns:
                bool: 是否修改成功
            '''
            
            # 检测新ID是否合法
            if not tool._is_name_not_uid(newID):
                return False

            # 修改ID
            self.objNameBar.setText(newID)
            return True

        def modifyLastTime(self, lastTime: str):
            '''修改最后消息的时间, 一般不会出错'''

            self.objLastTimeBar.setText(lastTime)

        def modifyLastChat(self, lastChat: str):
            '''修改最后一条消息'''

            self.objLastChatBar.setText(lastChat)

        def mousePressEvent(self, event: QMouseEvent) -> None:

            self.hasBeenClicked.emit(self.UID)

            return super().mousePressEvent(event)

    class FriendBar(QWidget):

        hasBeenClicked = Signal(str)

        def __init__(
                self,
                UID: str,
                ID: str
        ):
            
            super().__init__()

            self.UID = UID

            self.initUI()
            self.setStyleSheet("border: 2px solid blue;")
            self.modifyUserName(ID)

        def initUI(self):
            
            self.creWidgets()
            self.applyLayout()

        def creWidgets(self):

            # 名称
            self.userName = QLabel()
            self.userName.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
            self.userName.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.userName.setFixedHeight(30)

        def applyLayout(self):

            self.userNameLayout = ClassicLayout.Vertical(ClassicLayout.Center, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
            self.userNameLayout.addWidget(self.userName, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setLayout(self.userNameLayout)

        def modifyUserName(self, name: str):
            self.userName.setText(name)

        def mousePressEvent(self, event: QMouseEvent) -> None:

            self.hasBeenClicked.emit(self.UID)

            return super().mousePressEvent(event)

    class PartyBar(QWidget):

        hasBeenClicked = Signal(str)

        def __init__(
                self,
                UID: str,
                ID: str
        ):
            
            super().__init__()

            self.UID = UID

            self.initUI()
            self.setStyleSheet("border: 2px solid blue;")
            self.modifyPartyName(ID)

        def initUI(self):
            
            self.creWidgets()
            self.applyLayout()

        def creWidgets(self):

            # 名称
            self.partyName = QLabel()
            self.partyName.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
            self.partyName.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
            self.partyName.setFixedHeight(30)

        def applyLayout(self):

            self.partyNameLayout = ClassicLayout.Vertical(ClassicLayout.Center, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
            self.partyNameLayout.addWidget(self.partyName, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.setLayout(self.partyNameLayout)

        def modifyPartyName(self, name: str):
            self.partyName.setText(name)

        def mousePressEvent(self, event: QMouseEvent) -> None:

            self.hasBeenClicked.emit(self.UID)

            return super().mousePressEvent(event)

    class ChatBar(QWidget):
        '''
        显示在聊天区域的聊天块
        '''

        def __init__(
                self,
                isSelf: bool,
                senderUID: str,
                senderNickName: str,
                content: str,
                time: str
        ):
            '''
            Args:
                isSelf(bool): 消息是否为自己发出的
                senderUID(str): 发送者的UID
                senderNickName(str): 发送者的昵称
                content(str): 消息的内容
                time(str): 发送的时间
            '''
            super().__init__()

            self.isSelf = isSelf
            self.senderUID = senderUID,
            # self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
        
            self.initUI()

            self.modifySenderID(senderNickName)
            self.modifySendTime(UITool.format_msg_time(time))
            self.modifyChatContent(content)
        
        def initUI(self):

            self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Minimum)
            self.creWidgets()
            self.applyLayout()

        def creWidgets(self):

            # 时间
            self.chatSendTime = QLabel()
            self.chatSendTime.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.chatSendTime.setFixedSize(80, 20)
            self.chatSendTime.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 8))

            # 对象ID
            self.chatSenderID = QLabel()
            self.chatSenderID.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
            self.chatSenderID.setMinimumWidth(100)
            self.chatSenderID.setFixedHeight(30)
            self.chatSenderID.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
            
            # 消息内容块
            self.chatContent = QPlainTextEdit()
            self.chatContent.setFont(Fonts.UniversalPlainFont)
            self.chatContent.setWordWrapMode(QTextOption.WrapMode.WordWrap)
            self.chatContent.setReadOnly(True)
            self.chatContent.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Preferred)
            # self.chatContent.setMinimumWidth(200)
            self.chatContent.setStyleSheet("padding: 2px; border: 1px solid #ddd; border-radius: 4px;")
            if self.isSelf: self.chatContent.setStyleSheet("padding: 2px; border: 1px solid #ddd; border-radius: 4px; background-color: #868686;")
            
        def applyLayout(self):

            self.chatCubeLayout = ClassicLayout.Vertical(ClassicLayout.RTop, ClassicLayout.MinMax, (20, 0, 20, 0), 5) if self.isSelf else ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.Min, (20, 0, 20, 0), 5)
            self.chatCubeLayout.addWidget(self.chatSendTime, 0, alignment=Qt.AlignmentFlag.AlignRight if self.isSelf else Qt.AlignmentFlag.AlignLeft)
            self.chatCubeLayout.addWidget(self.chatSenderID, 0, alignment=Qt.AlignmentFlag.AlignRight if self.isSelf else Qt.AlignmentFlag.AlignLeft)
            self.chatCubeLayout.addWidget(self.chatContent, 0, alignment=Qt.AlignmentFlag.AlignRight if self.isSelf else Qt.AlignmentFlag.AlignLeft)
            # self.chatCubeLayout.addStretch(1)
            self.setLayout(self.chatCubeLayout)

        def modifySenderID(self, ID: str) -> bool:

            if not tool._is_name_not_uid(ID):
                return False

            self.chatSenderID.setText(ID)
            return True
        
        def modifySendTime(self, sendTime: str):
            self.chatSendTime.setText(sendTime)
        
        def modifyChatContent(self, content: str):
            self.chatContent.setPlainText(content)

    def __init__(self):
        super().__init__()

        

        self.UserID = "123456"
        self.CurrentChatID = None
        self.isCurrentChatGroup = False

        # 主窗口属性预设
        self.setWindowTitle("USTBChat")
        
        self.newsContactBarList = []
        self.friendsBarList = []
        self.partiesBarList = []

        self.cachedChatHistory = dict()

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

        self.initContactList()
        self.getFriendsListFromServer()
        self.getGroupsListFromServer()

        # 新增绑定按钮交互事件
        self.slotsConnect()

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
        self.messageListSection = Section((200, 538), Section.VExtendable)
        self.newsListSection = Section((200, 538), Section.VExtendable)
        self.friendsListSection = Section((200, 538), Section.VExtendable)
        self.partiesListSection = Section((200, 538), Section.VExtendable)
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
        self.scrollableFriendsList = QScrollArea()
        self.scrollablePartiesList = QScrollArea()
        self.scrollableNewsList.setWidgetResizable(True)
        self.scrollableFriendsList.setWidgetResizable(True)
        self.scrollablePartiesList.setWidgetResizable(True)

        self.newsListLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.newsListLayout.addStretch(1)
        self.newsListSection.setLayout(self.newsListLayout)
        self.scrollableNewsList.setWidget(self.newsListSection)

        self.friendsListLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.friendsListLayout.addStretch(1)
        self.friendsListSection.setLayout(self.friendsListLayout)
        self.scrollableFriendsList.setWidget(self.friendsListSection)

        self.partiesListLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.partiesListLayout.addStretch(1)
        self.partiesListSection.setLayout(self.partiesListLayout)
        self.scrollablePartiesList.setWidget(self.partiesListSection)

        self.switchableSection = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.switchableLayout = QStackedLayout()
        self.switchableLayout.setSizeConstraint(ClassicLayout.MinMax)
        self.switchableLayout.setContentsMargins(0, 0, 0, 0)
        self.switchableLayout.setSpacing(0)

        self.switchableLayout.addWidget(self.newsListSection)
        self.switchableLayout.addWidget(self.friendsListSection)
        self.switchableLayout.addWidget(self.partiesListSection)

        # 整个消息显示区域
        self.messageListSection.setLayout(self.switchableLayout)

        # 整个左边栏区域
        self.leftSideBarSection = Section((200, 618), Section.VExtendable)
        self.leftSideBarLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, ClassicLayout.NoBorder, 0)
        self.leftSideBarLayout.addWidget(self.personalInfoSection, 0)
        self.leftSideBarLayout.addWidget(Separator(width=1), 0)
        self.leftSideBarLayout.addWidget(self.switchButtonSection, 0)
        self.leftSideBarLayout.addWidget(Separator(width=1), 0)
        self.leftSideBarLayout.addWidget(self.messageListSection, 1)
        self.leftSideBarSection.setLayout(self.leftSideBarLayout)

    def applyMidLayout(self):
        '''
        创建中间区域的布局
        '''

        # 消息展示区域
        self.messageDisplaySection = Section((800, 418), Section.Extendable)
        self.scrollableMessageLayout = QScrollArea()
        self.scrollableMessageLayout.setWidgetResizable(True)
        self.scrollableMessageLayout.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollableMessageLayout.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.messageDisplayLayout = ClassicLayout.Vertical(constr=ClassicLayout.MinMax, margins=ClassicLayout.NoBorder, spacing=10)
        self.messageDisplaySection.setLayout(self.messageDisplayLayout)
        self.scrollableMessageLayout.setWidget(self.messageDisplaySection)

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
        # self.middleLayout.addWidget(self.messageDisplaySection, 2)
        self.middleLayout.addWidget(self.scrollableMessageLayout, 2)
        # self.middleLayout.addStretch(1)
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
    
    def slotsConnect(self):
        '''绑定UI交互事件'''
        # 将“发送”按钮的点击事件连接到 send_message 函数
        self.messageSendButton.clicked.connect(lambda checked: self.send_message())

        self.newsButton.clicked.connect(lambda checked: self.displayNewsContactBar())
        self.friendsButton.clicked.connect(lambda checked: self.displayFriendsBar())
        self.partiesButton.clicked.connect(lambda checked: self.displayPartiesBar())

    @Slot()
    def displayNewsContactBar(self):
        '''将左侧边栏下方改为显示最新消息'''

        # 切换显示区域
        self.switchableLayout.setCurrentIndex(0)

        self.newsListLayout.update()

    @Slot()
    def displayFriendsBar(self):

        # 切换显示区域
        self.switchableLayout.setCurrentIndex(1)

        self.newsListLayout.update()

    @Slot()
    def displayPartiesBar(self):

        # 切换显示区域
        self.switchableLayout.setCurrentIndex(2)

        self.newsListLayout.update()

    def initContactList(self) -> bool:
        '''登录后, 从服务器获取消息对象列表, 并显示在左侧边栏'''

        # import bin.tool.ContactTool as CT

        response = dict()
        # 向服务器获取
        while(True):
            try:
                response = CT.request_contacts_list()
            except:
                continue
            
            break
        
        # 解析服务器消息
        if response['type'] != 'contacts_list':
            return False
        
        # 将Contact转换为能直接用的ContactBar
        self.newsContactBarList = []
        for x in response['contacts']:
            _ = contactToBar(x)
            _.hasBeenClicked.connect(lambda uid = _.UID, isGroup = _.Type: self.showSpecificChatArea(uid, isGroup))
            self.newsContactBarList.append(_)
        # self.newsContactBarList[0].printInfo()

        self.displayNewsContactBar()

        for i in range(len(self.newsContactBarList)):
            self.newsListLayout.insertWidget(self.newsListLayout.count() - 1, self.newsContactBarList[i])
        
        return True

    def getFriendsListFromServer(self) -> bool:

        # import bin.tool.ContactTool as CT

        while(True):
            try:
                response = CT.request_friend_list()
            except:
                continue

            break

        # 解析服务器消息
        if response['type'] != 'friend_list':
            return False
        
        # 转换为Bar
        # self.friendsBarList = [friendToBar(x) for x in response['friends']]
        for x in response['friends']:
            _ = friendToBar(x)
            _.hasBeenClicked.connect(lambda uid = _.UID, isGroup = False: self.showSpecificChatArea(uid, isGroup))
            self.friendsBarList.append(_)

        for i in range(len(self.friendsBarList)):
            self.friendsListLayout.insertWidget(self.friendsListLayout.count() - 1, self.friendsBarList[i])

        return True

    def getGroupsListFromServer(self) -> bool:

        # import bin.tool.ContactTool as CT

        while(True):
            try:
                response = CT.request_group_list()
            except:
                continue

            break

        # 解析服务器消息
        if response['type'] != 'group_list':
            return False
        
        # 转换为Bar
        # self.partiesBarList = [partyToBar(x) for x in response['groups']]

        for x in response['groups']:
            _ = partyToBar(x)
            _.hasBeenClicked.connect(lambda uid = _.UID, isGroup = True: self.showSpecificChatArea(uid, isGroup))
            self.partiesBarList.append(_)

        for i in range(len(self.partiesBarList)):
            self.partiesListLayout.insertWidget(self.partiesListLayout.count() - 1, self.partiesBarList[i])

        return True

    def generateChatRowSection(self, msg: Message) -> Section:

        _ = self.ChatBar(
                isSelf=msg.is_self,
                senderUID=msg.sender_uid,
                senderNickName=msg.sender_nickname,
                content=msg.content,
                time=msg.time
            )

        isSelfSend = _.isSelf

        # 生成聊天栏布局

        chatRowSection = Section(policy=(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        if isSelfSend:
            chatRowLayout = ClassicLayout.Horizontal(ClassicLayout.RTop, ClassicLayout.MinMax, (5, 0, 5, 0), 5)
            chatRowLayout.addStretch(1)
            chatRowLayout.addWidget(_, 2, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        else:
            chatRowLayout = ClassicLayout.Horizontal(ClassicLayout.LTop, ClassicLayout.MinMax, (5, 0, 5, 0), 5)
            chatRowLayout.addWidget(_, 2, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            chatRowLayout.addStretch(1)

        chatRowSection.setLayout(chatRowLayout)

        return chatRowSection

    @Slot(str)
    def showSpecificChatArea(self, UID: str, isGroup: bool):

        # import bin.tool.ContactTool as CTool

        print("I am clicked")
        self.CurrentChatID = UID
        self.isCurrentChatGroup = isGroup

        # 清空聊天区域
        wipeOutChildItemOfLayout(self.messageDisplayLayout)

        # 缓存中不存在该UID, 则向服务器请求获取聊天记录
        if not (UID in self.cachedChatHistory.keys()):
            self.cachedChatHistory.update({UID: CT.fetch_history(UID)})

        # 向缓存中读取聊天记录
        chatUpcoming = self.cachedChatHistory[UID]

        # 将聊天记录转换为可使用的Qt组件
        for i in range(len(chatUpcoming)):
            
            chatRowSection = self.generateChatRowSection(chatUpcoming[i])

            # self.messageDisplayLayout.addLayout(chatRowLayout, 0)
            self.messageDisplayLayout.addWidget(chatRowSection, 0)
        
        # self.messageDisplayLayout.addStretch(1)
        self.messageDisplayLayout.update()
            
    # def getHistory

    @Slot(dict)
    def process_network_message(self, msg_dict):
        '''
        新增：处理从服务器推送到主界面的消息
        '''
        msg_type = msg_dict.get("type")
        
        if msg_type == "message":
            # 解析服务器传来的私聊消息
            sender_id = msg_dict.get("username", "Unknown")
            content = msg_dict.get("message", "")
            
            # 实例化新的 Message 对象
            new_msg = Message(
                sender_uid=sender_id,
                sender_nickname=sender_id, 
                content=content,
                time=msg_dict.get("time", ""),
                is_self=False
            )
            
            # 利用 AppState 进行本地持久化并更新内存缓存
            # AppState().add_message(target_id=sender_id, msg=new_msg)
            
            # 可以在这里追加 UI 刷新的代码，比如把消息打印到中间的聊天框里
            print(f"收到来自 {sender_id} 的消息: {content}")
            
        elif msg_type == "system":
            print(f"系统消息: {msg_dict.get('content')}")

    @Slot()
    def send_message(self):
        '''处理发送按钮点击事件'''

        # 看当前聊天的UID
        if not self.CurrentChatID:
            return

        # 获取输入框的纯文本
        text = self.messageInputer.toPlainText().strip()
        if not text:
            return # 没写字就不发
            
        # from bin.state.AppState import AppState
        from bin.state.ChatModels import Message

        # my_uid = AppState().uid
        
        # 注意：由于目前左侧列表没做好，我们暂时无法通过点击来“选中”好友。
        # 为了让代码跑通，我们先强行指定一个目标好友 (建议去 MySQL 注册一个名为 test 的账号用来测试)
        # target_friend = "test" 

        # 构造符合《通信接口.md》规范的报文
        # packet = {
        #     "type": "message",
        #     "username": self.UserID,
        #     "friendname": self.CurrentChatID,
        #     "message": text
        # }
        
        sendContent = self.messageInputer.toPlainText().strip()

        sendSuccess = CT.send_message(
            self.CurrentChatID,
            sendContent,
            self.isCurrentChatGroup
        )

        sendSuccess = True      # 测试用

        if not sendSuccess:
            QMessageBox.warning(self, "", "发送失败")
            return
        
        # 发送成功, 在本地显示自己发送的消息

        msg = Message(
            sender_uid=self.UserID,
            sender_nickname=self.personalID.text(),
            content=sendContent,
            time="",
            is_self=True
        )

        try:
            historyQuote: List[Message] = self.cachedChatHistory[self.CurrentChatID]
        except:
            QMessageBox.warning(self, "", "发送的聊天对象不存在")
            return
        
        self.messageInputer.clear()
        historyQuote.append(msg)
        
        _ = self.generateChatRowSection(msg)
        self.messageDisplayLayout.addWidget(_)
        scrollBar = self.scrollableMessageLayout.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
        self.messageDisplayLayout.update()

        # if self.client:
        #     # 1. 把消息发给服务器
        #     self.client.send_data(packet)
            
        #     # 2. 把消息存入本地 AppState
        #     new_msg = Message(
        #         sender_uid=my_uid,
        #         sender_nickname=AppState().nickname,
        #         content=text,
        #         time="刚刚",
        #         is_self=True
        #     )
        #     AppState().add_message(target_friend, new_msg)
            
        #     # 3. 清空输入框，并在控制台打印确认
        #     self.messageInputer.clear()
        #     print(f"成功发送给 {target_friend}: {text}")
        # else:
        #     QMessageBox.warning(self, "错误", "未连接到服务器！")

def cleanWidgetsInLayout(layout: QLayout, left: int = 0):
    '''清理布局中的组件, 但保留最后left数量的组件'''

    for i in range(layout.count() - left):
        _ = layout.takeAt(0)
        # assert _ is MainWindow.ContactBar
        _.deleteLater() # type: ignore

def wipeOutChildItemOfLayout(layout: QLayout, delete_layout_itself: bool = False):
    """
    递归地清空一个布局及其所有嵌套子布局中的所有组件。

    参数:
        layout (QLayout): 要清空的根布局对象。
        delete_layout_itself (bool): 清空内容后，是否也删除此布局对象本身。
                                      注意：如果此布局是另一个布局的子项，或已设置给一个部件，
                                      则通常不应将其删除（其父对象会管理它）。
    """
    if layout is None:
        return

    # 递归基线：当布局中不再有项时停止
    while layout.count():
        # 获取并移除最顶层的项
        item: QLayoutItem = layout.takeAt(0)
        if item is None:
            continue

        # 情况1：该项管理的是一个部件 (QWidget)
        widget = item.widget()
        if widget is not None:
            # 从父部件中移除
            widget.setParent(None)
            # 安排安全删除
            widget.deleteLater()
            # 注意：item 本身（QLayoutItem）由 takeAt() 返回，Qt内部会管理其销毁
            continue  # 此项处理完毕，继续下一项

        # 情况2：该项管理的是一个嵌套的子布局 (QLayout)
        sub_layout = item.layout()
        if sub_layout is not None:
            # 递归清空这个子布局
            wipeOutChildItemOfLayout(sub_layout, delete_layout_itself=True)
            # 子布局已被清空，其管理的 item 也被 takeAt 移除
            # 注意：此时 sub_layout 对象可能仍有父级，但已为空
            continue

        # 情况3：该项是一个空白/伸缩项 (QSpacerItem)
        # 对于 addStretch() 等添加的空白项，只需将其从布局中移除。
        # 被 takeAt 后，Qt 会负责清理这个 QSpacerItem。
        # 因此这里没有 widget 或 sub_layout 需要处理。

    # 可选：在清空所有内容后，是否删除此布局对象本身
    if delete_layout_itself:
        # 警告：只有在你明确创建了此布局，且它未被设置为任何部件的布局时，才可安全删除。
        # 通常，对于通过 addLayout() 添加的子布局，不应在此处删除，因为其父布局管理其生命周期。
        # 此处逻辑仅供参考，需根据实际情况谨慎使用。
        layout.setParent(None)
        # 注意：QLayout 没有 deleteLater() 方法，它继承自 QObject
        # 如果此布局对象是独立创建的，且您确信需要删除，可做标记并由垃圾回收器处理。
        # 更安全的做法是在函数外部管理顶级布局的生命周期。

def contactToBar(contact: Contact) -> MainWindow.ContactBar:
    return MainWindow.ContactBar(
        type=contact.is_group,
        UID=contact.id,
        ID=contact.name,
        isRead=(contact.unread == 0),
        lastTime=UITool.format_msg_time(contact.last_time),
        lastChat=contact.last_message
    )

def friendToBar(friend: Friend) -> MainWindow.FriendBar:
    return MainWindow.FriendBar(
        UID=friend.uid,
        ID=friend.nickname
    )

def partyToBar(party: Group) -> MainWindow.PartyBar:
    return MainWindow.PartyBar(
        UID=party.gid,
        ID=party.name
    )

if __name__ == '__main__':
    MMApp = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    MMApp.exec()


