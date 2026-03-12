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
from PySide6.QtGui import QTextOption
from PySide6.QtCore import Qt, Slot, QObject, Signal
from CommonCouple import Section, Fonts, Button, ClassicLayout, Separator

# 新增引入状态管理和消息模型
# from bin.state.AppState import AppState
from bin.state.ChatModels import Message, Contact
from bin.tool.LoginTool import LoginWindowTool as tool
from bin.tool.UserInterfaceTool import UserInterfaceTool as UITool

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
        
        Party = True
        Friend = False

        def __init__(self, type: bool, UID: str, ID: str = "DefaultID", isRead: bool = True, lastTime: str = "00:00", lastChat: str = "DefaultChat"):
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
            self.initUI()
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
    class ChatBar(QWidget):
        '''
        显示在聊天区域的聊天块
        '''

        def __init__(self, isSelf: bool):
            '''
            Args:
                isSelf(bool): 消息是否为自己发出的
            '''
            super().__init__()

            self.isSelf = isSelf
        
        def initUI(self):

            self.setSizePolicy(QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Maximum)
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
            self.chatContent.setWordWrapMode(QTextOption.WrapMode.WordWrap)
            self.chatContent.setReadOnly(True)
            self.chatContent.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.chatContent.setMinimumWidth(200)
            if self.isSelf: self.chatContent.setStyleSheet("background-color: #868686")
            
        def applyLayout(self):

            self.chatCubeLayout = ClassicLayout.Vertical(ClassicLayout.RTop, ClassicLayout.MinMax, (20, 0, 20, 0), 5) if self.isSelf else ClassicLayout.Vertical(ClassicLayout.LTop, ClassicLayout.MinMax, (20, 0, 20, 0), 5)
            self.chatCubeLayout.addWidget(self.chatSendTime, 0)
            self.chatCubeLayout.addWidget(self.chatSenderID, 0)
            self.chatCubeLayout.addWidget(self.chatContent, 1)
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

        # 主窗口属性预设
        self.setWindowTitle("USTBChat")
        
        self.newsContactBarList = []

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
    
    def displayNewsContactBar(self):
        '''将左侧边栏下方改为显示最新消息'''

        # 清空左侧边栏
        cleanWidgetsInLayout(self.newsListLayout, 1)

        # 加载
        for i in range(len(self.newsContactBarList)):
            self.newsListLayout.insertWidget(-1, self.newsContactBarList[i])
        
        self.newsListLayout.update()

    def initContactList(self) -> bool:
        '''登录后, 从服务器获取消息对象列表, 并显示在左侧边栏'''

        import bin.tool.ContactTool as CT

        response = dict()
        # 向服务器获取
        while ():
            try:
                response = CT.request_contacts_list()
            except:
                continue
            
            break
        
        # 解析服务器消息
        if not response['type'] != 'contacts_list':
            return False
        
        # 将Contact转换为能直接用的ContactBar
        self.newsContactBarList = [contactToBar(x) for x in response['contacts']]

        self.displayNewsContactBar()
        
        return True

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
    
    def slotsConnect(self):
        '''绑定UI交互事件'''
        # 将“发送”按钮的点击事件连接到 send_message 函数
        self.messageSendButton.clicked.connect(self.send_message)

    @Slot()
    def send_message(self):
        '''处理发送按钮点击事件'''
        # 获取输入框的纯文本
        text = self.messageInputer.toPlainText().strip()
        if not text:
            return # 没写字就不发
            
        # from bin.state.AppState import AppState
        from bin.state.ChatModels import Message

        # my_uid = AppState().uid
        
        # 注意：由于目前左侧列表没做好，我们暂时无法通过点击来“选中”好友。
        # 为了让代码跑通，我们先强行指定一个目标好友 (建议去 MySQL 注册一个名为 test 的账号用来测试)
        target_friend = "test" 

        # 构造符合《通信接口.md》规范的报文
        # packet = {
        #     "type": "message",
        #     "username": my_uid,
        #     "friendname": target_friend,
        #     "message": text
        # }
        
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
        layout.takeAt(0)

def contactToBar(contact: Contact) -> MainWindow.ContactBar:
    return MainWindow.ContactBar(
        type=contact.is_group,
        UID=contact.id,
        ID=contact.name,
        isRead=(contact.unread == 0),
        lastTime=UITool.format_msg_time(contact.last_time),
        lastChat=contact.last_message
    )


if __name__ == '__main__':
    MMApp = QApplication(sys.argv)
    Window = MainWindow()
    Window.show()
    MMApp.exec()


