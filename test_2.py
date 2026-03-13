from core import network_client
import time

if __name__ == "__main__":
    test = network_client.ChatClient(callback=lambda msg: print(f"收到消息: {msg}"))
    test.connect("127.0.0.1", "8888")

        #测试注册
    data={"type":"register","username":"test_xjz","code":"123$567"}
    test.send_data(data)
    
    data = {"type": "login", "username": "test_xjz", "code": "567"}
    test.send_data(data)

    data={"type":"create_group","groupname":"test_group","username":"test_xjz"}
    test.send_data(data)
    
    # data = {"type": "join_group", "groupname": "test_group", "username": "test_xjz"}
    # test.send_data(data)
    
    # 等待接收消息，30秒后自动退出
    time.sleep(300)
    
    # 断开连接
    test.disconnect()