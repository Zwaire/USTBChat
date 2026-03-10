# -*- coding: utf-8 -*-

'''
本文件用以定义各种消息的格式, 如函数间传递消息、进程间传递消息和客户端服务端通信消息
'''

class LoginInfo:
    '''
    用于本地函数间, 客户端与服务端间
    登录信息, 存储用户的登录或注册请求
    '''

    def __init__(
            self,
            mode: int,
            id: str,
            password: str,
            ):
        '''
        Args:
            mode(int): 该请求的类型, 0表示登录, 1表示注册
            id(str): 用户的昵称或UID
            password(str): 用户的密码
        '''
        
        self.Mode = mode
        self.ID = id
        self.Password = password


