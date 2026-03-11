import mysql.connector

def register(name,code):
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
        return {"type":"register","statuts":0}
    else :
        sql="insert into users (name,code) values (%s,%s)"
        cursor.execute(sql,(name,code))
        db.commit()
        return {"type":"register","statuts":1}
    
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
            sql="update user_sessions set ip=INET_ATON(%s) time=now()  where name=%s"
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
    
def get_history_message_private(user_name, friend_name):

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
    SELECT m.message, m.time, u.name
    FROM messages m
    JOIN users u ON m.send_id = u.user_id
    WHERE (m.send_id=%s AND m.recive_id=%s)
       OR (m.send_id=%s AND m.recive_id=%s)
    ORDER BY m.time DESC, m.id DESC
    LIMIT 50
    """

    cursor.execute(sql, (user_id, friend_id, friend_id, user_id))

    results = cursor.fetchall()

    messages = []

    for row in results:
        messages.append({
            "send_name": row[2],
            "message": row[0],
            "time": row[1]
        })

    return messages

def get_history_message_public(group_name):

    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )

    cursor = db.cursor()

    group_id = find(group_name,"groups_list")

    sql = """
    SELECT u.name, gm.message, gm.time
    FROM group_messages gm
    JOIN users u ON gm.send_id = u.user_id
    WHERE gm.group_id = %s
    ORDER BY gm.time DESC, gm.id DESC
    LIMIT 50
    """

    cursor.execute(sql, (group_id,))

    results = cursor.fetchall()

    messages = []

    for row in results:
        messages.append({
            "send_name": row[0],
            "message": row[1],
            "time": row[2]
        })

    cursor.close()
    db.close()

    return messages