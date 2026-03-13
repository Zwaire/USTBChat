from core.network_server import ChatServer
import os

if __name__ == '__main__':
    print("正在启动服务端...")
    host = os.environ.get("USTBCHAT_SERVER_HOST", "0.0.0.0")
    port = int(os.environ.get("USTBCHAT_SERVER_PORT", "8888"))
    server = ChatServer(host=host, port=port)
    server.start()
