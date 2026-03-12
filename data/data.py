import mysql.connector

def register(name,code,seed):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from users where name = %s"
    cursor.execute(sql,(name,))
    results=cursor.fetchall()
    if len(results)!=0:
        return {"type":"register","statuts":1}
    else :
        sql="insert into users (name,code,seed) values (%s,%s)"
        cursor.execute(sql,(name,code,seed))
        db.commit()
        return {"type":"register","statuts":0}
    
def seed(name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from users where name = %s"
    cursor.execute(sql,(name,))
    results=cursor.fetchall()
    if len(results)>0:
        seed=results[0][3]
        db.commit()
        return {"type":"seed","status":0,"seed":seed}
    else:
        db.commit()
        return {"type":"seed","status":9}
    
def request_pwd_find(name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from users where name=%s"
    cursor.execute(sql,(name,))
    results=cursor.fetchall()
    if results>0:
        return {"type":"request_pwd_find","status":0}
    else:
        return{"type":"request_pwd_find","status":8}
    
def change_code(name,code,seed):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="update users set code=%s ,seed=%s where name=%s "
    cursor.execute(sql,(code,seed,name))
    
def log_in(name,code,ip):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from users where name = %s"
    cursor.execute(sql,(name,))
    results=cursor.fetchone()
    if results[2]==code:
        sql="select * from user_sessions where user_id =%s"
        cursor.execute(sql,(results[0],))
        results_two=cursor.fetchall()
        if len(results_two)>0:
            sql="update user_sessions set ip=INET_ATON(%s), time=now()  where name=%s"
            cursor.execute(sql,(ip,name))
            db.commit()
            return {"type":"login","statuts":0}
        else:
            sql="insert into user_sessions (user_id,ip,login_time,status) values (%s,INET_ATON(%s),now(),%s)"
            cursor.execute(sql,(results[0],ip,1))
            db.commit()
            return {"type":"login","statuts":0}
    else:
        return {"type":"login","statuts":2}
    

def find_users(name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from users where name=%s"
    cursor.execute(sql,(name,))
    results=cursor.fetchall()
    db.commit()
    if len(results)>0:
        return True
    else :
        return False

def add_friend(user_name,friend_name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from users where name=%s"
    cursor.execute(sql,(user_name,))
    result_one=cursor.fetchone()
    user_id=result_one[0]

    cursor.execute(sql,(friend_name,))
    result_two=cursor.fetchone()
    if result_two:
        friend_id=result_two[0]
        sql="insert into friends (user_id,friend_id) values(%s,%s)"
        cursor.execute(sql,(user_id,friend_id))
        cursor.execute(sql,(friend_id,user_id))
        db.commit()
        return {"type":"add_friend","statuts":0}
    else :
        return {"type":"add_friend","statuts":3}
        
def create_group(group_name,owner_name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()

    sql="select * from groups_list where name=%s"
    cursor.execute(sql,(group_name,))
    results=cursor.fetchall()

    if len(results)==0:
        sql="insert into groups_list (name) values (%s)"
        cursor.execute(sql,(group_name,))

        sql="select * from users where name=%s"
        cursor.execute(sql,(owner_name,))
        results_user=cursor.fetchall()

        sql="select * from groups_list where name=%s"
        cursor.execute(sql,(group_name,))
        results_group=cursor.fetchall()

        if len(results_user)>0:
            owner_id=results_user[0][0]
            group_id=results_group[0][0]
            sql="insert into groups_member (group_id,user_id) values (%s,%s)"
            cursor.execute(sql,(owner_id,group_id))
            db.commit()
            return {"type":"create_group","statuts":0}
        else:
            db.commit()
            return {"type":"create_group","statuts":5}
    else:
        return {"type":"create_group","statuts":4}
    
def add_group_member(group_name,new_name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )

    cursor=db.cursor()
    sql="select * from groups_list where name=%s"
    cursor.execute(sql,(group_name,))
    results=cursor.fetchall()

    if len(results)>0:
        sql="select * from groups_list where name=%s"
        cursor.execute(sql,(group_name,))
        results_group=cursor.fetchall()
        group_id=results_group[0][0]

        sql="select * from users where name=%s"
        cursor.execute(sql,(new_name,))
        results_user=cursor.fetchall()
        user_id=results_user[0][0]

        sql="select * from groups_member where group_id=%s and user_id=%s "
        cursor.execute(sql,(group_id,user_id))
        results=cursor.fetchall()

        if len(results)>0:
            return {"type":"add_group","statuts":6}
        else:
            sql="insert into groups_member (group_id,user_id) values(%s,%s)"
            cursor.execute(sql,(group_id,user_id))
            db.commit()
            return  {"type":"add_group","status":0}
    else:
        return {"type":"add_group","statuts":7}

def find(name, table):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()
    sql = f"SELECT * FROM {table} WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()
    if len(results) > 0:
        return results[0][0]
    else:
        return -1   
def save_message(user_name,friend_name,message):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    user_id=find(user_name,"users")
    friend_id=find(friend_name,"users")
    sql="insert into messages (send_id,recive_id,message,time) values(%s,%s,%s,now())"
    cursor.execute(sql,(user_id,friend_id,message))
    db.commit()
    return True



def save_group_message(user_name,group_name,message):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    user_id=find(user_name,"users")
    group_id=find(group_name,"groups_list")
    sql="insert into group_messages (group_id,send_id,message,time) values(%s,%s,%s,now()) "
    cursor.execute(sql,(user_id,group_id,message))
    db.commit()
    return True

def find_ip(name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from user_sessions where name=%s"
    cursor.execute(sql,(name,))
    results=cursor.fetchall()
    if len(results)>0:
        return results[0][2]
    else:
        return None
    
def find_group_ip(name):
    db=mysql.connector.connect(
    host="localhost",
    user="root",
    password="1",
    database="chat"
    )
    cursor=db.cursor()
    sql="select * from groups_list where name=%s"
    cursor.execute(sql,(name,))
    results=cursor.fetchall()
    if len(results)>0:
        group_id=results[0][0]
        sql="select * from groups_member where group_id=%s"
        cursor.execute(sql,(group_id,))
        results=cursor.fetchall()
        ip=[]
        for result in results:
            user_id=result[2]
            sql="select * from user_sessions where user_id=%s"
            cursor.execute(sql,(user_id,))
            result=cursor.fetchone()
            ip.append(result[2])
            return ip
    else:
        return None
    


def get_friends(name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()

    sql = "select friend_id from friends where user_id=%s"
    user_id = find(name, "users")
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()

    friends = []
    for item in results:
        friend_id = item[0]
        sql = "select * from users where id=%s"
        cursor.execute(sql, (friend_id,))
        result_user = cursor.fetchone()
        if result_user:
            friends.append({
                "uid": result_user[1],
                "nickname": result_user[1]
            })

    db.commit()
    return friends


def get_group_list(name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()

    user_id = find(name, "users")
    sql = "select group_id from groups_member where user_id=%s"
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()

    groups = []
    for item in results:
        group_id = item[0]
        sql = "select * from groups_list where id=%s"
        cursor.execute(sql, (group_id,))
        result_group = cursor.fetchone()
        if result_group:
            groups.append({
                "gid": result_group[1],
                "name": result_group[1]
            })

    db.commit()
    return groups


def get_groups(name):
    return get_group_list(name)


def get_group_members(group_name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()

    sql = "select * from groups_list where name=%s"
    cursor.execute(sql, (group_name,))
    result_group = cursor.fetchone()

    members = []
    if result_group:
        group_id = result_group[0]
        sql = "select user_id from groups_member where group_id=%s"
        cursor.execute(sql, (group_id,))
        results = cursor.fetchall()

        for item in results:
            user_id = item[0]
            sql = "select * from users where id=%s"
            cursor.execute(sql, (user_id,))
            result_user = cursor.fetchone()
            if result_user:
                members.append({
                    "uid": result_user[1],
                    "nickname": result_user[1]
                })

    db.commit()
    return members


def get_history(user_name, friend_name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()

    user_id = find(user_name, "users")
    friend_id = find(friend_name, "users")

    sql = """
        select * from messages
        where (send_id=%s and recive_id=%s) or (send_id=%s and recive_id=%s)
        order by time asc
    """
    cursor.execute(sql, (user_id, friend_id, friend_id, user_id))
    results = cursor.fetchall()

    messages = []
    for item in results:
        send_id = item[1]
        content = item[3]
        msg_time = str(item[4])

        sql = "select * from users where id=%s"
        cursor.execute(sql, (send_id,))
        result_user = cursor.fetchone()

        if result_user:
            sender_name = result_user[1]
        else:
            sender_name = ""

        messages.append({
            "sender_uid": sender_name,
            "sender_nickname": sender_name,
            "content": content,
            "time": msg_time,
            "is_self": True if sender_name == user_name else False
        })

    db.commit()
    return messages


def get_group_history(group_name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()

    group_id = find(group_name, "groups_list")

    sql = """
        select * from group_messages
        where group_id=%s
        order by time asc
    """
    cursor.execute(sql, (group_id,))
    results = cursor.fetchall()

    messages = []
    for item in results:
        send_id = item[2]
        content = item[3]
        msg_time = str(item[4])

        sql = "select * from users where id=%s"
        cursor.execute(sql, (send_id,))
        result_user = cursor.fetchone()

        if result_user:
            sender_name = result_user[1]
        else:
            sender_name = ""

        messages.append({
            "sender_uid": sender_name,
            "sender_nickname": sender_name,
            "content": content,
            "time": msg_time,
            "is_self": False
        })

    db.commit()
    return messages


def remove_group_member(group_name, user_name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor()

    sql = "select * from groups_list where name=%s"
    cursor.execute(sql, (group_name,))
    result_group = cursor.fetchone()

    if result_group:
        group_id = result_group[0]
        user_id = find(user_name, "users")

        sql = "delete from groups_member where group_id=%s and user_id=%s"
        cursor.execute(sql, (group_id, user_id))
        db.commit()
        return {"type": "leave_group", "status": 0}
    else:
        db.commit()
        return {"type": "leave_group", "status": 7}


def leave_group(group_name, user_name):
    return remove_group_member(group_name, user_name)

# =====================【新增结束：联系人/群组/历史记录接口】=====================
