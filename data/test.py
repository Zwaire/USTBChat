from   data import *
import time



if __name__ == '__main__':
    # register("wzx","123")
    # register("xjz",234)
    # log_in("wzx","123","127.0.0.1")
    # log_in("xjz","234","127.0.0.1")
    # add_friend("wzx","xjz")
    # create_group("test","wzx")
    # add_group_member("test","xjz")
    # save_message("wzx","xjz","hello!")
    # save_group_message("wzx","test","hello groups friend")
    sender="wzx"
    # # reciver="xjz"
    for i in range(200,300):
        save_group_message(sender,"test",f"this is message {i}")
        time.sleep(0.01)
    messages=get_history_message_public("test")
    for row in messages:
        print(row.get("message"))
