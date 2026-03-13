import os
from typing import Optional

import mysql.connector
from mysql.connector.connection import MySQLConnection
from mysql.connector.cursor import MySQLCursor


DB_HOST = os.environ.get("USTBCHAT_DB_HOST", "localhost")
DB_PORT = int(os.environ.get("USTBCHAT_DB_PORT", "3306"))
DB_USER = os.environ.get("USTBCHAT_DB_USER", "root")
DB_PASSWORD = os.environ.get("USTBCHAT_DB_PASSWORD", "1")
DB_NAME = os.environ.get("USTBCHAT_DB_NAME", "chat")


def get_db() -> MySQLConnection:
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )


def _is_int_like(value) -> bool:
    if isinstance(value, int):
        return True
    if isinstance(value, str):
        return value.strip().isdigit()
    return False


def _resolve_user(cursor: MySQLCursor, identifier: Optional[str | int]):
    if identifier is None:
        return None

    if _is_int_like(identifier):
        cursor.execute("SELECT id, name, code, seed FROM users WHERE id=%s", (int(str(identifier).strip()),))
        row = cursor.fetchone()
        if row:
            return row

    cursor.execute("SELECT id, name, code, seed FROM users WHERE name=%s", (str(identifier).strip(),))
    return cursor.fetchone()


def _resolve_group(cursor: MySQLCursor, identifier: Optional[str | int]):
    if identifier is None:
        return None

    if _is_int_like(identifier):
        cursor.execute("SELECT id, name FROM groups_list WHERE id=%s", (int(str(identifier).strip()),))
        row = cursor.fetchone()
        if row:
            return row

    cursor.execute("SELECT id, name FROM groups_list WHERE name=%s", (str(identifier).strip(),))
    return cursor.fetchone()


def _ensure_ai_table(cursor: MySQLCursor):
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS group_ai_members (
            group_id INT PRIMARY KEY,
            ai_name VARCHAR(64) NOT NULL DEFAULT 'lulu'
        )
        """
    )


def register(name, code, seed):
    db = get_db()
    cursor = db.cursor()
    try:
        username = str(name).strip()
        cursor.execute("SELECT id FROM users WHERE name=%s", (username,))
        if cursor.fetchone():
            return {"type": "register", "status": 1}

        cursor.execute(
            "INSERT INTO users (name, code, seed) VALUES (%s, %s, %s)",
            (username, str(code), str(seed)),
        )
        db.commit()
        return {"type": "register", "status": 0}
    finally:
        cursor.close()
        db.close()


def seed(name):
    db = get_db()
    cursor = db.cursor()
    try:
        row = _resolve_user(cursor, name)
        if row:
            return {"type": "seed", "status": 0, "seed": row[3]}
        return {"type": "seed", "status": 9}
    finally:
        cursor.close()
        db.close()


def request_pwd_find(name):
    db = get_db()
    cursor = db.cursor()
    try:
        row = _resolve_user(cursor, name)
        if row:
            return {"type": "request_pwd_find", "status": 0}
        return {"type": "request_pwd_find", "status": 8}
    finally:
        cursor.close()
        db.close()


def change_code(name, code, seed):
    db = get_db()
    cursor = db.cursor()
    try:
        row = _resolve_user(cursor, name)
        if not row:
            return {"type": "change_code", "status": 8}

        cursor.execute(
            "UPDATE users SET code=%s, seed=%s WHERE id=%s",
            (str(code), str(seed), row[0]),
        )
        db.commit()
        return {"type": "change_code", "status": 0}
    finally:
        cursor.close()
        db.close()


def log_in(name, code, ip):
    db = get_db()
    cursor = db.cursor()
    try:
        row = _resolve_user(cursor, name)
        if not row:
            return {"type": "login", "status": 8}

        user_id, user_name, user_code = row[0], row[1], row[2]
        if str(user_code) != str(code):
            return {"type": "login", "status": 2}

        cursor.execute("SELECT id FROM user_sessions WHERE user_id=%s", (user_id,))
        session = cursor.fetchone()

        if session:
            cursor.execute(
                """
                UPDATE user_sessions
                SET name=%s, ip=INET_ATON(%s), login_time=NOW(), status=%s
                WHERE user_id=%s
                """,
                (user_name, str(ip), 1, user_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO user_sessions (user_id, name, ip, login_time, status)
                VALUES (%s, %s, INET_ATON(%s), NOW(), %s)
                """,
                (user_id, user_name, str(ip), 1),
            )

        db.commit()
        return {
            "type": "login",
            "status": 0,
            "id": f"{user_id:06d}",
            "name": user_name,
        }
    finally:
        cursor.close()
        db.close()


