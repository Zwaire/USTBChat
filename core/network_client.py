import socket
import threading
from core.protocol import encode_msg, decode_msg
from utils.logger import get_logger

logger = get_logger("Client")

class ChatClient:
    def __init__(self, callback, t):
        self.socket = None
        self.username = None
        self.callback = callback
        self.running = False
        self.t = t

    def connect(self, host, port):
        """只建立物理连接，不发送业务报文"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, int(port)))
            self.running = True
            threading.Thread(target= lambda t = self.t: self.receive_loop(t), daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            return False

    def receive_loop(self, targetFunction):
        while self.running:
            try:
                # msg = decode_msg(self.socket)
                # #print(f"Received message: {msg}")
                # if msg:
                #     try:
                #         self.callback(msg)
                #     except Exception:
                #         pass
                # else:
                #     break
                data = self.socket.recv(1024) # type: ignore
                if not data:
                    break
                else:
                    message = data.decode('utf-8')
                    targetFunction(message)
            except Exception:
                break
        self.disconnect()
        self.callback({"type": "system", "content": "unlink from server!!"})

    def send_data(self, msg_dict):
        """通用发送接口，支持传入符合通信接口规范的字典"""
        if not self.socket or not self.running:
            return False
        try:
            self.socket.sendall(encode_msg(msg_dict))
            return True
        except Exception as e:
            logger.error(f"发送失败: {e}")
            return False
        
    def disconnect(self):
        self.running = False
        if self.socket:
            self.socket.close()
            self.socket = None