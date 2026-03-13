from core import network_client
import time
if __name__ =="__main__":
    test=network_client.ChatClient(callback=lambda msg: print(f"收到消息: {msg}"))
    test.connect("127.0.0.1","8888")
    #测试注册
    data={"type":"register","username":"test_wzx","code":"123$567"}
    test.send_data(data)
    #测试登录
    data={"type":"login","username":"test_wzx","code":"567"}
    test.send_data(data)

    #测试找回密码
    data={"type":"request_pwd_find","username":"test_wzx","code":"qwe$rty"}
    test.send_data(data)

    #测试添加好友
    data={"type":"add_friend","username":"test_wzx","friendname":"test_xjz"}
    test.send_data(data)
    # 发送私聊信息
    data={"type":"message","username":"test_wzx","friendname":"test_xjz","message":"hello xjz!"}
    test.send_data(data)
    # 创建群聊
    # data={"type":"create_group","groupname":"test_group","username":"test_wzx"}
    # test.send_data(data)
    # 加入群聊
    data = {"type": "join_group", "groupname": "test_group", "username": "test_wzx"}
    test.send_data(data)
    #data={"type":"join_group","groupname":"test_group","username":"test_zgy"}
    #发送群聊信息
    data={"type":"group_message","username":"test_wzx","groupname":"test_group","message":"hello group!"}
    test.send_data(data)
    #获取好友列表
    data={"type":"get_friend_list","username":"test_wzx"}
    test.send_data(data)
    #获取群聊列表
    data={"type":"get_group_list","username":"test_wzx"}
    test.send_data(data)
    #获取联系人列表
    data={"type":"get_contact_list","username":"test_wzx"}
    test.send_data(data)
    # 退出群聊
    data={"type":"leave_group","groupname":"test_group","username":"test_wzx"}
    test.send_data(data)
    # 获取群成员
    data={"type":"get_group_members","groupname":"test_group"}
    test.send_data(data)
    #获取历史记录
    #data={"type":"get_history","username":"test_wzx","friendname":"test_xjz"}

    time.sleep(300)

    time.disconnect()