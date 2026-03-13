"""
服务端消息分发与业务处理。
支持：登录注册、加好友、私聊、建群、入群、群聊、历史记录、群聊AI回复。
"""

import os
import socket
import threading
from datetime import datetime

from core.protocol import decode_msg, encode_msg
from data import data as db
from utils.logger import get_logger

try:
    from core.ai_client import AIServiceClient
except Exception:
    AIServiceClient = None


logger = get_logger("Server")


class ChatServer:
    def __init__(self, host="0.0.0.0", port=8888):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(20)

        # 在线用户：key = username(name)，value = {"conn": socket, "ip": ip}
        self.clients = {}
        self.lock = threading.Lock()

        self.ai_name = os.environ.get("USTBCHAT_AI_NAME", "lulu")
        ai_url = os.environ.get("USTBCHAT_AI_URL", "http://127.0.0.1:5001")
        self.ai_client = AIServiceClient(ai_url, timeout=90) if AIServiceClient else None
        if self.ai_client:
            health = self.ai_client.health()
            if health.get("status") != 0:
                logger.warning(f"AI service unavailable on startup: {health.get('error')}")

    def start(self):
        logger.info(f"Server started on {self.host}:{self.port}")
        try:
            while True:
                conn, addr = self.server_socket.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            logger.info("Server shut down.")
        finally:
            self.server_socket.close()

    def handle_client(self, conn, addr):
        current_user = None
        try:
            while True:
                msg = decode_msg(conn)
                if not msg:
                    break

                msg_type = msg.get("type")
                if not msg_type:
                    continue

                if msg_type == "register":
                    username = msg.get("username")
                    code = str(msg.get("code") or "")
                    parts = code.split("$", 1)
                    salt_hex = parts[0] if len(parts) == 2 else ""
                    dk_hex = parts[1] if len(parts) == 2 else ""
                    res = db.register(username, dk_hex, salt_hex)
                    conn.sendall(encode_msg(res))

                elif msg_type == "seed":
                    username = msg.get("username")
                    res = db.seed(username)
                    conn.sendall(encode_msg(res))

                elif msg_type == "request_pwd_find":
                    username = msg.get("username")
                    res = db.request_pwd_find(username)
                    if res.get("status") == 0:
                        code = str(msg.get("code") or "")
                        parts = code.split("$", 1)
                        salt_hex = parts[0] if len(parts) == 2 else ""
                        dk_hex = parts[1] if len(parts) == 2 else ""
                        db.change_code(username, dk_hex, salt_hex)
                    conn.sendall(encode_msg(res))

                elif msg_type == "login":
                    username = msg.get("username")
                    code = msg.get("code")
                    res = db.log_in(username, code, addr[0])
                    if res.get("status") == 0:
                        current_user = res.get("name")
                        with self.lock:
                            self.clients[current_user] = {"conn": conn, "ip": addr[0]}
                        logger.info(f"User {current_user} ({addr[0]}) connected")
                    conn.sendall(encode_msg(res))

                elif msg_type == "add_friend":
                    username = msg.get("username") or current_user
                    friend = msg.get("friendname") or msg.get("target")
                    res = db.add_friend(username, friend)
                    conn.sendall(encode_msg(res))

                elif msg_type == "message":
                    self._handle_private_message(msg, current_user)

                elif msg_type == "group_message":
                    self._handle_group_message(msg, current_user)

                elif msg_type == "get_friend_list":
                    username = msg.get("username") or current_user
                    friends = db.get_friends(username)
                    conn.sendall(encode_msg({"type": "friend_list", "friends": friends}))

                elif msg_type == "get_group_list":
                    username = msg.get("username") or current_user
                    groups = db.get_group_list(username)
                    conn.sendall(encode_msg({"type": "group_list", "groups": groups}))

                elif msg_type == "get_contacts_list":
                    username = msg.get("username") or current_user
                    contacts = self._build_contacts(username)
                    conn.sendall(encode_msg({"type": "contacts_list", "contacts": contacts}))

                elif msg_type == "create_group":
                    username = msg.get("username") or current_user
                    groupname = msg.get("groupname") or msg.get("group_name")
                    with_ai = bool(msg.get("with_ai"))
                    res = db.create_group(groupname, username)

                    # 可选：建群后批量加人（接收uid或name）
                    if res.get("status") == 0:
                        for member in msg.get("uids", []):
                            db.add_group_member(res.get("gid"), member)
                        if with_ai:
                            db.add_ai_to_group(res.get("gid"), self.ai_name)
                    res["with_ai"] = with_ai

                    conn.sendall(encode_msg(res))

                elif msg_type == "join_group":
                    username = msg.get("username") or current_user
                    group = msg.get("groupname") or msg.get("gid")
                    res = db.add_group_member(group, username)
                    conn.sendall(
                        encode_msg(
                            {
                                "type": "join_group",
                                "status": res.get("status", 1),
                                "gid": res.get("gid", str(group or "")),
                                "group_name": res.get("group_name", str(group or "")),
                            }
                        )
                    )

                elif msg_type == "leave_group":
                    username = msg.get("username") or current_user
                    group = msg.get("groupname") or msg.get("gid")
                    res = db.remove_group_member(group, username)
                    conn.sendall(encode_msg(res))

                elif msg_type == "get_group_members":
                    group = msg.get("groupname") or msg.get("gid")
                    members = db.get_group_members(group)
                    group_ai_name = db.get_ai_name_for_group(group)
                    ai_online = False
                    if group_ai_name and self.ai_client:
                        health = self.ai_client.health()
                        ai_online = health.get("status") == 0

                    with self.lock:
                        online_usernames = set(self.clients.keys())

                    decorated_members = []
                    for member in members:
                        nickname = str(member.get("nickname", ""))
                        uid = str(member.get("uid", ""))
                        is_ai = uid.startswith("ai_") or (group_ai_name is not None and nickname == str(group_ai_name))
                        online = ai_online if is_ai else nickname in online_usernames
                        decorated_members.append(
                            {
                                "uid": uid,
                                "nickname": nickname,
                                "online": bool(online),
                                "is_ai": bool(is_ai),
                            }
                        )

                    gid = str(db.find(group, "groups_list") if group is not None else "")
                    conn.sendall(
                        encode_msg(
                            {
                                "type": "group_members",
                                "gid": gid,
                                "members": decorated_members,
                                "online_count": sum(1 for x in decorated_members if x.get("online")),
                                "total_count": len(decorated_members),
                            }
                        )
                    )

                elif msg_type == "get_history":
                    username = msg.get("username") or current_user
                    target = (
                        msg.get("target")
                        or msg.get("target_id")
                        or msg.get("friendname")
                        or msg.get("groupname")
                        or msg.get("gid")
                    )
                    messages = self._get_history(username, target, msg.get("is_group"))
                    conn.sendall(
                        encode_msg(
                            {
                                "type": "history",
                                "target_id": str(target or ""),
                                "messages": messages,
                            }
                        )
                    )

                elif msg_type == "get_group_atmosphere":
                    group = msg.get("groupname") or msg.get("gid")
                    conn.sendall(encode_msg(self.handle_group_atmosphere(group)))

                elif msg_type == "file_message":
                    self.handle_private_file_message(msg, current_user)

                elif msg_type == "group_file_message":
                    self.handle_group_file_message(msg, current_user)

        except ConnectionResetError:
            pass
        except Exception as e:
            logger.error(f"handle_client error: {e}")
        finally:
            if current_user:
                self.remove_client(current_user)
            else:
                try:
                    conn.close()
                except Exception:
                    pass

    def _build_contacts(self, username):
        friends = db.get_friends(username)
        groups = db.get_group_list(username)
        contacts = []

        for item in friends:
            contacts.append(
                {
                    "id": str(item.get("uid")),
                    "name": str(item.get("nickname")),
                    "is_group": False,
                    "last_message": "",
                    "last_time": "",
                    "unread": 0,
                }
            )

        for item in groups:
            contacts.append(
                {
                    "id": str(item.get("gid")),
                    "name": str(item.get("name")),
                    "is_group": True,
                    "last_message": "",
                    "last_time": "",
                    "unread": 0,
                }
            )

        return contacts

    def _get_history(self, username, target, is_group_hint=None):
        if not username or not target:
            return []

        is_group = None
        if isinstance(is_group_hint, bool):
            is_group = is_group_hint
        elif isinstance(is_group_hint, str):
            normalized = is_group_hint.strip().lower()
            if normalized in {"1", "true", "yes", "y"}:
                is_group = True
            elif normalized in {"0", "false", "no", "n"}:
                is_group = False

        if is_group is None:
            is_group = False
            for g in db.get_group_list(username):
                gid = str(g.get("gid"))
                gname = str(g.get("name"))
                if str(target) in (gid, gname):
                    is_group = True
                    break

        if is_group:
            current_uid = str(db.find(username, "users"))
            result = []
            for item in db.get_group_history(target):
                sender_uid = str(item.get("sender_uid", ""))
                result.append(
                    {
                        "sender_uid": sender_uid,
                        "sender_nickname": str(item.get("sender_nickname", sender_uid)),
                        "content": str(item.get("content", "")),
                        "time": str(item.get("time", "")),
                        "is_self": sender_uid == current_uid,
                    }
                )
            return result

        return db.get_history(username, target)

    def _handle_private_message(self, msg, current_user):
        sender = msg.get("username") or current_user
        target = msg.get("friendname") or msg.get("target") or msg.get("friendid")
        content = msg.get("message")
        if not sender or not target or content is None:
            return

        timestamp = msg.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.save_message(sender, target, content)

        sender_uid = db.find(sender, "users")
        sender_uid_str = str(sender_uid if sender_uid != -1 else sender)

        forward_msg = {
            "type": "message",
            "username": str(sender),
            "friendname": str(sender),
            "friendid": sender_uid_str,
            "message": str(content),
            "time": str(timestamp),
        }
        self.send_private(target, forward_msg)

        threading.Thread(
            target=self.handle_ai_private,
            args=(sender, target, str(content), msg),
            daemon=True,
        ).start()

    def _handle_group_message(self, msg, current_user):
        sender = msg.get("username") or current_user
        group = msg.get("groupname") or msg.get("groupid") or msg.get("friendname") or msg.get("gid")
        content = msg.get("groupmessage")
        if content is None:
            content = msg.get("message")

        if not sender or not group or content is None:
            return

        timestamp = msg.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.save_group_message(sender, group, content)

        group_id = db.find(group, "groups_list")
        group_id_str = str(group_id if group_id != -1 else group)

        forward_msg = {
            "type": "group_message",
            "username": str(sender),
            "groupname": str(group),
            "groupid": group_id_str,
            "groupmessage": str(content),
            "time": str(timestamp),
        }
        self.send_group(group, forward_msg, exclude_user=str(sender))

        if db.is_ai_in_group(group):
            threading.Thread(
                target=self.handle_ai_group,
                args=(sender, group, str(content), msg),
                daemon=True,
            ).start()

    def _find_online_user_key(self, user_identifier):
        if user_identifier is None:
            return None

        identifier = str(user_identifier)
        with self.lock:
            if identifier in self.clients:
                return identifier

            for username in self.clients.keys():
                uid = db.find(username, "users")
                if uid != -1 and str(uid) == identifier:
                    return username

        return None

    def send_private(self, target_user, msg_dict):
        data = encode_msg(msg_dict)
        key = self._find_online_user_key(target_user)
        if not key:
            return

        with self.lock:
            client = self.clients.get(key)
            if not client:
                return
            try:
                client["conn"].sendall(data)
            except Exception as e:
                logger.error(f"Private message failed: {e}")

    def send_group(self, group_identifier, msg_dict, exclude_user=None):
        members = db.get_group_members(group_identifier)
        if not members:
            return

        data = encode_msg(msg_dict)
        with self.lock:
            for member in members:
                username = str(member.get("nickname", ""))
                if exclude_user is not None and username == str(exclude_user):
                    continue
                info = self.clients.get(username)
                if not info:
                    continue
                try:
                    info["conn"].sendall(data)
                except Exception:
                    pass

    def broadcast(self, msg_dict):
        data = encode_msg(msg_dict)
        with self.lock:
            for info in self.clients.values():
                try:
                    info["conn"].sendall(data)
                except Exception:
                    pass

    def remove_client(self, username):
        with self.lock:
            info = self.clients.pop(username, None)
        if info:
            try:
                info["conn"].close()
            except Exception:
                pass
        logger.info(f"User {username} disconnected")

    def is_ai_trigger(self, text: str) -> bool:
        if not text:
            return False
        raw = str(text).strip()
        return raw.startswith("@智能助手") or raw.startswith(f"@{self.ai_name}")

    def format_ai_error(self, err_text: str) -> str:
        raw = str(err_text or "")
        if "Connection refused" in raw or "Failed to establish a new connection" in raw:
            return "lulu当前离线：AI服务未启动或地址配置错误，请先启动assistant_service.py。"
        if "Max retries exceeded" in raw:
            return "lulu当前不可达：请检查AI服务地址与端口。"
        return f"lulu调用失败：{raw}"

    def extract_file_info(self, msg: dict):
        filename = msg.get("filename") or msg.get("file_name") or ""
        content = msg.get("content") or msg.get("file_content") or msg.get("text_content") or ""

        file_obj = msg.get("file")
        if isinstance(file_obj, dict):
            if not filename:
                filename = file_obj.get("filename") or file_obj.get("file_name") or ""
            if not content:
                content = file_obj.get("content") or file_obj.get("file_content") or ""

        return str(filename).strip(), str(content).strip()

    def handle_private_file_message(self, msg: dict, current_user):
        sender = msg.get("username") or current_user
        target = msg.get("friendname") or msg.get("target") or msg.get("friendid")
        if not sender or not target:
            return

        filename, content = self.extract_file_info(msg)
        forward_msg = {
            "type": "file_message",
            "username": str(sender),
            "friendname": str(sender),
            "friendid": str(db.find(sender, "users")),
            "filename": filename,
            "content": content,
            "time": msg.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.send_private(target, forward_msg)

        if self.is_ai_trigger(str(msg.get("message") or "")):
            threading.Thread(
                target=self.handle_ai_private,
                args=(sender, target, str(msg.get("message") or ""), msg),
                daemon=True,
            ).start()

    def handle_group_file_message(self, msg: dict, current_user):
        sender = msg.get("username") or current_user
        group = msg.get("groupname") or msg.get("groupid") or msg.get("friendname") or msg.get("gid")
        if not sender or not group:
            return

        filename, content = self.extract_file_info(msg)
        forward_msg = {
            "type": "group_file_message",
            "username": str(sender),
            "groupname": str(group),
            "groupid": str(db.find(group, "groups_list")),
            "filename": filename,
            "content": content,
            "time": msg.get("time") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.send_group(group, forward_msg, exclude_user=str(sender))

        if db.is_ai_in_group(group) and self.is_ai_trigger(str(msg.get("groupmessage") or msg.get("message") or "")):
            threading.Thread(
                target=self.handle_ai_group,
                args=(sender, group, str(msg.get("groupmessage") or msg.get("message") or ""), msg),
                daemon=True,
            ).start()

    def build_ai_private_msg(self, chat_target: str, content: str):
        target_uid = db.find(chat_target, "users")
        target_uid = str(target_uid if target_uid != -1 else chat_target)
        return {
            "type": "message",
            "username": self.ai_name,
            "friendname": str(chat_target),
            "friendid": target_uid,
            "message": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def build_ai_group_msg(self, groupname: str, content: str):
        gid = db.find(groupname, "groups_list")
        gid = str(gid if gid != -1 else groupname)
        return {
            "type": "group_message",
            "username": self.ai_name,
            "groupname": str(groupname),
            "groupid": gid,
            "groupmessage": content,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def send_private_from_ai(self, to_user: str, chat_target: str, content: str):
        self.send_private(to_user, self.build_ai_private_msg(chat_target, content))

    def send_group_from_ai(self, groupname: str, content: str):
        db.save_group_message(self.ai_name, groupname, content)
        self.send_group(groupname, self.build_ai_group_msg(groupname, content))

    def handle_ai_private(self, username: str, friendname: str, message: str, raw_msg: dict):
        if not self.ai_client or not self.is_ai_trigger(message):
            return

        filename, file_content = self.extract_file_info(raw_msg)
        if file_content:
            result = self.ai_client.summarize_private(
                username=username,
                friendname=friendname,
                message=message,
                filename=filename or "未知文件",
                content=file_content,
            )
            reply_text = result.get("summary") if result.get("status") == 0 else self.format_ai_error(result.get("error", "未知错误"))
        else:
            recent_messages = db.get_recent_private_messages(username, friendname, limit=5)
            if not recent_messages or recent_messages[-1].get("message") != message:
                recent_messages.append({"username": username, "message": message})

            result = self.ai_client.reply_private(
                username=username,
                friendname=friendname,
                message=message,
                recent_messages=recent_messages,
            )
            reply_text = result.get("reply") if result.get("status") == 0 else self.format_ai_error(result.get("error", "未知错误"))

        self.send_private_from_ai(username, friendname, reply_text or "我暂时无法回答。")

    def handle_ai_group(self, username: str, groupname: str, groupmessage: str, raw_msg: dict):
        if not self.ai_client or not db.is_ai_in_group(groupname) or not self.is_ai_trigger(groupmessage):
            return

        filename, file_content = self.extract_file_info(raw_msg)
        if file_content:
            result = self.ai_client.summarize_group(
                username=username,
                groupname=groupname,
                groupmessage=groupmessage,
                filename=filename or "未知文件",
                content=file_content,
            )
            reply_text = result.get("summary") if result.get("status") == 0 else self.format_ai_error(result.get("error", "未知错误"))
        else:
            recent_messages = db.get_recent_group_messages(groupname, limit=5)
            if not recent_messages or recent_messages[-1].get("message") != groupmessage:
                recent_messages.append({"username": username, "message": groupmessage})

            result = self.ai_client.reply_group(
                username=username,
                groupname=groupname,
                groupmessage=groupmessage,
                recent_messages=recent_messages,
            )
            reply_text = result.get("reply") if result.get("status") == 0 else self.format_ai_error(result.get("error", "未知错误"))

        self.send_group_from_ai(groupname, reply_text or "我暂时无法回答。")

    def handle_group_atmosphere(self, groupname: str):
        if not self.ai_client:
            return {
                "type": "group_atmosphere",
                "status": 1,
                "groupname": str(groupname or ""),
                "error": "AI服务不可用",
            }

        recent_messages = db.get_recent_group_messages(groupname, limit=5)
        result = self.ai_client.analyze_atmosphere(groupname=groupname, recent_messages=recent_messages)

        if result.get("status") == 0:
            return {
                "type": "group_atmosphere",
                "status": 0,
                "groupname": str(groupname),
                "emotion": result.get("emotion"),
                "label": result.get("label"),
                "color": result.get("color"),
            }

        return {
            "type": "group_atmosphere",
            "status": 1,
            "groupname": str(groupname),
            "error": result.get("error", "群聊氛围分析失败"),
        }
