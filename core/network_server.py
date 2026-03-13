'''
负责处理用户的上线、下线，保存用户的用户名和 IP，并将消息广播或定向发送 。
'''
import socket
import threading
from core.protocol import encode_msg, decode_msg
from utils.logger import get_logger

import threading
from datetime import datetime
# from ai_client import AIServiceClient

# 引入 ustbchat 的数据库操作模块
from data import data as db

logger = get_logger("Server")

class ChatServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # 使用TCP协议
        self.server_socket.bind((self.host, self.port)) # 绑定地址和端口
        self.server_socket.listen(10) # 最大接受的等待连接数
        # 记录在线用户 {username: {"conn": socket, "ip": ip_addr}}
        self.clients = {}
        self.lock = threading.Lock()
        # self.ai_client = AIServiceClient("http://192.168.182.128:5001", timeout=60)
        self.ai_name = "智能助手"

    def normalize_friend_list(self, data):
        result = []
        for item in data:
            uid = item.get("uid")
            nickname = item.get("nickname")
            if uid is not None:
                result.append({
                    "uid": str(uid),
                    "nickname": str(nickname) if nickname is not None else str(uid)
                })
        return result

    def normalize_group_list(self, data):
        result = []
        for item in data:
            gid = item.get("gid")
            name = item.get("name")
            if gid is not None:
                result.append({
                    "gid": str(gid),
                    "name": str(name) if name is not None else str(gid)
                })
        return result

    def build_contacts(self, friends, groups):
        # [TODO] 是否能够实现对于消息和时间的提取？
        contacts = []
        for item in friends:
            contacts.append({
                "id": item.get("uid"),
                "name": item.get("nickname"),
                "is_group": False,
                "last_message": "",
                "last_time": "",
                "unread": 0
            })
        for item in groups:
            contacts.append({
                "id": item.get("gid"),
                "name": item.get("name"),
                "is_group": True,
                "last_message": "",
                "last_time": "",
                "unread": 0
            })
        return contacts
    
    # 初始化监听Socket，用于TCP连接
    def start(self):
        logger.info(f"Server started, listening on {self.host}:{self.port}, waiting for connections...")
        try:
            while True:
                conn, addr = self.server_socket.accept() # TCP握手协议，成功后返回（新的用于传输数据的socket，连接的IP），原本的socket用于监听
                # 为该数据传输socket建立守护线程（守护线程：当主线程退出时，Python 会强制杀死所有守护线程，程序立刻结束（意味着当server被终止时所有client将失去连接）；否则，主线程必须的确认所有非守护线程结束后才能退出）
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Server shut down.")
            self.server_socket.close()

    # 处理来自客户端的请求与信息
    def handle_client(self, conn, addr):
        current_user = None
        try:
            while True:
                msg = decode_msg(conn)
                if not msg:
                    break

                msg_type = msg.get("type")

                if msg_type == "add_friend" and msg.get("friendname") is None and msg.get("target") is not None:
                    msg["friendname"] = msg.get("target")

                if msg_type == "group_message" and msg.get("groupname") is None and msg.get("friendname") is not None:
                    msg["groupname"] = msg.get("friendname")

                if msg_type == "group_message" and msg.get("groupmessage") is None and msg.get("message") is not None:
                    msg["groupmessage"] = msg.get("message")

                if msg_type == "group_message" and msg.get("time") is None:
                    msg["time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                if (msg_type == "create_group" or msg_type == "join_group" or msg_type == "leave_group" or msg_type == "get_group_members") and msg.get(
                        "groupname") is None and msg.get("gid") is not None:
                    msg["groupname"] = msg.get("gid")

                if (msg_type == "fetch_history" or msg_type == "get_history" or msg_type == "history") and msg.get(
                        "target") is None and msg.get("target_id") is not None:
                    msg["target"] = msg.get("target_id")

                # 1. 注册请求
                if msg_type == "register":
                    username = msg.get("username")
                    code = msg["code"]
                    parts = code.split('$', 1)  # split(分隔符, 最大拆分次数)
                    if len(parts) == 2:
                        salt_hex = parts[0]  # 第一部分：盐值的十六进制字符串
                        dk_hex = parts[1]    # 第二部分：派生密钥的十六进制字符串
                    else:
                        salt_hex = ""
                        dk_hex = ""
                        print("错误：拼接字符串格式不正确，缺少分隔符 $")
                    print(dk_hex)
                    print(salt_hex)

                    res = db.register(username, dk_hex, salt_hex)
                    # status: 0为成功，1为已存在
                    conn.sendall(encode_msg(res))

                # 2. 登录需求返回密码salt
                elif msg_type=="seed":
                    username=msg.get("username")
                    res=db.seed(username)
                    conn.sendall(encode_msg(res))

                # 3. 找回密码的请求
                elif msg_type=="request_pwd_find":
                    username=msg.get("username")
                    res=db.request_pwd_find(username)
                    if res.get("status")==0:
                        parts = msg.get("code").split('$', 1)  # split(分隔符, 最大拆分次数) #type: ignore
                        if len(parts) == 2:
                            salt_hex = parts[0]  # 第一部分：盐值的十六进制字符串
                            dk_hex = parts[1]    # 第二部分：派生密钥的十六进制字符串
                        print(dk_hex)
                        print(salt_hex)
                        db.change_code(msg.get("username"), dk_hex,salt_hex)
                        conn.sendall(encode_msg(res))
                    else:
                        conn.sendall(encode_msg(res))

                # 4. 登录请求
                elif msg_type == "login":
                    username = msg.get("username")
                    print(username)
                    code = msg.get("code")
                    res = db.log_in(username, code, addr[0])
                    # status: 0为成功，2为密码错误等
                    if res.get("status") == 0:
                        print("password correct")
                        current_user = username
                        with self.lock: 
                            self.clients[current_user] = {"conn": conn, "ip": addr[0]}
                        logger.info(f"User {current_user} ({addr[0]}) connected.")
  
                        conn.sendall(encode_msg(res))
                    else:
                        conn.sendall(encode_msg(res))

                # 5. 添加好友
                elif msg_type == "add_friend":
                    res = db.add_friend(msg.get("username"), msg.get("friendname"))
                    conn.sendall(encode_msg(res))

                # 6. 私聊消息
                elif msg_type == "message":
                    sender = msg.get("username")
                    target = msg.get("friendname")
                    content = msg.get("message")
                    # 保存到数据库
                    print(self.clients)
                    db.save_message(sender, target, content)
                    # 转发给目标用户
                    self.send_private(target, msg)
                    threading.Thread(
                        target=self.handle_ai_private,
                        args=(sender, target, content, msg),
                        daemon=True
                    ).start()
                # 7. 群聊消息
                elif msg_type == "group_message":
                    sender = msg.get("username")
                    groupname = msg.get("groupname")
                    content = msg.get("groupmessage")
                    # 保存到数据库
                    db.save_group_message(sender, groupname, content)
                    # 群聊广播逻辑 (遍历群成员发送)
                    self.broadcast(msg)
                    threading.Thread(
                        target=self.handle_ai_group,
                        args=(sender, groupname, content, msg),
                        daemon=True
                    ).start()
                # 8. 获取好友列表
                elif msg_type == "get_friend_list":
                    username = msg.get("username")
                    if username is None:
                        username = current_user
                    res = db.get_friends(username)
                    res = self.normalize_friend_list(res)
                    # print('=====测试有没有进入=====================')
                    conn.sendall(encode_msg({
                        "type": "friend_list",
                        "friends": res
                    }))

                # 9. 获取群列表
                elif msg_type == "get_group_list":
                    username = msg.get("username")
                    if username is None:
                        username = current_user
                    res = db.get_group_list(username)
                    res = self.normalize_group_list(res)
                    conn.sendall(encode_msg({
                        "type": "group_list",
                        "groups": res
                    }))

                # 10. 获取联系人列表
                elif msg_type == "get_contacts_list":
                    username = msg.get("username")
                    if username is None:
                        username = current_user
                    friends = db.get_friends(username)
                    groups = db.get_group_list(username)
                    friends = self.normalize_friend_list(friends)
                    groups = self.normalize_group_list(groups)
                    contacts = self.build_contacts(friends, groups)
                    conn.sendall(encode_msg({
                        "type": "contacts_list",
                        "contacts": contacts
                    }))

                # 11. 建群
                elif msg_type == "create_group":
                    username = msg.get("username")
                    if username is None:
                        username = current_user
                    groupname = msg.get("groupname")
                    res = db.create_group(groupname, username)

                    if res.get("status") == 0:
                        uids = msg.get("uids", [])
                        
                        for uid in uids:
                            member_name = db.get_username_by_uid(uid)
                            if member_name and member_name != username:
                                db.add_group_member(groupname, member_name)

                    conn.sendall(encode_msg(res))

                # 12. 加入群
                elif msg_type == "join_group":
                    username = msg.get("username")
                    if username is None:
                        username = current_user
                    groupname = msg.get("groupname")
                    res = db.add_group_member(groupname, username)

                    conn.sendall(encode_msg(res))

                # 13. 退群
                elif msg_type == "leave_group":
                    username = msg.get("username")
                    if username is None:
                        username = current_user
                    groupname = msg.get("groupname")
                    res = db.remove_group_member(groupname, username)

                    conn.sendall(encode_msg(res))

                # 13. 获取群成员
                elif msg_type == "get_group_members":
                    groupname = msg.get("groupname")
                    res = db.get_group_members(groupname)
                    res = self.normalize_friend_list(res)
                    conn.sendall(encode_msg({
                        "type": "group_members",
                        "gid": groupname ,
                        "members": res
                    }))

                # 14. 获取历史记录
                elif msg_type == "get_history":
                    target = msg.get("target") or msg.get("target_id") or msg.get("username")

                    messages = []
                    is_group = False

                    group_list = db.get_group_list(current_user)
                    for g in group_list:
                        if type(g) == dict and (str(g.get("gid")) == str(target) or str(g.get("name")) == str(target)):
                            is_group = True
                            target = g.get("name")
                            break

                    if is_group:
                        messages = db.get_group_history(target)
                    else:
                        messages = db.get_history(current_user, target)

                    conn.sendall(encode_msg({
                        "type": "history",
                        "target_id": target if target is not None else "",
                        "messages": messages
                    }))
                    
                #15. 获取群聊氛围
                elif msg_type == "get_group_atmosphere":
                    groupname = msg.get("groupname")
                    res = self.handle_group_atmosphere(groupname)
                    conn.sendall(encode_msg(res))
                #16. 私发文件
                elif msg_type == "file_message":
                    sender = msg.get("username")
                    target = msg.get("friendname") or msg.get("target")
                    filename = msg.get("filename") or msg.get("file_name") or ""
                    content = msg.get("content") or msg.get("file_content") or msg.get("text_content") or ""
                
                    file_obj = msg.get("file")
                    if isinstance(file_obj, dict):
                        if not filename:
                            filename = file_obj.get("filename") or file_obj.get("file_name") or ""
                        if not content:
                            content = file_obj.get("content") or file_obj.get("file_content") or ""
                
                    forward_msg = {
                        "type": "file_message",
                        "username": sender,
                        "friendname": target,
                        "filename": filename,
                        "content": content,
                        "time": msg.get("time")
                    }
                
                    self.send_private(target, forward_msg)
                #17. 群发文件
                elif msg_type == "group_file_message":
                    sender = msg.get("username")
                    groupname = msg.get("groupname") or msg.get("friendname")
                    filename = msg.get("filename") or msg.get("file_name") or ""
                    content = msg.get("content") or msg.get("file_content") or msg.get("text_content") or ""
                
                    file_obj = msg.get("file")
                    if isinstance(file_obj, dict):
                        if not filename:
                            filename = file_obj.get("filename") or file_obj.get("file_name") or ""
                        if not content:
                            content = file_obj.get("content") or file_obj.get("file_content") or ""
                
                    forward_msg = {
                        "type": "group_file_message",
                        "username": sender,
                        "groupname": groupname,
                        "filename": filename,
                        "content": content,
                        "time": msg.get("time")
                    }
                
                    self.broadcast(forward_msg)
        except ConnectionResetError:
            pass
        finally:
            if current_user:
                self.remove_client(current_user)

    #新增
    def is_ai_trigger(self, text: str) -> bool:
        if not text:
            return False
        return str(text).strip().startswith("@智能助手")

    def extract_file_info(self, msg: dict):
        filename = (
            msg.get("filename")
            or msg.get("file_name")
            or ""
        )
        content = (
            msg.get("content")
            or msg.get("file_content")
            or msg.get("text_content")
            or ""
        )

        file_obj = msg.get("file")
        if isinstance(file_obj, dict):
            if not filename:
                filename = file_obj.get("filename") or file_obj.get("file_name") or ""
            if not content:
                content = file_obj.get("content") or file_obj.get("file_content") or ""

        return str(filename).strip(), str(content).strip()

    def build_ai_private_msg(self, to_user: str, content: str):
        return {
            "type": "message",
            "username": self.ai_name,
            "friendname": to_user,
            "message": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def build_ai_group_msg(self, groupname: str, content: str):
        return {
            "type": "group_message",
            "username": self.ai_name,
            "groupname": groupname,
            "groupmessage": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def send_private_from_ai(self, to_user: str, content: str):
        msg = self.build_ai_private_msg(to_user, content)
        self.send_private(to_user, msg)

    def send_group_from_ai(self, groupname: str, content: str):
        msg = self.build_ai_group_msg(groupname, content)
        # 如果你们有“只给群成员广播”的函数，请替换这一句
        self.broadcast(msg)

    def handle_ai_private(self, username: str, friendname: str, message: str, raw_msg: dict):
        if not self.is_ai_trigger(message):
            return

        filename, file_content = self.extract_file_info(raw_msg)

        # 有文件：走总结
        if file_content:
            result = self.ai_client.summarize_private(
                username=username,
                friendname=friendname,
                message=message,
                filename=filename or "未知文件",
                content=file_content
            )
            reply_text = result.get("summary") if result.get("status") == 0 else f"总结失败：{result.get('error', '未知错误')}"
        else:
            recent_messages = db.get_recent_private_messages(username, friendname, limit=5)

            # 当前消息在 recent 里未出现时，补进去
            if not recent_messages or recent_messages[-1].get("message") != message:
                recent_messages.append({
                    "username": username,
                    "message": message
                })

            result = self.ai_client.reply_private(
                username=username,
                friendname=friendname,
                message=message,
                recent_messages=recent_messages
            )
            reply_text = result.get("reply") if result.get("status") == 0 else f"调用失败：{result.get('error', '未知错误')}"

        self.send_private_from_ai(username, reply_text or "我暂时无法回答。")

    def handle_ai_group(self, username: str, groupname: str, groupmessage: str, raw_msg: dict):
        if not self.is_ai_trigger(groupmessage):
            return

        filename, file_content = self.extract_file_info(raw_msg)

        # 有文件：走总结
        if file_content:
            result = self.ai_client.summarize_group(
                username=username,
                groupname=groupname,
                groupmessage=groupmessage,
                filename=filename or "未知文件",
                content=file_content
            )
            reply_text = result.get("summary") if result.get("status") == 0 else f"总结失败：{result.get('error', '未知错误')}"
        else:
            recent_messages = db.get_recent_group_messages(groupname, limit=5)

            if not recent_messages or recent_messages[-1].get("message") != groupmessage:
                recent_messages.append({
                    "username": username,
                    "message": groupmessage
                })

            result = self.ai_client.reply_group(
                username=username,
                groupname=groupname,
                groupmessage=groupmessage,
                recent_messages=recent_messages
            )
            reply_text = result.get("reply") if result.get("status") == 0 else f"调用失败：{result.get('error', '未知错误')}"

        self.send_group_from_ai(groupname, reply_text or "我暂时无法回答。")

    def handle_group_atmosphere(self, groupname: str):
        recent_messages = db.get_recent_group_messages(groupname, limit=5)
        result = self.ai_client.analyze_atmosphere(
            groupname=groupname,
            recent_messages=recent_messages
        )

        if result.get("status") == 0:
            return {
                "type": "group_atmosphere",
                "status": 0,
                "groupname": groupname,
                "emotion": result.get("emotion"),
                "label": result.get("label"),
                "color": result.get("color")
            }

        return {
            "type": "group_atmosphere",
            "status": 1,
            "groupname": groupname,
            "error": result.get("error", "群聊氛围分析失败")
        }

    def broadcast(self, msg_dict):
        """公共消息广播：发送给所有用户"""
        data = encode_msg(msg_dict)
        with self.lock:
            # 遍历每个用户并发送信息，sendall是python内置的循环发送函数
            for user, info in self.clients.items(): 
                try:
                    info["conn"].sendall(data)
                except Exception:
                    pass

    def send_private(self, target_user, msg_dict):
        """私发消息"""
        data = encode_msg(msg_dict)
        print("进入发送消息")
        # 获取互斥锁
        with self.lock:
            if target_user in self.clients:
                try:
                    print("开始发送")
                    # 只针对target客户
                    self.clients[target_user]["conn"].sendall(data)
                    # # 同时让发送者在本地也能看到自己发送的消息（也就是对发送者这个用户进行一次信息发送），由于这个逻辑在if中，保证了信息是在发送过去后才回显
                    # sender = msg_dict.get("sender")
                #     if sender != target_user and sender in self.clients:
                #         self.clients[sender]["conn"].sendall(data)
                except Exception as e:
                    logger.error(f"Private message failed: {e}")

    # def broadcast_user_list(self):
    #     """广播在线用户"""
    #     with self.lock:
    #         users = [{"username": k, "ip": v["ip"]} for k, v in self.clients.items()]
    #     self.broadcast({"type": "user_list", "users": users})

    def remove_client(self, username):
        """处理离线用户"""
        with self.lock:
            if username in self.clients:
                self.clients[username]["conn"].close()
                del self.clients[username]
        logger.info(f"User {username} disconnected.")
        # self.broadcast_user_list()
        # # 修改这里：将系统通知改为英文
        # self.broadcast({"type": "system", "content": f"User {username} left the chat."})