def find_users(name):
    db = get_db()
    cursor = db.cursor()
    try:
        return _resolve_user(cursor, name) is not None
    finally:
        cursor.close()
        db.close()


def add_friend(user_name, friend_name):
    db = get_db()
    cursor = db.cursor()
    try:
        me = _resolve_user(cursor, user_name)
        if not me:
            return {"type": "add_friend", "status": 8}

        friend = _resolve_user(cursor, friend_name)
        if not friend:
            return {"type": "add_friend", "status": 3}

        user_id = me[0]
        friend_id = friend[0]
        if user_id == friend_id:
            return {"type": "add_friend", "status": 3}

        cursor.execute(
            "SELECT id FROM friends WHERE user_id=%s AND friend_id=%s",
            (user_id, friend_id),
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)",
                (user_id, friend_id),
            )

        cursor.execute(
            "SELECT id FROM friends WHERE user_id=%s AND friend_id=%s",
            (friend_id, user_id),
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO friends (user_id, friend_id) VALUES (%s, %s)",
                (friend_id, user_id),
            )

        db.commit()
        return {"type": "add_friend", "status": 0}
    finally:
        cursor.close()
        db.close()


def create_group(group_name, owner_name):
    db = get_db()
    cursor = db.cursor()
    try:
        gname = str(group_name or "").strip()
        if not gname:
            return {"type": "create_group", "status": 4}

        cursor.execute("SELECT id FROM groups_list WHERE name=%s", (gname,))
        if cursor.fetchone():
            return {"type": "create_group", "status": 4}

        owner = _resolve_user(cursor, owner_name)
        if not owner:
            return {"type": "create_group", "status": 5}

        cursor.execute("INSERT INTO groups_list (name) VALUES (%s)", (gname,))
        group_id = cursor.lastrowid
        cursor.execute(
            "INSERT INTO groups_member (group_id, user_id) VALUES (%s, %s)",
            (group_id, owner[0]),
        )
        db.commit()

        return {
            "type": "create_group",
            "status": 0,
            "gid": str(group_id),
            "group_name": gname,
        }
    finally:
        cursor.close()
        db.close()


def add_group_member(group_name, new_name):
    db = get_db()
    cursor = db.cursor()
    try:
        group_row = _resolve_group(cursor, group_name)
        if not group_row:
            return {"type": "add_group", "status": 7}

        user_row = _resolve_user(cursor, new_name)
        if not user_row:
            return {"type": "add_group", "status": 8}

        group_id = group_row[0]
        user_id = user_row[0]

        cursor.execute(
            "SELECT id FROM groups_member WHERE group_id=%s AND user_id=%s",
            (group_id, user_id),
        )
        if cursor.fetchone():
            return {"type": "add_group", "status": 6}

        cursor.execute(
            "INSERT INTO groups_member (group_id, user_id) VALUES (%s, %s)",
            (group_id, user_id),
        )
        db.commit()

        return {
            "type": "add_group",
            "status": 0,
            "gid": str(group_id),
            "group_name": group_row[1],
        }
    finally:
        cursor.close()
        db.close()


