# -*- coding: utf-8 -*-

import os
from pathlib import Path

from PySide6.QtWidgets import (QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLayout, QSizePolicy, QLineEdit)

class LoginWindow(QWidget):
    '''
    * 外观
    登录窗口, 继承自QWidget
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

