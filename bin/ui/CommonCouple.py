# -*- coding: utf-8 -*-

'''
一些常见的Qt组件的组合
提取出来方便代码复用
'''

from typing import Tuple
from PySide6.QtWidgets import (QLayout, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QLabel, QSizePolicy, QLineEdit,
                               QFrame)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt

class Fonts:
    '''
    常用跨平台字体家族
    '''
    
    UniversalPlainFont = QFont("Segoe UI, Arial, Liberation Sans, DejaVu Sans, sans-serif", 16)             # 用于界面显示
    MonospacedCodeFont = QFont("Consolas, Courier New, Liberation Mono, DejaVu Sans Mono, monospace", 16)   # 用于代码编写
    SerifPrintFont = QFont("Times New Roman, Liberation Serif, DejaVu Serif, serif", 16)                    # 用于打印阅读

    @classmethod
    def sizedFont(cls, font: QFont, size: int):
        '''
        返回修改过大小的字体

        Args:
            font(QFont): 字体
            size(int): 字体大小
        
        Returns:
            QFont: 字体类
        
        Raises:
            None
        '''

        font.setPointSize(size)
        return font

class TextInput(QHBoxLayout):
    '''
    横向输入框, 由描述和输入框组成
    '''

    Hidden = 0
    Displayed = 1

    def __init__(self, text: str, phText: str = '', mode: int = 1, size: Tuple[int, int] = (400, 40) , font: QFont = Fonts.UniversalPlainFont):
        '''
        创建QLabel和QLineEdit组件并应用至布局

        Args:
            text(str): 标签内容
            phText(str): 占位符文本内容
            mode(int): 输入框显示模式, Hidden是隐藏, Displayed是显示
            size(Tuple[int, int]): 文本输入框尺寸
            font(QFont): 标签及文本输入框的字体
        
        Returns:
            None: 该函数没有返回值
        
        Raises:
            参数mode非 0, 1 时抛出ValueError错误
        '''
        super().__init__()

        # 创建并设置标签组件
        qText = QLabel(text)
        qText.setFont(font)
        qText.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        # 创建并设置文本输入框组件
        qInput = QLineEdit()
        qInput.setFont(font)
        qInput.setPlaceholderText(phText)
        qInput.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        qInput.setFixedSize(size[0], size[1])

        if mode == self.Hidden:
            qInput.setEchoMode(QLineEdit.EchoMode.Password)
        elif mode == self.Displayed:
            qInput.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            raise ValueError("参数mode超出范围")

        # 定义获取输入值的函数
        self.getInput = lambda: qInput.text()

        # 设置布局属性
        self.setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(0)

        # 添加组件
        self.addWidget(qText, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        self.addWidget(qInput, 0, alignment=Qt.AlignmentFlag.AlignLeft)

class Button(QPushButton):
    '''
    按钮
    '''

    def __init__(self, text: str, tip: str = '', size: Tuple[int, int] = (200, 40), font: QFont = Fonts.UniversalPlainFont):
        '''
        设置按钮组件的属性

        Args:
            text(str): 按钮上显示的文本
            tip(str): 按钮工具提示, 悬浮文本
            size(Tuple[int, int]): 按钮的尺寸
            font(QFont): 按钮上文本的字体
        
        Returns:
            None
        
        Raises:
            None
        '''
        super().__init__()

        self.setFont(Fonts.UniversalPlainFont)
        self.setText(text)
        self.setToolTip(tip)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(size[0], size[1])

class Section(QWidget):
    '''
    一个专门用于承载布局的空白组件, 用于在多布局的复杂情况中把布局换位组件, 减少排版复杂度
    '''

    Fixed = (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
    Limited = (QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
    HExtendable = (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.Fixed)
    VExtendable = (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.MinimumExpanding)
    Extendable = (QSizePolicy.Policy.MinimumExpanding, QSizePolicy.Policy.MinimumExpanding)

    def __init__(self, size: Tuple[int, int] = (400, 400),
                 policy:  Tuple[QSizePolicy.Policy, QSizePolicy.Policy] = (QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)):
        super().__init__()

        self.setSizePolicy(policy[0], policy[1])
        self.setMinimumSize(size[0], size[1])

        if policy == self.Fixed:
            self.setFixedSize(size[0], size[1])
        elif policy == self.HExtendable:
            self.setFixedHeight(size[1])
        elif policy == self.VExtendable:
            self.setFixedWidth(size[0])

class ClassicLayout():
    '''
    经典布局
    '''

    # 常用对其方式
    Left = Qt.AlignmentFlag.AlignLeft
    Right = Qt.AlignmentFlag.AlignRight
    Top = Qt.AlignmentFlag.AlignTop
    Bottom = Qt.AlignmentFlag.AlignBottom
    Center = Qt.AlignmentFlag.AlignCenter
    HCenter = Qt.AlignmentFlag.AlignHCenter
    VCenter = Qt.AlignmentFlag.AlignVCenter
    CTop = Top | HCenter
    CBottom = Bottom | HCenter
    CLeft = Left | VCenter
    CRight = Right | VCenter
    LTop = Left | Top

    # 常用约束
    Default = QLayout.SizeConstraint.SetDefaultConstraint
    Max = QLayout.SizeConstraint.SetMaximumSize
    Min = QLayout.SizeConstraint.SetMinimumSize
    MinMax = QLayout.SizeConstraint.SetMinAndMaxSize
    No = QLayout.SizeConstraint.SetNoConstraint
    Fixed = QLayout.SizeConstraint.SetFixedSize

    # 常用边界间距
    NoBorder = (0, 0, 0, 0)
    SmallBorder = (20, 20, 20, 20)
    LargeBorder = (40, 40, 40, 40)

    class Horizontal(QHBoxLayout):
        '''
        水平布局
        '''

        def __init__(self, align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, constr: QLayout.SizeConstraint = QLayout.SizeConstraint.SetDefaultConstraint, margins: Tuple[int, int, int, int] = (0, 0, 0, 0), spacing: int = 0):
            '''
            设置常用的布局属性

            Args:
                align(AlignmentFlag): 对其方向
                constr(SizeConstraint): 尺寸约束
                margins(Tuple[int, int, int, int]): 组件距边界距离
                spacing(int): 内部组件间距离
            
            Returns:
                None

            Raises:
                None
            '''
            super().__init__()

            self.setAlignment(align)
            self.setSizeConstraint(constr)
            self.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
            self.setSpacing(spacing)

    class Vertical(QVBoxLayout):
        '''
        垂直布局
        '''

        def __init__(self, align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft, constr: QLayout.SizeConstraint = QLayout.SizeConstraint.SetDefaultConstraint, margins: Tuple[int, int, int, int] = (0, 0, 0, 0), spacing: int = 0):
            '''
            设置常用的布局属性

            Args:
                align(AlignmentFlag): 对其方向
                constr(SizeConstraint): 尺寸约束
                margins(Tuple[int, int, int, int]): 组件距边界距离
                spacing(int): 内部组件间距离
            
            Returns:
                None

            Raises:
                None
            '''
            super().__init__()

            self.setAlignment(align)
            self.setSizeConstraint(constr)
            self.setContentsMargins(margins[0], margins[1], margins[2], margins[3])
            self.setSpacing(spacing)

class Separator(QFrame):
    '''
    用于在布局内生成分隔符
    '''

    # 方向
    Vertical = QFrame.Shape.VLine
    Horizontal = QFrame.Shape.HLine

    # 阴影
    Sunken = QFrame.Shadow.Sunken

    # 样式
    LightDark = "background-color: #3f3f3f;"

    def __init__(self, direct: QFrame.Shape = Horizontal, width: int = 3, shadow: QFrame.Shadow = Sunken, style: str = LightDark):
        '''
        设置分隔符属性

        Args:
            direct(QFrame.Shape): 分隔符方向, 垂直或水平
            width(int): 分隔符的粗细
            shadow(QFrame.Shadow): 分隔符阴影类型
            style(str): 分隔符的样式表
        
        Returns:
            None or Self
        
        Raises:
            当输入的direct参数非两种预设时抛出ValueError错误
        '''

        super().__init__()

        self.setFrameShape(direct)
        self.setFrameShadow(shadow)
        self.setFixedHeight(width)
        self.setStyleSheet(style)