def add_ai_to_group(group_name, ai_name="lulu"):
    db = get_db()
    cursor = db.cursor()
    try:
        group_row = _resolve_group(cursor, group_name)
        if not group_row:
            return {"type": "add_ai", "status": 7}

        ai_name = str(ai_name or "lulu")

        cursor.execute("SELECT id FROM users WHERE name=%s", (ai_name,))
        ai_user = cursor.fetchone()
        if ai_user:
            ai_user_id = ai_user[0]
        else:
            cursor.execute(
                "INSERT INTO users (name, code, seed) VALUES (%s, %s, %s)",
                (ai_name, "AI_BOT", "AI_BOT"),
            )
            ai_user_id = cursor.lastrowid

        cursor.execute(
            "SELECT id FROM groups_member WHERE group_id=%s AND user_id=%s",
            (group_row[0], ai_user_id),
        )
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO groups_member (group_id, user_id) VALUES (%s, %s)",
                (group_row[0], ai_user_id),
            )

        _ensure_ai_table(cursor)
        cursor.execute(
            """
            INSERT INTO group_ai_members (group_id, ai_name)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE ai_name=VALUES(ai_name)
            """,
            (group_row[0], ai_name),
        )
        db.commit()
        return {"type": "add_ai", "status": 0, "ai_name": ai_name}
    finally:
        cursor.close()
        db.close()


def remove_ai_from_group(group_name):
    db = get_db()
    cursor = db.cursor()
    try:
        group_row = _resolve_group(cursor, group_name)
        if not group_row:
            return {"type": "remove_ai", "status": 7}

        _ensure_ai_table(cursor)
        cursor.execute("SELECT ai_name FROM group_ai_members WHERE group_id=%s", (group_row[0],))
        ai_row = cursor.fetchone()
        if ai_row:
            ai_name = str(ai_row[0])
            cursor.execute("SELECT id FROM users WHERE name=%s", (ai_name,))
            ai_user = cursor.fetchone()
            if ai_user:
                cursor.execute(
                    "DELETE FROM groups_member WHERE group_id=%s AND user_id=%s",
                    (group_row[0], ai_user[0]),
                )

        cursor.execute("DELETE FROM group_ai_members WHERE group_id=%s", (group_row[0],))
        db.commit()
        return {"type": "remove_ai", "status": 0}
    finally:
        cursor.close()
        db.close()


def get_ai_name_for_group(group_name):
    db = get_db()
    cursor = db.cursor()
    try:
        group_row = _resolve_group(cursor, group_name)
        if not group_row:
            return None

        _ensure_ai_table(cursor)
        cursor.execute("SELECT ai_name FROM group_ai_members WHERE group_id=%s", (group_row[0],))
        row = cursor.fetchone()
        return str(row[0]) if row else None
    finally:
        cursor.close()
        db.close()


def is_ai_in_group(group_name):
    return get_ai_name_for_group(group_name) is not None


def find(name, table):
    db = get_db()
    cursor = db.cursor()
    try:
        if table == "users":
            row = _resolve_user(cursor, name)
            return row[0] if row else -1
        if table == "groups_list":
            row = _resolve_group(cursor, name)
            return row[0] if row else -1

        cursor.execute(f"SELECT id FROM {table} WHERE name=%s", (str(name),))
        row = cursor.fetchone()
        return row[0] if row else -1
    finally:
        cursor.close()
        db.close()


def save_message(user_name, friend_name, message):
    db = get_db()
    cursor = db.cursor()
    try:
        me = _resolve_user(cursor, user_name)
        peer = _resolve_user(cursor, friend_name)
        if not me or not peer:
            return False

        cursor.execute(
            "INSERT INTO messages (send_id, recive_id, message, time) VALUES (%s, %s, %s, NOW())",
            (me[0], peer[0], str(message)),
        )
        db.commit()
        return True
    finally:
        cursor.close()
        db.close()


def save_group_message(user_name, group_name, message):
    db = get_db()
    cursor = db.cursor()
    try:
        me = _resolve_user(cursor, user_name)
        group = _resolve_group(cursor, group_name)
        if not me or not group:
            return False

        cursor.execute(
            "INSERT INTO group_messages (group_id, send_id, message, time) VALUES (%s, %s, %s, NOW())",
            (group[0], me[0], str(message)),
        )
        db.commit()
        return True
    finally:
        cursor.close()
        db.close()


