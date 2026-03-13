# -*- coding: utf-8 -*-

'''
用户界面
登录成功后的主界面
包括群聊、私信、文件传输等功能
'''

import os
import sys
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from typing import List, Dict, Optional
from PySide6.QtWidgets import (QApplication, QLayoutItem, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLayout,
                               QSizePolicy, QLineEdit, QMessageBox, QMainWindow, QScrollArea, QPlainTextEdit, QCheckBox,
                               QStackedLayout, QMenu)
from PySide6.QtGui import QMouseEvent, QTextOption, QAction
from PySide6.QtCore import Qt, Slot, QObject, Signal
from bin.ui.CommonCouple import Section, Fonts, Button, ClassicLayout, Separator, TextInput

# 新增引入状态管理和消息模型
# from bin.state.AppState import AppState
from bin.state.ChatModels import Message, Contact, Friend, Group
from bin.tool.LoginTool import LoginWindowTool as tool
from bin.tool.UserInterfaceTool import UserInterfaceTool as UITool
import bin.tool.ContactTool as CT

# 新增一个信号类，用于安全地将子线程收到的网络消息抛给主线程 UI
class MainSignals(QObject):
    msg_received = Signal(dict)

class AddFriendPartyWindow(QWidget):
    '''
    右键菜单中用以添加好友或群聊的窗口
    '''

    addSuccess = Signal()

    def __init__(self, addFriend: bool):
        '''
        Args:
            addFriend(bool): 该窗口的类型, 若为True则是添加好友, 若为False则为添加群聊
        '''
        super().__init__()

        self.FriendAddType = addFriend
        self.initUI()

    def initUI(self):
        
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(460, 50)

        self.creWidgets()
        self.applyLayout()
        self.slotsConnect()

    def creWidgets(self):

        # 用来输入UID的输入框
        self.uidInputer = TextInput(
            "UID: ",
            "输入要添加的好友的UID" if self.FriendAddType else "输入要添加的群聊的UID",
            TextInput.Displayed,
            (360, 40),
            Fonts.UniversalPlainFont
        )

        # 添加按钮
        self.addButton = Button(
            "添加",
            "点击以向该用户申请添加好友" if self.FriendAddType else "点击以向该群聊申请加入",
            (80, 40),
            Fonts.UniversalPlainFont
        )

    def applyLayout(self):

        # 水平布局
        self.mainLayout = ClassicLayout.Horizontal(ClassicLayout.Center, ClassicLayout.MinMax, (10, 5, 10, 5), 5)

        self.mainLayout.addLayout(self.uidInputer, 0)
        self.mainLayout.addStretch(1)
        self.mainLayout.addWidget(self.addButton, 0)

        self.setLayout(self.mainLayout)

    def slotsConnect(self):
        self.addButton.clicked.connect(lambda checked: self.buttonClicked())

    @Slot()
    def buttonClicked(self):
        '''点击按钮后的操作, 向服务器发送添加请求, 成功则发出信号'''

        # print("WHY")

        # 检查输入是否合法
        whatUserWrite = self.uidInputer.getInput()
        validate_res = tool._validate_id(whatUserWrite)
        if validate_res != True:
            QMessageBox.warning(self, "", "输入UID的格式有误")
            return

        try:
            if self.FriendAddType:
                response: Dict = CT.request_add_friend(whatUserWrite)
            else:
                response = CT.request_join_group(whatUserWrite)
        except Exception:
            QMessageBox.warning(self, "", "网络错误")
            return
        
        # 处理服务器消息
        responseType = response.get('type')
        expected_types = {'add_friend'} if self.FriendAddType else {'join_group', 'add_group'}
        if responseType not in expected_types:
            QMessageBox.warning(self, "", "服务器返回类型有误")
            return
        
        status = response.get('status')
        if status == 3:
            QMessageBox.warning(self, "", "该用户不存在")
        elif status == 7:
            QMessageBox.warning(self, "", "该群聊不存在")
        elif status == 6:
            QMessageBox.warning(self, "", "你已在该群聊中")
        elif status == 0:
            # 添加成功
            self.uidInputer.clearInput()
            self.addSuccess.emit()
            QMessageBox.warning(self, "", "添加成功")
        else:
            QMessageBox.warning(self, "", "服务器状态错误")

