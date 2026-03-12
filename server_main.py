from core.network_server import ChatServer

if __name__ == '__main__':
    print("正在启动服务端...")
    # 默认绑定 0.0.0.0，允许局域网内所有设备访问
    server = ChatServer(host='0.0.0.0', port=8888)
    server.start()