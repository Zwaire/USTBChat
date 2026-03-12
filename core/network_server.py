'''
负责处理用户的上线、下线，保存用户的用户名和 IP，并将消息广播或定向发送 。
'''
import socket
import threading
from core.protocol import encode_msg, decode_msg
from utils.logger import get_logger

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
                print(f"This is {msg_type} type message")
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

                    res = db.register(username, dk_hex, salt_hex)

                    print('===============',res.get("status"))
                    # status: 0为成功，1为已存在

                    # conn.sendall(encode_msg({
                    #     "type": "register",
                    #     "status": True if res.get("status") == 0 else False,
                    #     "warnings": "The user exists" if res.get("status") == 0 else ""
                    # }))
                    conn.sendall(encode_msg({
                        "type": "register",
                        "status": res.get("status"),
                        "warnings": "The user exists" if res.get("status") == 1 else ""
                    }))
                elif msg_type=="seed":
                    username=msg.get("username")
                    res=db.seed(username)
                    conn.sendall(encode_msg(res))
                elif msg_type=="request_pwd_find":
                    username=msg.get("username")
                    res=db.request_pwd_find(username)
                    conn.sendall(encode_msg)
                    if res.get("status")==0:
                        db.change_code(msg.get("code"),msg.get("seed"))
                        conn.sendall(encode_msg(res))
                    else:
                        conn.sendall(encode_msg(res))
                # 2. 登录请求
                elif msg_type == "login":
                    username = msg.get("username")
                    code = msg.get("code")
                    res = db.log_in(username, code, addr[0])
                    # status: 0为成功，2为密码错误等
                    if res.get("statuts") == 0:
                        current_user = username
                        with self.lock: 
                            self.clients[current_user] = {"conn": conn, "ip": addr[0]}
                        logger.info(f"User {current_user} ({addr[0]}) connected.")
                        # conn.sendall(encode_msg({"type": "login", "status": True}))
                        # 适配客户端 AppState
                        # 返回 uid, nickname, friends, groups。
                        # 注：目前 data.py 没有提供 get_friends 等接口，暂时传入空列表以保证客户端 AppState 能够正确完成初始化。未来数据库支持后在此替换即可。
                        conn.sendall(encode_msg({
                            "type": "login", 
                            "status": True,
                            "uid": current_user,
                            "nickname": current_user,
                            "friends": [], 
                            "groups": []
                        }))
                    else:
                        conn.sendall(encode_msg({"type": "login", "status": False, "warnings": "Password error or user not found"}))

                # 3. 添加好友
                elif msg_type == "add_friend":
                    res = db.add_friend(msg.get("username"), msg.get("friendname"))
                    conn.sendall(encode_msg({
                        "type": "add_friend",
                        "status": True if res.get("statuts") == 0 else False
                    }))

                # 4. 私聊消息
                elif msg_type == "message":
                    sender = msg.get("username")
                    target = msg.get("friendname")
                    content = msg.get("message")
                    # 保存到数据库
                    db.save_message(sender, target, content)
                    # 转发给目标用户
                    self.send_private(target, msg)

                # 5. 群聊消息
                elif msg_type == "group_message":
                    sender = msg.get("username")
                    groupname = msg.get("groupname")
                    content = msg.get("groupmessage")
                    # 保存到数据库
                    db.save_group_message(sender, groupname, content)
                    # 群聊广播逻辑 (遍历群成员发送)
                    self.broadcast(msg)
                    
        except ConnectionResetError:
            pass
        finally:
            if current_user:
                self.remove_client(current_user)

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
        # 获取互斥锁
        with self.lock:
            if target_user in self.clients:
                try:
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