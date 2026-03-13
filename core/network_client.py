import socket
import threading
from core.protocol import encode_msg, decode_msg
from utils.logger import get_logger

logger = get_logger("Client")

class ChatClient:
    def __init__(self, callback):
        self.socket = None
        self.username = None
        self.callback = callback
        self.running = False
        self.host = None
        self.port = None

    def connect(self, host, port):
        """建立物理连接；若已连接到其他地址会先重连。"""
        host = str(host).strip()
        port = int(port)

        if self.running and self.socket:
            if self.host == host and self.port == port:
                return True
            self.disconnect()

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((host, port))
            self.running = True
            self.host = host
            self.port = port
            threading.Thread(target=self.receive_loop, daemon=True).start()
            return True
        except Exception as e:
            logger.error(f"连接失败: {e}")
            self.host = None
            self.port = None
            return False

    def receive_loop(self):
        while self.running:
            try:
                msg = decode_msg(self.socket)
                #print(f"Received message: {msg}")
                if msg:
                    try:
                        self.callback(msg)
                    except Exception:
                        pass
                else:
                    break
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
        self.host = None
        self.port = None