class CreatePartyWindow(QWidget):
    '''创建群聊时的窗口'''

    createSuccess = Signal()

    class OptionFriendBar(QWidget):
        '''
        现在我每写一个class我心脏都得停跳一拍
        '''

        SelectedStyle = """
            #FriendBar {
                border: 2px solid #3a86ff;
                border-radius: 8px;
                padding: 8px;
                background-color: #73FE01;
            }
        """

        UnSelectedStyle = """
            #FriendBar {
                border: 2px solid #3a86ff;
                border-radius: 8px;
                padding: 8px;
                background-color: #FFFFFF;
            }
        """

        def __init__(self, name: str, uid: str, selected: bool = False):
            super().__init__()

            self.setObjectName("FriendBar")
            self.UID = uid
            self.selected = selected
            self.initUI()
            self.modifyName(name)

        def initUI(self):

            if self.selected:
                self.setStyleSheet(self.SelectedStyle)
            else:
                self.setStyleSheet(self.UnSelectedStyle)

            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.setFixedSize(320, 50)

            self.creWidgets()
            self.applyLayout()

        def creWidgets(self):

            self.userName = QLabel()
            self.userName.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            self.userName.setFixedHeight(40)
            self.userName.setFont(Fonts.UniversalPlainFont)
        
        def applyLayout(self):

            self.mainLayout = ClassicLayout.Horizontal(
                ClassicLayout.CLeft,
                ClassicLayout.Max,
                (5, 5, 5, 5),
                0
            )

            self.mainLayout.addWidget(self.userName, 0, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self.mainLayout.addStretch(1)
            self.setLayout(self.mainLayout)

        def mousePressEvent(self, event: QMouseEvent) -> None:
            
            self.switchSelected()

            return super().mousePressEvent(event)

        def switchSelected(self):

            if self.selected:
                self.selected = False
                self.setStyleSheet(self.UnSelectedStyle)
            else:
                self.selected = True
                self.setStyleSheet(self.SelectedStyle)

        def modifyName(self, newName: str):

            self.userName.setText(newName)

    def __init__(self, friends: List[Friend]):
        super().__init__()

        self.friends = friends
        self.initUI()

    def initUI(self):

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(420, 650)

        self.creWidgets()
        self.applyLayout()
        self.slotsConnect()

    def creWidgets(self):

        self.partyName = TextInput(
            "群名称: ",
            "请输入群聊的名称",
            TextInput.Displayed,
            (240, 40),
            Fonts.UniversalPlainFont
        )

        self.confirmButton = Button(
            "确认",
            "点击后以当前选中的用户为成员创建群聊",
            (80, 40),
            Fonts.UniversalPlainFont
        )
        self.aiBotCheck = QCheckBox("添加智能助手 lulu")
        self.aiBotCheck.setChecked(False)
        self.aiBotCheck.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 10))

    def applyLayout(self):

        # 群聊名称行
        self.partyNameRow = Section(
            (420, 50),
            Section.Fixed
        )

        self.partyNameLayout = ClassicLayout.Horizontal(
            ClassicLayout.CLeft,
            ClassicLayout.Max,
            ClassicLayout.TinyBorder,
            5
        )

        self.partyNameLayout.addLayout(self.partyName, 0)
        self.partyNameLayout.addWidget(self.aiBotCheck, 0, alignment=Qt.AlignmentFlag.AlignVCenter)
        self.partyNameLayout.addStretch(1)
        self.partyNameLayout.addWidget(self.confirmButton, 0)
        self.partyNameRow.setLayout(self.partyNameLayout)

        # 好友列表
        self.friendsListSection = Section(
            (420, 600),
            Section.Fixed
        )

        self.scrollableFriendsList = QScrollArea()
        self.scrollableFriendsList.setWidgetResizable(True)
        self.scrollableFriendsList.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollableFriendsList.setWidget(self.friendsListSection)

        self.friendsListLayout = ClassicLayout.Vertical(
            ClassicLayout.LTop,
            ClassicLayout.MinMax,
            ClassicLayout.TinyBorder,
            5
        )

        for i in range(len(self.friends)):
            _ = self.OptionFriendBar(
                self.friends[i].nickname,
                self.friends[i].uid
            )

            self.friendsListLayout.addWidget(_, 0, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        self.friendsListSection.setLayout(self.friendsListLayout)

        self.mainLayout = ClassicLayout.Vertical(
            ClassicLayout.CTop,
            ClassicLayout.Max,
            ClassicLayout.NoBorder,
            0
        )

        self.mainLayout.addWidget(self.partyNameRow, 0)
        self.mainLayout.addWidget(Separator(width=1))
        self.mainLayout.addWidget(self.scrollableFriendsList, 1)

        self.setLayout(self.mainLayout)

    def slotsConnect(self):
        
        self.confirmButton.clicked.connect(lambda checked: self.onConfirmButton())

    def onConfirmButton(self):
        '''点击确认按钮, 想服务器发送创建群聊请求'''

        # print("WWW")
        groupName = self.partyName.getInput()
        result = tool._is_name_not_uid(groupName)

        if not result:
            QMessageBox.warning(self, "", "群聊名称不合法")
            return

        hahahahaha = []
        for i in range(self.friendsListLayout.count()):
            
            
            uid: CreatePartyWindow.OptionFriendBar = self.friendsListLayout.itemAt(i).widget() #type: ignore
            # assert uid is CreatePartyWindow.OptionFriendBar

            if uid.selected:
                hahahahaha.append(uid.UID)

        try:
            response = CT.request_create_group(groupName, hahahahaha, with_ai=self.aiBotCheck.isChecked())
        except Exception:
            QMessageBox.warning(self, "", "服务器不给你创建群聊")
            return

        if response.get("type") != "create_group":
            QMessageBox.warning(self, "", "服务器返回类型有误")
            return

        status = response.get("status")
        if status == 4:
            QMessageBox.warning(self, "", "群聊名已存在")
            return
        if status == 5:
            QMessageBox.warning(self, "", "创建者不存在")
            return
        if status != 0:
            QMessageBox.warning(self, "", "建群失败")
            return

        self.partyName.clearInput()
        # print("chenggong?")

        self.createSuccess.emit()


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
            self.setStyleSheet("ContactBar { border: 2px solid blue; }")
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
            self.Name = ID

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

    class GroupMemberBar(QWidget):
        def __init__(self, uid: str, name: str, online: bool, is_ai: bool = False):
            super().__init__()
            self.uid = str(uid or "")
            self.name = str(name or "")
            self.online = bool(online)
            self.is_ai = bool(is_ai)
            self.initUI()

        def initUI(self):
            self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
            self.setFixedHeight(32)

            status_text = "在线" if self.online else "离线"
            role_text = " [AI]" if self.is_ai else ""
            self.nameLabel = QLabel(f"{self.name}{role_text}")
            self.nameLabel.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 10))

            self.statusLabel = QLabel(status_text)
            self.statusLabel.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
            self.statusLabel.setStyleSheet("color: #1f8f3a;" if self.online else "color: #888888;")

            layout = ClassicLayout.Horizontal(ClassicLayout.CLeft, ClassicLayout.MinMax, (8, 2, 8, 2), 4)
            layout.addWidget(self.nameLabel, 1, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            layout.addStretch(1)
            layout.addWidget(self.statusLabel, 0, alignment=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.setLayout(layout)

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

    def __init__(
            self,
            uid: str,
            name: str
    ):
        super().__init__()

        self.UserID = uid
        self.CurrentChatID: Optional[str] = None
        self.isCurrentChatGroup = False

        # 主窗口属性预设
        self.setWindowTitle("USTBChat")
        
        self.newsContactBarList = []
        self.friendsBarList = []
        self.partiesBarList = []

        self.friendNameByID: Dict[str, str] = {}
        self.groupNameByID: Dict[str, str] = {}
        self.cachedChatHistory: Dict[str, List[Message]] = {}
        self.cachedGroupMembers: Dict[str, list[dict]] = {}

        self.friendAddWindow = None
        self.partyAddWindow = None
        self.createPartyWindow = None

        # 分三个部分初始化界面
        self.initUI()

        self.modifyID('myUID', uid)
        self.modifyID('myName', name)

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

        self.rightSideBarSection.setHidden(True)

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
        self.personalInfoSection.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.personalInfoSection.customContextMenuRequested.connect(lambda pos, target=self.personalInfoSection: self.rcMenuOfPersonalInfoBar(pos, target))
        self.personalID = QLabel("ID")
        self.personalID.setFont(Fonts.UniversalPlainFont)
        self.personalUID = QLabel("UID:123456")
        self.personalUID.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
        self.quickAddFriendButton = Button("加好友", "添加好友", (92, 30), Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
        self.quickJoinGroupButton = Button("加群聊", "加入已有群聊", (92, 30), Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
        self.quickCreateGroupButton = Button("建群聊", "发起新的群聊", (92, 30), Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
        self.quickRefreshButton = Button("刷新列表", "刷新会话/好友/群聊列表", (92, 30), Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
        self.quickActionSection = Section((200, 72), Section.Fixed)

        # 消息列表切换按钮栏
        self.switchButtonSection = Section((200, 40))
        self.newsButton = Button("会话", "最新消息", (56, 34), Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        self.friendsButton = Button("好友", "好友列表", (56, 34), Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        self.partiesButton = Button("群聊", "群聊列表", (56, 34), Fonts.sizedFont(Fonts.UniversalPlainFont, 10))

        # 消息列表区域
        self.messageListSection = Section((200, 518), Section.VExtendable)
        self.newsListSection = Section((200, 518), Section.VExtendable)
        self.friendsListSection = Section((200, 518), Section.VExtendable)
        self.partiesListSection = Section((200, 518), Section.VExtendable)
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
        self.messageInputer.setPlaceholderText("输入消息内容，点击“发送”即可。")

        # 消息发送按钮
        self.messageSendButton = Button("发送", '发送当前输入消息', (90, 32), Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
    
    def creRightWidgets(self):
        '''
        创建右边区域的组件
        '''

        # 群聊名称
        self.partyName = QLabel("群聊")
        self.partyName.setFont(Fonts.UniversalPlainFont)
        self.partyUID = QLabel("GID: -")
        self.partyUID.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 12))
        self.partyMemberTitle = QLabel("群成员")
        self.partyMemberTitle.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 11))
        self.partyMemberCount = QLabel("在线 0/0")
        self.partyMemberCount.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        self.partyMemberCount.setStyleSheet("color: gray;")

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

        self.quickActionTopRow = ClassicLayout.Horizontal(ClassicLayout.Center, ClassicLayout.Default, (4, 2, 4, 2), 4)
        self.quickActionTopRow.addWidget(self.quickAddFriendButton, 0)
        self.quickActionTopRow.addWidget(self.quickJoinGroupButton, 0)
        
        self.quickActionBottomRow = ClassicLayout.Horizontal(ClassicLayout.Center, ClassicLayout.Default, (4, 0, 4, 2), 4)
        self.quickActionBottomRow.addWidget(self.quickCreateGroupButton, 0)
        self.quickActionBottomRow.addWidget(self.quickRefreshButton, 0)

        self.quickActionLayout = ClassicLayout.Vertical(ClassicLayout.CTop, ClassicLayout.Default, ClassicLayout.NoBorder, 0)
        self.quickActionLayout.addLayout(self.quickActionTopRow, 0)
        self.quickActionLayout.addLayout(self.quickActionBottomRow, 0)
        self.quickActionSection.setLayout(self.quickActionLayout)

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
        self.leftSideBarLayout.addWidget(self.quickActionSection, 0)
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
        self.scrollablePartyMembers = QScrollArea()
        self.scrollablePartyMembers.setWidgetResizable(True)
        self.scrollablePartyMembers.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scrollablePartyMembers.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.partyMemberListBody = Section((200, 500), Section.VExtendable)
        self.partyMemberListLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, (0, 0, 0, 0), 2)
        self.partyMemberListLayout.addStretch(1)
        self.partyMemberListBody.setLayout(self.partyMemberListLayout)
        self.scrollablePartyMembers.setWidget(self.partyMemberListBody)
        self.partyMemberLayout = ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, (8, 8, 8, 8), 6)
        self.partyMemberLayout.addWidget(self.partyMemberTitle, 0)
        self.partyMemberLayout.addWidget(self.partyMemberCount, 0)
        self.partyMemberLayout.addWidget(self.scrollablePartyMembers, 1)
        self.partyMemberSection.setLayout(self.partyMemberLayout)

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
        self.quickAddFriendButton.clicked.connect(lambda checked: self.openFriendAddWindow())
        self.quickJoinGroupButton.clicked.connect(lambda checked: self.openPartyAddWindow())
        self.quickCreateGroupButton.clicked.connect(lambda checked: self.openCreatePartyWindow())
        self.quickRefreshButton.clicked.connect(lambda checked: self.refresh_all_lists(show_tip=True))

        self.newsButton.clicked.connect(lambda checked: self.displayNewsContactBar())
        self.friendsButton.clicked.connect(lambda checked: self.displayFriendsBar())
        self.partiesButton.clicked.connect(lambda checked: self.displayPartiesBar())

    def _request_with_expected(self, request_fn, expected_type: str, retry: int = 5) -> dict:
        for _ in range(retry):
            try:
                response = request_fn()
            except Exception:
                response = {}
            if isinstance(response, dict) and response.get("type") == expected_type:
                return response
        return {}

    def _chat_history_key(self, uid: str, is_group: bool) -> str:
        return f"{'g' if is_group else 'u'}:{str(uid)}"

    def _resolve_chat_name(self, uid: str, is_group: bool) -> str:
        uid = str(uid)
        if is_group:
            return self.groupNameByID.get(uid, f"群聊 {uid}")
        return self.friendNameByID.get(uid, f"用户 {uid}")

    def _fetch_chat_history(self, uid: str, is_group: bool) -> List[Message]:
        history = CT.fetch_history(str(uid), is_group)
        key = self._chat_history_key(uid, is_group)
        self.cachedChatHistory[key] = history
        return history

    def refresh_group_members(self, gid: str) -> bool:
        gid = str(gid)
        response = self._request_with_expected(lambda: CT.request_group_members(gid), "group_members", retry=3)
        cleanWidgetsInLayout(self.partyMemberListLayout, left=1)

        if not response:
            self.partyMemberCount.setText("在线 ?/?")
            tip = QLabel("群成员加载失败")
            tip.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
            tip.setStyleSheet("color: #888888;")
            self.partyMemberListLayout.insertWidget(self.partyMemberListLayout.count() - 1, tip)
            return False

        members = response.get("members", [])
        if not isinstance(members, list):
            members = []
        self.cachedGroupMembers[gid] = members

        total_count = int(response.get("total_count", len(members)))
        online_count = int(response.get("online_count", sum(1 for x in members if isinstance(x, dict) and x.get("online"))))
        self.partyMemberCount.setText(f"在线 {online_count}/{total_count}")

        if not members:
            tip = QLabel("暂无成员")
            tip.setFont(Fonts.sizedFont(Fonts.UniversalPlainFont, 9))
            tip.setStyleSheet("color: #888888;")
            self.partyMemberListLayout.insertWidget(self.partyMemberListLayout.count() - 1, tip)
            return True

        for item in members:
            if not isinstance(item, dict):
                continue
            bar = self.GroupMemberBar(
                uid=str(item.get("uid", "")),
                name=str(item.get("nickname") or item.get("name") or ""),
                online=bool(item.get("online")),
                is_ai=bool(item.get("is_ai")),
            )
            self.partyMemberListLayout.insertWidget(self.partyMemberListLayout.count() - 1, bar)

        self.partyMemberListLayout.update()
        return True

    def modifyID(self, type: str, value: str):
        '''
        非用户输入, 因此可以不检测值是否合法

        Args:
            type(str): myUID, myName, groupUID, groupName
        '''

        # print(type, ":", value)

        if type == 'myUID':
            self.personalUID.setText("UID: " + value)
        elif type == 'myName':
            self.personalID.setText(value)
        elif type == 'groupUID':
            self.partyUID.setText(value)
        elif type == 'groupName':
            self.partyName.setText(value)
        else:
            raise ValueError("不存在的类型")

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

        response = self._request_with_expected(CT.request_contacts_list, "contacts_list")
        
        # 解析服务器消息
        if not response:
            return False
        
        # 将Contact转换为能直接用的ContactBar
        cleanWidgetsInLayout(self.newsListLayout, left=1)
        self.newsContactBarList = []
        self.friendNameByID.clear()
        self.groupNameByID.clear()
        for x in response['contacts']:

            aContact = Contact(
                x['id'],
                x['name'],
                x['is_group'],
                x['last_message'],
                x['last_time'],
                int(x.get('unread', 0))
            )
            if bool(aContact.is_group):
                self.groupNameByID[str(aContact.id)] = str(aContact.name)
            else:
                self.friendNameByID[str(aContact.id)] = str(aContact.name)

            _ = contactToBar(aContact)
            _.hasBeenClicked.connect(lambda uid = _.UID, isGroup = _.Type: self.showSpecificChatArea(uid, isGroup))
            self.newsContactBarList.append(_)
        # self.newsContactBarList[0].printInfo()

        self.displayNewsContactBar()

        for i in range(len(self.newsContactBarList)):
            self.newsListLayout.insertWidget(self.newsListLayout.count() - 1, self.newsContactBarList[i])
        
        return True

    def getFriendsListFromServer(self) -> bool:
        response = self._request_with_expected(CT.request_friend_list, "friend_list")

        # 解析服务器消息
        if not response:
            return False
        
        cleanWidgetsInLayout(self.friendsListLayout, left=1)
        self.friendsBarList.clear()
        self.friendNameByID.clear()

        # 转换为Bar
        # self.friendsBarList = [friendToBar(x) for x in response['friends']]
        for x in response['friends']:

            aFriend = Friend(
                x['uid'],
                x['nickname']
            )
            self.friendNameByID[str(aFriend.uid)] = str(aFriend.nickname)

            _ = friendToBar(aFriend)
            _.hasBeenClicked.connect(lambda uid = _.UID, isGroup = False: self.showSpecificChatArea(uid, isGroup))
            self.friendsBarList.append(_)

        for i in range(len(self.friendsBarList)):
            self.friendsListLayout.insertWidget(self.friendsListLayout.count() - 1, self.friendsBarList[i])

        return True

    def getGroupsListFromServer(self) -> bool:
        response = self._request_with_expected(CT.request_group_list, "group_list")

        # 解析服务器消息
        if not response:
            return False
        
        # 转换为Bar
        # self.partiesBarList = [partyToBar(x) for x in response['groups']]

        cleanWidgetsInLayout(self.partiesListLayout, left=1)
        self.partiesBarList.clear()
        self.groupNameByID.clear()

        for x in response['groups']:

            aGroup = Group(
                x['gid'],
                x['name'],
                None
            )
            self.groupNameByID[str(aGroup.gid)] = str(aGroup.name)

            _ = partyToBar(aGroup)
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

    def onReceivedMessage(self, chatUID: str, msg: Message, isGroup: bool = False) -> bool:
        '''
        当接收到新消息后执行
        判断该消息是否为当前打开的Chat, 若是则直接刷新, 若否, 仅加入到消息缓存中

        Args:
            chatUID(str): 聊天对象的UID, 若是私聊消息则为消息发送人的UID, 若是群聊消息则为群聊的GID
            msg(Message): 接收到的消息对象

        Returns:
            bool: 执行成功与否
        '''
        
        chatUID = str(chatUID)
        chat_key = self._chat_history_key(chatUID, isGroup)

        # 先加入到缓存中
        if chat_key not in self.cachedChatHistory:
            self._fetch_chat_history(chatUID, isGroup)
            if self.CurrentChatID == chatUID and self.isCurrentChatGroup == bool(isGroup):
                self.showSpecificChatArea(chatUID, bool(isGroup))
            return True

        chatQuote: List[Message] = self.cachedChatHistory.setdefault(chat_key, [])
        chatQuote.append(msg)

        # 仅当前会话打开时才直接渲染
        if self.CurrentChatID == chatUID and self.isCurrentChatGroup == bool(isGroup):
            row = self.generateChatRowSection(msg)
            self.messageDisplayLayout.addWidget(row)
            scrollBar = self.scrollableMessageLayout.verticalScrollBar()
            scrollBar.setValue(scrollBar.maximum())
            self.messageDisplayLayout.update()
            if isGroup:
                self.refresh_group_members(chatUID)

        return True

    @Slot(str, bool)
    def showSpecificChatArea(self, UID: str, isGroup: bool):

        # import bin.tool.ContactTool as CTool

        UID = str(UID)
        self.CurrentChatID = UID
        self.isCurrentChatGroup = bool(isGroup)

        # 若是私聊, 则隐藏右边的区域
        if not isGroup:
            self.rightSideBarSection.setHidden(True)
        else:
            self.rightSideBarSection.setHidden(False)
            self.modifyID('groupUID', f"GID: {UID}")
            self.modifyID('groupName', self._resolve_chat_name(UID, True))
            self.refresh_group_members(UID)

        # 清空聊天区域
        wipeOutChildItemOfLayout(self.messageDisplayLayout)

        # 缓存中不存在该UID, 则向服务器请求获取聊天记录
        chat_key = self._chat_history_key(UID, bool(isGroup))
        if chat_key not in self.cachedChatHistory:
            self._fetch_chat_history(UID, bool(isGroup))

        # 向缓存中读取聊天记录
        chatUpcoming = self.cachedChatHistory.get(chat_key, [])

        # 将聊天记录转换为可使用的Qt组件
        for i in range(len(chatUpcoming)):
            
            chatRowSection = self.generateChatRowSection(chatUpcoming[i])

            # self.messageDisplayLayout.addLayout(chatRowLayout, 0)
            self.messageDisplayLayout.addWidget(chatRowSection, 0)
        
        # self.messageDisplayLayout.addStretch(1)
        self.messageDisplayLayout.update()
        scrollBar = self.scrollableMessageLayout.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
            
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
            
        from bin.state.ChatModels import Message
        
        sendContent = text

        sendSuccess = CT.send_message(
            self.CurrentChatID,
            sendContent,
            self.isCurrentChatGroup
        )

        if not sendSuccess:
            QMessageBox.warning(self, "", "发送失败")
            return
        
        # 发送成功, 在本地显示自己发送的消息

        msg = Message(
            sender_uid=self.UserID,
            sender_nickname=self.personalID.text(),
            content=sendContent,
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            is_self=True
        )

        try:
            assert self.CurrentChatID is not None
            cache_key = self._chat_history_key(self.CurrentChatID, self.isCurrentChatGroup)
            historyQuote: List[Message] = self.cachedChatHistory[cache_key]
        except Exception:
            historyQuote = self._fetch_chat_history(str(self.CurrentChatID), self.isCurrentChatGroup)
        
        self.messageInputer.clear()
        historyQuote.append(msg)
        
        _ = self.generateChatRowSection(msg)
        self.messageDisplayLayout.addWidget(_)
        scrollBar = self.scrollableMessageLayout.verticalScrollBar()
        scrollBar.setValue(scrollBar.maximum())
        self.messageDisplayLayout.update()

    def refresh_all_lists(self, show_tip: bool = False):
        ok_contacts = self.initContactList()
        ok_friends = self.getFriendsListFromServer()
        ok_groups = self.getGroupsListFromServer()

        if self.CurrentChatID:
            self._fetch_chat_history(self.CurrentChatID, self.isCurrentChatGroup)
            self.showSpecificChatArea(self.CurrentChatID, self.isCurrentChatGroup)

        if show_tip:
            if ok_contacts and ok_friends and ok_groups:
                QMessageBox.information(self, "", "列表刷新完成")
            else:
                QMessageBox.warning(self, "", "部分列表刷新失败，请检查网络后重试")

    @Slot()
    def rcMenuOfPersonalInfoBar(self, pos, target):

        menu = QMenu(self)

        actionAddFriend = QAction("添加好友", self)
        actionAddParty = QAction("添加群聊", self)
        actionCreateParty = QAction("发起群聊", self)

        actionAddFriend.triggered.connect(lambda checked: self.openFriendAddWindow())
        actionAddParty.triggered.connect(lambda checked: self.openPartyAddWindow())
        actionCreateParty.triggered.connect(lambda checked: self.openCreatePartyWindow())

        menu.addAction(actionAddFriend)
        menu.addSeparator()
        menu.addAction(actionAddParty)
        menu.addSeparator()
        menu.addAction(actionCreateParty)

        menu.exec(target.mapToGlobal(pos))

    def openFriendAddWindow(self):

        if self.friendAddWindow != None:
            if not self.friendAddWindow.isVisible():
                self.friendAddWindow.show()
        else:
            self.friendAddWindow = AddFriendPartyWindow(True)
            self.friendAddWindow.addSuccess.connect(lambda: self.refresh_all_lists(show_tip=False))
            self.friendAddWindow.show()
        return
    
    def openPartyAddWindow(self):
        
        if self.partyAddWindow != None:
            if not self.partyAddWindow.isVisible():
                self.partyAddWindow.show()
        else:
            self.partyAddWindow = AddFriendPartyWindow(False)
            self.partyAddWindow.addSuccess.connect(lambda: self.refresh_all_lists(show_tip=False))
            self.partyAddWindow.show()
        return

    def openCreatePartyWindow(self):

        if self.createPartyWindow != None:
            if not self.createPartyWindow.isVisible():
                self.createPartyWindow.show()
        else:

            friendsList = [Friend(x.UID, x.Name) for x in self.friendsBarList]

            self.createPartyWindow = CreatePartyWindow(friendsList)
            self.createPartyWindow.createSuccess.connect(lambda: self.refresh_all_lists(show_tip=False))
            self.createPartyWindow.show()
        return

def cleanWidgetsInLayout(layout: QLayout, left: int = 0):
    '''清理布局中的组件, 但保留最后left数量的组件'''

    if layout is None:
        return

    remove_count = max(0, layout.count() - left)
    for _ in range(remove_count):
        item: QLayoutItem = layout.takeAt(0)  # type: ignore
        if item is None:
            continue

        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
            continue

        sub_layout = item.layout()
        if sub_layout is not None:
            wipeOutChildItemOfLayout(sub_layout, delete_layout_itself=True)
            continue

        # spacer item: takeAt后无需额外处理

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
        item: QLayoutItem = layout.takeAt(0) #type: ignore
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
    Window = MainWindow("A", "123456")
    Window.show()
    MMApp.exec()