def find_ip(name):
    db = get_db()
    cursor = db.cursor()
    try:
        user = _resolve_user(cursor, name)
        if not user:
            return None

        cursor.execute(
            "SELECT INET_NTOA(ip) FROM user_sessions WHERE user_id=%s ORDER BY login_time DESC LIMIT 1",
            (user[0],),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        cursor.close()
        db.close()


def find_group_ip(name):
    db = get_db()
    cursor = db.cursor()
    try:
        group = _resolve_group(cursor, name)
        if not group:
            return None

        cursor.execute(
            """
            SELECT INET_NTOA(us.ip)
            FROM groups_member gm
            LEFT JOIN user_sessions us ON gm.user_id = us.user_id
            WHERE gm.group_id=%s
            """,
            (group[0],),
        )
        rows = cursor.fetchall()
        return [r[0] for r in rows if r and r[0]]
    finally:
        cursor.close()
        db.close()


def get_friends(name):
    db = get_db()
    cursor = db.cursor()
    try:
        user = _resolve_user(cursor, name)
        if not user:
            return []

        cursor.execute(
            """
            SELECT u.id, u.name
            FROM friends f
            JOIN users u ON f.friend_id = u.id
            WHERE f.user_id=%s
            ORDER BY u.name ASC
            """,
            (user[0],),
        )
        rows = cursor.fetchall()
        return [{"uid": str(uid), "nickname": uname} for uid, uname in rows]
    finally:
        cursor.close()
        db.close()


def get_group_list(name):
    db = get_db()
    cursor = db.cursor()
    try:
        user = _resolve_user(cursor, name)
        if not user:
            return []

        cursor.execute(
            """
            SELECT g.id, g.name
            FROM groups_member gm
            JOIN groups_list g ON gm.group_id = g.id
            WHERE gm.user_id=%s
            ORDER BY g.id ASC
            """,
            (user[0],),
        )
        rows = cursor.fetchall()
        return [{"gid": str(gid), "name": gname} for gid, gname in rows]
    finally:
        cursor.close()
        db.close()


def get_groups(name):
    return get_group_list(name)


def get_group_members(group_name):
    db = get_db()
    cursor = db.cursor()
    try:
        group = _resolve_group(cursor, group_name)
        if not group:
            return []

        cursor.execute(
            """
            SELECT u.id, u.name
            FROM groups_member gm
            JOIN users u ON gm.user_id = u.id
            WHERE gm.group_id=%s
            ORDER BY u.name ASC
            """,
            (group[0],),
        )
        rows = cursor.fetchall()
        members = [{"uid": str(uid), "nickname": uname} for uid, uname in rows]

        _ensure_ai_table(cursor)
        cursor.execute("SELECT ai_name FROM group_ai_members WHERE group_id=%s", (group[0],))
        ai_row = cursor.fetchone()
        if ai_row:
            ai_name = str(ai_row[0])
            exists = False
            for member in members:
                if member.get("nickname") == ai_name:
                    exists = True
                    break
            if not exists:
                members.append({"uid": f"ai_{ai_name}", "nickname": ai_name})

        return members
    finally:
        cursor.close()
        db.close()


def get_history(user_name, friend_name):
    db = get_db()
    cursor = db.cursor()
    try:
        me = _resolve_user(cursor, user_name)
        peer = _resolve_user(cursor, friend_name)
        if not me or not peer:
            return []

        cursor.execute(
            """
            SELECT t.send_id, t.recive_id, t.message, t.time, t.sender_name, t.receiver_name
            FROM (
                SELECT m.id, m.send_id, m.recive_id, m.message, m.time, s.name AS sender_name, r.name AS receiver_name
                FROM messages m
                JOIN users s ON m.send_id = s.id
                JOIN users r ON m.recive_id = r.id
                WHERE (m.send_id=%s AND m.recive_id=%s)
                   OR (m.send_id=%s AND m.recive_id=%s)
                ORDER BY m.id DESC
                LIMIT 200
            ) t
            ORDER BY t.id ASC
            """,
            (me[0], peer[0], peer[0], me[0]),
        )
        rows = cursor.fetchall()

        messages = []
        for send_id, _, content, send_time, sender_name, _ in rows:
            messages.append(
                {
                    "sender_uid": str(send_id),
                    "sender_nickname": sender_name,
                    "content": str(content or ""),
                    "time": str(send_time),
                    "is_self": str(send_id) == str(me[0]),
                }
            )
        return messages
    finally:
        cursor.close()
        db.close()


def get_group_history(group_name):
    db = get_db()
    cursor = db.cursor()
    try:
        group = _resolve_group(cursor, group_name)
        if not group:
            return []

        cursor.execute(
            """
            SELECT t.send_id, t.message, t.time, t.sender_name
            FROM (
                SELECT gm.id, gm.send_id, gm.message, gm.time, u.name AS sender_name
                FROM group_messages gm
                JOIN users u ON gm.send_id = u.id
                WHERE gm.group_id=%s
                ORDER BY gm.id DESC
                LIMIT 200
            ) t
            ORDER BY t.id ASC
            """,
            (group[0],),
        )
        rows = cursor.fetchall()
        messages = []
        for send_id, content, send_time, sender_name in rows:
            messages.append(
                {
                    "sender_uid": str(send_id),
                    "sender_nickname": sender_name,
                    "content": str(content or ""),
                    "time": str(send_time),
                }
            )
        return messages
    finally:
        cursor.close()
        db.close()


def remove_group_member(group_name, user_name):
    db = get_db()
    cursor = db.cursor()
    try:
        group = _resolve_group(cursor, group_name)
        if not group:
            return {"type": "leave_group", "status": 7}

        user = _resolve_user(cursor, user_name)
        if not user:
            return {"type": "leave_group", "status": 8}

        cursor.execute(
            "DELETE FROM groups_member WHERE group_id=%s AND user_id=%s",
            (group[0], user[0]),
        )
        db.commit()
        return {"type": "leave_group", "status": 0}
    finally:
        cursor.close()
        db.close()


def leave_group(group_name, user_name):
    return remove_group_member(group_name, user_name)


def get_recent_private_messages(username, friendname, limit=5):
    db = get_db()
    cursor = db.cursor()
    try:
        me = _resolve_user(cursor, username)
        peer = _resolve_user(cursor, friendname)
        if not me or not peer:
            return []

        cursor.execute(
            """
            SELECT m.send_id, m.message, u.name
            FROM messages m
            JOIN users u ON m.send_id = u.id
            WHERE (m.send_id=%s AND m.recive_id=%s)
               OR (m.send_id=%s AND m.recive_id=%s)
            ORDER BY m.id DESC
            LIMIT %s
            """,
            (me[0], peer[0], peer[0], me[0], int(limit)),
        )
        rows = list(cursor.fetchall())
        rows.reverse()
        return [{"username": name, "message": str(msg or "")} for _, msg, name in rows]
    finally:
        cursor.close()
        db.close()


def get_recent_group_messages(groupname, limit=5):
    db = get_db()
    cursor = db.cursor()
    try:
        group = _resolve_group(cursor, groupname)
        if not group:
            return []

        cursor.execute(
            """
            SELECT gm.send_id, gm.message, u.name
            FROM group_messages gm
            JOIN users u ON gm.send_id = u.id
            WHERE gm.group_id=%s
            ORDER BY gm.id DESC
            LIMIT %s
            """,
            (group[0], int(limit)),
        )
        rows = list(cursor.fetchall())
        rows.reverse()
        return [{"username": name, "message": str(msg or "")} for _, msg, name in rows]
    finally:
        cursor.close()
        db.close()
