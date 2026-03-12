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
    print('=========',len(results))
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
        sql = "SELECT * FROM user_sessions WHERE user_id=%s"
        cursor.execute(sql, (user[0],))
        results_two = cursor.fetchall()

        if len(results_two) > 0:
            sql = "UPDATE user_sessions SET ip=INET_ATON(%s), time=NOW(), name=%s, status=%s WHERE user_id=%s"
            cursor.execute(sql, (ip, name, 1, user[0]))
            db.commit()
            cursor.close()
            db.close()
            return {"type": "login", "status": 0}
        else:
            sql = "INSERT INTO user_sessions (user_id, name, ip, login_time, time, status) VALUES (%s, %s, INET_ATON(%s), NOW(), NOW(), %s)"
            cursor.execute(sql, (user[0], name, ip, 1))
            db.commit()
            cursor.close()
            db.close()
            return {"type": "login", "status": 0}
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

    sql = "SELECT * FROM users WHERE name=%s"
    cursor.execute(sql, (user_name,))
    result_one = cursor.fetchone()
    if not result_one:
        cursor.close()
        db.close()
        return {"type": "add_friend", "status": 8}

    user_id = result_one[0]

    cursor.execute(sql, (friend_name,))
    result_two = cursor.fetchone()
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
            return {"type": "add_group", "status": 0}
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
