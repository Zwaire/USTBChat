import mysql.connector


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )


def register(name, code, seed):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()
    if len(results) != 0:
        cursor.close()
        db.close()
        return {"type": "register", "status": 1}
    else:
        sql = "INSERT INTO users (name, code, seed) VALUES (%s, %s, %s)"
        cursor.execute(sql, (name, code, seed))
        db.commit()
        cursor.close()
        db.close()
        return {"type": "register", "status": 0}


def seed(name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()

    if len(results) > 0:
        user_seed = results[0][3] 
        cursor.close()
        db.close()
        return {"type": "seed", "status": 0, "seed": user_seed}
    else:
        cursor.close()
        db.close()
        return {"type": "seed", "status": 9}


def request_pwd_find(name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()

    cursor.close()
    db.close()

    if len(results) > 0:
        return {"type": "request_pwd_find", "status": 0}
    else:
        return {"type": "request_pwd_find", "status": 8}


def change_code(name, code, seed):
    db = get_db()
    cursor = db.cursor()

    sql = "UPDATE users SET code=%s, seed=%s WHERE name=%s"
    cursor.execute(sql, (code, seed, name))
    db.commit()

    cursor.close()
    db.close()

    return {"type": "change_code", "status": 0}


def log_in(name, code, ip):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (name,))
    user = cursor.fetchone()

    if user is None:
        cursor.close()
        db.close()
        return {"type": "login", "status": 8}

    if user[2] == code:
        user_id_6str = f"{user[0]:06d}"
        # print(user_id_6str)
        sql = "SELECT * FROM user_sessions WHERE user_id=%s"
        cursor.execute(sql, (user[0],))
        results_two = cursor.fetchall()

        if len(results_two) > 0:
            sql = "UPDATE user_sessions SET ip=INET_ATON(%s), login_time=NOW(),  status=%s WHERE user_id=%s"
            cursor.execute(sql, (ip, 1, user[0]))
            db.commit()
            cursor.close()
            db.close()
            return {"type": "login", "status": 0,"id":user_id_6str,"name":user[1]}
        else:
            sql = "INSERT INTO user_sessions (user_id,  ip, login_time,  status) VALUES (%s, INET_ATON(%s), NOW(), %s)"
            cursor.execute(sql, (user[0],  ip, 1))
            db.commit()
            cursor.close()
            db.close()
            return {"type": "login", "status": 0,"id":user_id_6str,"name":user[1]}
    else:
        cursor.close()
        db.close()
        return {"type": "login", "status": 2}


def find_users(name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()

    cursor.close()
    db.close()

    return len(results) > 0

def add_friend(user_name, friend_name):
    db = get_db()
    cursor = db.cursor()
    print('===============user_name为',user_name,'===================')
    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (user_name,))
    result_one = cursor.fetchone()
    if not result_one:
        cursor.close()
        db.close()
        return {"type": "add_friend", "status": 8}

    user_id = result_one[0]

    cursor.execute(sql, (friend_name,))
    print("friend_name:", friend_name)
    result_two = cursor.fetchone()
    print(result_two)
    if result_two:
        friend_id = result_two[0]
        sql = "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)"
        cursor.execute(sql, (user_id, friend_id))
        cursor.execute(sql, (friend_id, user_id))
        db.commit()
        cursor.close()
        db.close()
        return {"type": "add_friend", "status": 0}
    else:
        cursor.close()
        db.close()
        return {"type": "add_friend", "status": 3}


def create_group(group_name, owner_name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM groups_list WHERE name=%s"
    cursor.execute(sql, (group_name,))
    results = cursor.fetchall()

    if len(results) == 0:
        sql = "INSERT INTO groups_list (name) VALUES (%s)"
        cursor.execute(sql, (group_name,))

        sql = "SELECT * FROM users WHERE name=%s"
        cursor.execute(sql, (owner_name,))
        results_user = cursor.fetchall()

        sql = "SELECT * FROM groups_list WHERE name=%s"
        cursor.execute(sql, (group_name,))
        results_group = cursor.fetchall()

        if len(results_user) > 0:
            owner_id = results_user[0][0]
            group_id = results_group[0][0]
            sql = "INSERT INTO groups_member (group_id, user_id) VALUES (%s, %s)"
            cursor.execute(sql, (group_id, owner_id))
            db.commit()
            cursor.close()
            db.close()
            return {"type": "create_group", "status": 0}
        else:
            db.commit()
            cursor.close()
            db.close()
            return {"type": "create_group", "status": 5}
    else:
        cursor.close()
        db.close()
        return {"type": "create_group", "status": 4}


def add_group_member(group_name, new_name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM groups_list WHERE name=%s"
    cursor.execute(sql, (group_name,))
    results = cursor.fetchall()

    if len(results) > 0:
        group_id = results[0][0]

        sql = "SELECT * FROM users WHERE name=%s"
        cursor.execute(sql, (new_name,))
        results_user = cursor.fetchall()

        if len(results_user) == 0:
            cursor.close()
            db.close()
            return {"type": "add_group", "status": 8}

        user_id = results_user[0][0]

        sql = "SELECT * FROM groups_member WHERE group_id=%s AND user_id=%s"
        cursor.execute(sql, (group_id, user_id))
        results = cursor.fetchall()

        if len(results) > 0:
            cursor.close()
            db.close()
            return {"type": "add_group", "status": 6}
        else:
            sql = "INSERT INTO groups_member (group_id, user_id) VALUES (%s, %s)"
            cursor.execute(sql, (group_id, user_id))
            db.commit()
            cursor.close()
            db.close()
            return {"type": "add_group", "status": 0,"gid":group_id,"group_name":group_name}
    else:
        cursor.close()
        db.close()
        return {"type": "add_group", "status": 7}


def find(name, table):
    db = get_db()
    cursor = db.cursor()
    sql = f"SELECT * FROM {table} WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()

    cursor.close()
    db.close()

    if len(results) > 0:
        return results[0][0]
    else:
        return -1


def save_message(user_name, friend_name, message):
    db = get_db()
    cursor = db.cursor()

    user_id = find(user_name, "users")
    friend_id = find(friend_name, "users")

    if user_id == -1 or friend_id == -1:
        cursor.close()
        db.close()
        return False

    sql = "INSERT INTO messages (send_id, recive_id, message, time) VALUES (%s, %s, %s, NOW())"
    cursor.execute(sql, (user_id, friend_id, message))
    db.commit()

    cursor.close()
    db.close()
    return True


def save_group_message(user_name, group_name, message):
    db = get_db()
    cursor = db.cursor()

    user_id = find(user_name, "users")
    group_id = find(group_name, "groups_list")

    if user_id == -1 or group_id == -1:
        cursor.close()
        db.close()
        return False

    sql = "INSERT INTO group_messages (group_id, send_id, message, time) VALUES (%s, %s, %s, NOW())"
    cursor.execute(sql, (group_id, user_id, message))
    db.commit()

    cursor.close()
    db.close()
    return True


def find_ip(name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM user_sessions WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()

    cursor.close()
    db.close()

    if len(results) > 0:
        return results[0][3]
    else:
        return None


def find_group_ip(name):
    db = get_db()
    cursor = db.cursor()

    sql = "SELECT * FROM groups_list WHERE name=%s"
    cursor.execute(sql, (name,))
    results = cursor.fetchall()

    if len(results) > 0:
        group_id = results[0][0]
        sql = "SELECT * FROM groups_member WHERE group_id=%s"
        cursor.execute(sql, (group_id,))
        members = cursor.fetchall()

        ip_list = []
        for member in members:
            user_id = member[2]
            sql = "SELECT * FROM user_sessions WHERE user_id=%s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                ip_list.append(result[3])

        cursor.close()
        db.close()
        return ip_list
    else:
        cursor.close()
        db.close()
        return None
    
# [TODO] 下面的函数风格需要对应上，基本功能目前差不多
def get_friends(name):
    db = get_db()
    cursor = db.cursor()

    sql = "select friend_id from friends where user_id=%s"
    user_id = find(name, "users")
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()

    friends = []
    for item in results:
        friend_id = item[0]
        print(name,"friend_id:", friend_id)
        sql = "select * from users where user_id=%s"
        cursor.execute(sql, (friend_id,))
        result_user = cursor.fetchone()
        if result_user:
            friends.append({
                "uid": result_user[0],
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
    cursor = db.cursor(dictionary=True)

    # 先获取用户ID
    user_id = find(user_name, "users")
    friend_id = find(friend_name, "users")

    # 使用 JOIN 同时获取发送者和接收者信息
    sql = """
        SELECT 
            m.id,
            m.send_id,
            m.recive_id,
            m.content,
            m.time,
            s.username as sender_name,
            r.username as receiver_name
        FROM messages m
        LEFT JOIN users s ON m.send_id = s.id
        LEFT JOIN users r ON m.recive_id = r.id
        WHERE (m.send_id = %s AND m.recive_id = %s) 
           OR (m.send_id = %s AND m.recive_id = %s)
        ORDER BY m.time ASC
        LIMIT 30
    """
    cursor.execute(sql, (user_id, friend_id, friend_id, user_id))
    results = cursor.fetchall()

    messages = []
    for item in results:
        sender_name = item[5]
        reciver_name= item[6]
        content=item[3]
        time=item[4]
        messages.append({
            "sender_name": sender_name,
            "reciver_name": reciver_name,
            "content": content,
            "time": time,
        })

    cursor.close()
    db.close()
    return messages


def get_group_history(group_name):
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="1",
        database="chat"
    )
    cursor = db.cursor(dictionary=True)

    # 先获取群组ID
    group_id = find(group_name, "groups_list")
    
    if not group_id:
        cursor.close()
        db.close()
        return []

    # 使用 JOIN 获取群消息和发送者信息，限制最新30条
    sql = """
        SELECT 
            gm.group_id,
            gm.send_id,
            gm.content,
            gm.time,
            u.username as sender_name,
            u.id as sender_id
        FROM group_messages gm
        LEFT JOIN users u ON gm.send_id = u.id
        WHERE gm.group_id = %s
        ORDER BY gm.time DESC
        LIMIT 30
    """
    cursor.execute(sql, (group_id,))
    results = cursor.fetchall()
    
    # 由于是按时间倒序取的，需要再反转回正序
    results.reverse()

    messages = []
    for item in results:
        messages.append({
            "group_name": group_name,
            "sender_name": item[4],
            "content": item[2],
            "time": str(item[3]),
        })

    cursor.close()
    db.close()
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

# 新增
def get_recent_private_messages(username, friendname, limit=5):
    db = get_db()
    cursor = db.cursor()

    user_id = find(username, "users")
    friend_id = find(friendname, "users")

    if user_id == -1 or friend_id == -1:
        cursor.close()
        db.close()
        return []

    sql = """
        SELECT send_id, message
        FROM messages
        WHERE (send_id=%s AND recive_id=%s)
           OR (send_id=%s AND recive_id=%s)
        ORDER BY id DESC
        LIMIT %s
    """
    cursor.execute(sql, (user_id, friend_id, friend_id, user_id, limit))
    rows = cursor.fetchall()

    rows = list(rows)
    rows.reverse()

    result = []
    for send_id, message in rows:
        cursor.execute("SELECT name FROM users WHERE id=%s", (send_id,))
        user_row = cursor.fetchone()
        sender_name = user_row[0] if user_row else str(send_id)

        result.append({
            "username": sender_name,
            "message": message
        })

    cursor.close()
    db.close()
    return result


def get_recent_group_messages(groupname, limit=5):
    db = get_db()
    cursor = db.cursor()

    group_id = find(groupname, "groups_list")
    if group_id == -1:
        cursor.close()
        db.close()
        return []

    sql = """
        SELECT send_id, message
        FROM group_messages
        WHERE group_id=%s
        ORDER BY id DESC
        LIMIT %s
    """
    cursor.execute(sql, (group_id, limit))
    rows = cursor.fetchall()

    rows = list(rows)
    rows.reverse()

    result = []
    for send_id, message in rows:
        cursor.execute("SELECT name FROM users WHERE id=%s", (send_id,))
        user_row = cursor.fetchone()
        sender_name = user_row[0] if user_row else str(send_id)

        result.append({
            "username": sender_name,
            "message": message
        })

    cursor.close()
    db.close()
    return result


