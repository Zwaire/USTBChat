import re
import os
import hashlib
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from bin.MessageFormat import LoginInfo
import core.protocol as protocol

MAX_LEN = 20
_RE_UID      = re.compile(r'^\d+$')
_RE_NICKNAME = re.compile(r'^[\u4e00-\u9fa5A-Za-z0-9_]+$')
_RE_PASSWORD = re.compile(r'^[A-Za-z0-9_/\.]+$')

class LoginWindowTool:
    def __init__(self):
        pass
    @classmethod
    def _validate_id(cls, text: str) -> str | bool:
        """
        检查输入的字符串是否符合账户ID或昵称的要求
        Args:
            text (str): 待检查的字符串
        Returns:
            str | bool: 合法返回True,否则返回错误信息
        """
        if not text:
            return "账户不能为空"
        if len(text) > MAX_LEN:
            return f"账户长度不能超过 {MAX_LEN} 个字符"
        if _RE_UID.match(text):          # 纯数字 → UID，合法
            return True
        if text[0].isdigit():
            return "昵称不能以数字开头"
        if not _RE_NICKNAME.match(text):
            return "昵称只能包含汉字、英文字母、数字、下划线"
        return True
    
    @classmethod
    def _validate_password(cls, text: str) -> str | bool:
        '''
        检查输入的字符串是否符合密码的要求
        '''
        if not text:
            return "密码不能为空"
        if len(text) > MAX_LEN:
            return f"密码长度不能超过 {MAX_LEN} 个字符"
        if not _RE_PASSWORD.match(text):
            return "密码只能包含英文字母、数字、下划线、斜杠、英文句点"
        return True
    
    @classmethod
    def _is_uid(cls,text: str) -> bool:
        return bool(_RE_UID.match(text))
    
    @classmethod
    def _pwd_encryption(cls, text: str) -> str:
        """
        对密码进行派生哈希处理并返回字符串结果。
        Args:
            test(str):等待加密的明文密码
        Returns:
            str:加密后的密码字符串，格式为 "salt$derived_key"，其中 salt 和 derived_key 都是十六进制字符串。
        采用核心的 PBKDF2-HMAC-SHA256 加密算法。
        其中 salt 是盐，可以认为是双方共有的随机值，服务器端应保存注册时使用的盐以供登录时验证。
        pepper 是一个额外的安全参数，是双方共同规定的一个固定字符串，目前默认使用"USTBChat_Default_Pepper_ChangeMe"
        derived_key 是派生的密钥，基于输入的密码、盐和一个固定的 pepper 进行计算。
        在登录的时候验证利用服务器存储的 salt 和相同的 pepper 
        """
        if not text:
                return ""

        # 客户端固定的 pepper，应通过安全配置注入环境变量以便更换
        PEPPER = os.environ.get("USTBCHAT_PWD_PEPPER", "USTBChat_Default_Pepper_ChangeMe")

        # 随机盐，注册时应保存到服务器；登录时需与服务器协商使用相同盐
        salt = os.urandom(16)

        # 使用 PBKDF2-HMAC-SHA256 进行密钥派生
        dk = hashlib.pbkdf2_hmac(
                'sha256',
                text.encode('utf-8'),
                salt + PEPPER.encode('utf-8'),
                100_000
        )

        return salt.hex() + '$' + dk.hex()

    def _get_response(self, request: dict) -> dict:
        '''
        发送请求到服务器，并获取响应
        Args:
            request (dict): 待发送的请求数据，包含请求类型、用户名、IP等信息
        Returns:
            dict: 服务器返回的响应数据，包含是否成功、错误信息等
        '''

        return

    def _request_pwd_find(self, id: str) -> dict:
        ''' 向服务器发送请求，发送id进行查验 '''
        request = {
            "type": "request_pwd_find",
            "username": id,
            "ip": LoginInfo._get_localip()
        }
        response = self._get_response(request)
        return response  

    def _send_login_info(self, info: LoginInfo) -> dict | bool:
        ''' 
        向服务器发送登录信息，错误会返回名为"error"的键，成功则返回服务器响应的字典
        '''
        _pwd = info.Password

        # 对密码进行客户端派生加密（返回格式为 "salt$derived_key"）
        encrypted = self._pwd_encryption(_pwd)
        if not encrypted:
            return {"error": "empty password"}

        # 尝试拆分 salt 和 hash
        if '$' in encrypted:
            salt_hex, dk_hex = encrypted.split('$', 1)
        else:
            return {"error": "password error"}

        # 构建发送到服务器的请求体
        request = {
            "type": "login",
            "mode": getattr(info, 'Mode', 0),
            "username": getattr(info, 'ID', ''),
            "hash": dk_hex,
            "ip": LoginInfo._get_localip()
        }

        response = self._get_response(request)
        if not response:
            return {"error": "no response from server"}
        else:
            return response