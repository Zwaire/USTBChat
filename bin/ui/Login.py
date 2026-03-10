# -*- coding: utf-8 -*-

import re
import json
import socket
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QLabel, QPushButton,
                               QVBoxLayout, QHBoxLayout, QSizePolicy, QLineEdit,
                               QStackedLayout, QDialog, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal

from CommonCouple import TextInput, Button, ClassicLayout, Fonts

# ── 输入验证规则 ────────────────────────────────────────────────s
MAX_LEN = 20

_RE_UID      = re.compile(r'^\d+$')
_RE_NICKNAME = re.compile(r'^[\u4e00-\u9fa5A-Za-z0-9_]+$')
_RE_PASSWORD = re.compile(r'^[A-Za-z0-9_/\.]+$')

def _validate_id(text: str) -> str | None:
    """返回 None 表示合法，否则返回错误信息"""
    if not text:
        return "账户不能为空"
    if len(text) > MAX_LEN:
        return f"账户长度不能超过 {MAX_LEN} 个字符"
    if _RE_UID.match(text):          # 纯数字 → UID，合法
        return None
    if text[0].isdigit():
        return "昵称不能以数字开头"
    if not _RE_NICKNAME.match(text):
        return "昵称只能包含汉字、英文字母、数字、下划线"
    return None

def _validate_password(text: str) -> str | None:
    if not text:
        return "密码不能为空"
    if len(text) > MAX_LEN:
        return f"密码长度不能超过 {MAX_LEN} 个字符"
    if not _RE_PASSWORD.match(text):
        return "密码只能包含英文字母、数字、下划线、斜杠、英文句点"
    return None

def _is_uid(text: str) -> bool:
    return bool(_RE_UID.match(text))


# ── 网络线程 ────────────────────────────────────────────────────
class NetThread(QThread):
    finished = Signal(dict)
    error    = Signal(str)

    def __init__(self, host: str, port: int, payload: dict):
        super().__init__()
        self.host, self.port, self.payload = host, port, payload

    def run(self):
        try:
            with socket.create_connection((self.host, self.port), timeout=5) as s:
                s.sendall(json.dumps(self.payload, ensure_ascii=False).encode())
                data = b""
                while chunk := s.recv(4096):
                    data += chunk
            self.finished.emit(json.loads(data.decode()))
        except (socket.timeout, ConnectionRefusedError):
            self.error.emit("无法连接到服务器，请检查地址和端口")
        except Exception as e:
            self.error.emit(f"网络错误: {e}")


# ── 服务器地址弹窗 ──────────────────────────────────────────────
class ServerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("连接服务器")
        self.setFixedSize(360, 180)
        self.setModal(True)
        self._apply_style()

        self._ip_edit   = QLineEdit("127.0.0.1")
        self._port_edit = QLineEdit("8888")
        for w in (self._ip_edit, self._port_edit):
            w.setFixedHeight(36)
            w.setFont(Fonts.UniversalPlainFont)

        confirm = QPushButton("确认连接")
        confirm.setFixedHeight(36)
        confirm.setFont(Fonts.UniversalPlainFont)
        confirm.clicked.connect(self._on_confirm)

        form = QVBoxLayout()
        for label, widget in (("服务器 IP:", self._ip_edit), ("端口:", self._port_edit)):
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setFont(Fonts.UniversalPlainFont)
            lbl.setFixedWidth(80)
            row.addWidget(lbl)
            row.addWidget(widget)
            form.addLayout(row)

        form.addSpacing(8)
        form.addWidget(confirm)
        form.setContentsMargins(24, 20, 24, 20)
        form.setSpacing(10)
        self.setLayout(form)

        self.host: str = ""
        self.port: int = 0

    def _apply_style(self):
        self.setStyleSheet("""
            QDialog { background: #1e1e2e; color: #cdd6f4; }
            QLabel  { color: #cdd6f4; }
            QLineEdit {
                background: #313244; color: #cdd6f4;
                border: 1px solid #45475a; border-radius: 6px; padding: 4px 8px;
            }
            QLineEdit:focus { border-color: #89b4fa; }
            QPushButton {
                background: #89b4fa; color: #1e1e2e; border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background: #b4befe; }
        """)

    def _on_confirm(self):
        ip   = self._ip_edit.text().strip()
        port = self._port_edit.text().strip()
        if not ip:
            QMessageBox.warning(self, "错误", "IP 地址不能为空")
            return
        if not port.isdigit() or not (1 <= int(port) <= 65535):
            QMessageBox.warning(self, "错误", "端口必须为 1~65535 的整数")
            return
        self.host = ip
        self.port = int(port)
        self.accept()


# ── 登录窗口 ────────────────────────────────────────────────────
class LoginWindow(QWidget):
    '''
    登录窗口, 继承自QWidget

    * 外观
    有登录和注册两种界面
    登录界面包含UID或昵称输入框和密码输入框
    注册界面包含昵称输入框、密码输入框和确认密码输入框
    包含登录注册模式切换按钮
    包含登录确认或注册确认按钮

    * 功能
    点击登录或注册按钮时按顺序执行以下操作:
    1. 获取所有输入框的内容并验证符号合法性(禁止非法字符、输入长度限制、字符种类要求)
    2. TCP连接服务器检查是否连接成功(是否超时)
    3. 打包用户输入的信息并向服务器发送请求
    4. 接收并处理服务器返回的信息
    5. 若要注册账户, 注册成功则提示并切换到登录界面, 注册失败仍要提示
    6. 若要登录账户, 登录成功则进入主界面, 否则提示错误
    '''

    def __init__(self):
        super().__init__()
        self.setWindowTitle("USTBChat — 登录")
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedSize(600, 360)
        self._net_thread: NetThread | None = None
        self._server_host = ""
        self._server_port = 0
        self._apply_style()
        self.initUI()

    # ── 样式 ──────────────────────────────────────────────────
    def _apply_style(self):
        self.setStyleSheet("""
            QWidget#loginWindow, QWidget#registerWindow {
                background: #1e1e2e;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 4px 10px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            QPushButton#mainBtn {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #89b4fa, stop:1 #b4befe);
                color: #1e1e2e;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton#mainBtn:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #b4befe, stop:1 #cba6f7);
            }
            QPushButton#mainBtn:disabled {
                background: #45475a;
                color: #6c7086;
            }
            QPushButton#smallBtn {
                background: transparent;
                color: #89b4fa;
                border: none;
                text-decoration: underline;
            }
            QPushButton#smallBtn:hover { color: #b4befe; }
        """)

    # ── 初始化 ────────────────────────────────────────────────
    def initUI(self):
        self.creWidgets()
        self.applyLayout()
        self.connectSignals()

    def creWidgets(self):
        self.idInputer        = TextInput("账户: ",    "请输入你的UID或昵称")
        self.idInputer.setAlignment(ClassicLayout.Left)
        self.pwdInputer       = TextInput("密码: ",    "请输入密码",         TextInput.Hidden)
        self.pwdInputer.setAlignment(ClassicLayout.Left)
        self.pwdVerification  = TextInput("确认密码: ", "再次输入相同的密码",  TextInput.Hidden)
        self.pwdVerification.setAlignment(ClassicLayout.Left)

        # 注册界面的昵称输入框（不允许纯数字）
        self.nicknameInputer  = TextInput("昵称: ",    "请输入昵称")
        self.nicknameInputer.setAlignment(ClassicLayout.Left)

        self.loginButton    = Button("登录", "信息填写完毕后点击登录")
        self.registerButton = Button("注册", "信息填写完毕后点击注册")
        for btn in (self.loginButton, self.registerButton):
            btn.setObjectName("mainBtn")

        self.pwdFoundButtonLogin    = Button("找回密码", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        self.pwdFoundButtonRegister = Button("找回密码", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        self.regAccountButton       = Button("注册账户", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        self.loginAccountButton     = Button("登录账户", size=(100, 24), font=Fonts.sizedFont(Fonts.UniversalPlainFont, 10))
        for btn in (self.pwdFoundButtonLogin, self.pwdFoundButtonRegister,
                    self.regAccountButton, self.loginAccountButton):
            btn.setObjectName("smallBtn")

        self.loginWindow    = QWidget(); self.loginWindow.setObjectName("loginWindow")
        self.registerWindow = QWidget(); self.registerWindow.setObjectName("registerWindow")
        self.loginWindow.setFixedSize(600, 360)
        self.registerWindow.setFixedSize(600, 360)

    def applyLayout(self):
        self.mainLayout = ClassicLayout.Vertical(constr=ClassicLayout.Default,
                                                 margins=ClassicLayout.NoBorder, spacing=0)

        # 登录界面底部小按钮行
        pnrLayout = ClassicLayout.Horizontal(constr=ClassicLayout.MinMax,
                                             margins=(80, 0, 80, 0), spacing=0)
        pnrLayout.addWidget(self.pwdFoundButtonLogin, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        pnrLayout.addStretch(1)
        pnrLayout.addWidget(self.regAccountButton, 0, alignment=Qt.AlignmentFlag.AlignRight)

        # 注册界面底部小按钮行
        pnlLayout = ClassicLayout.Horizontal(constr=ClassicLayout.MinMax,
                                             margins=(80, 0, 80, 0), spacing=0)
        pnlLayout.addWidget(self.pwdFoundButtonRegister, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        pnlLayout.addStretch(1)
        pnlLayout.addWidget(self.loginAccountButton, 0, alignment=Qt.AlignmentFlag.AlignRight)

        # 登录界面布局
        loginLayout = ClassicLayout.Vertical(align=ClassicLayout.CTop, constr=ClassicLayout.MinMax,
                                             margins=(80, 40, 80, 30), spacing=12)
        loginLayout.addLayout(self.idInputer, 0)
        loginLayout.addLayout(self.pwdInputer, 0)
        loginLayout.addLayout(pnrLayout, 0)
        loginLayout.addStretch(1)
        loginLayout.addWidget(self.loginButton, 0, alignment=ClassicLayout.CBottom)

        # 注册界面布局
        registerLayout = ClassicLayout.Vertical(align=ClassicLayout.CTop, constr=ClassicLayout.MinMax,
                                                margins=(80, 30, 80, 20), spacing=10)
        registerLayout.addLayout(self.nicknameInputer, 0)
        registerLayout.addLayout(self.pwdInputer, 0)
        registerLayout.addLayout(self.pwdVerification, 0)
        registerLayout.addLayout(pnlLayout, 0)
        registerLayout.addStretch(1)
        registerLayout.addWidget(self.registerButton, 0, alignment=ClassicLayout.CBottom)

        self.loginWindow.setLayout(loginLayout)
        self.registerWindow.setLayout(registerLayout)

        self.switchLayout = QStackedLayout()
        self.switchLayout.setSizeConstraint(ClassicLayout.MinMax)
        self.switchLayout.setContentsMargins(0, 0, 0, 0)
        self.switchLayout.setSpacing(0)
        self.switchLayout.addWidget(self.loginWindow)
        self.switchLayout.addWidget(self.registerWindow)

        self.mainLayout.addLayout(self.switchLayout, 1)
        self.setLayout(self.mainLayout)

    def connectSignals(self):
        self.loginButton.clicked.connect(self._on_login)
        self.registerButton.clicked.connect(self._on_register)
        self.regAccountButton.clicked.connect(lambda: self.switchLayout.setCurrentIndex(1))
        self.loginAccountButton.clicked.connect(lambda: self.switchLayout.setCurrentIndex(0))
        # 找回密码暂不处理
        self.pwdFoundButtonLogin.clicked.connect(lambda: None)
        self.pwdFoundButtonRegister.clicked.connect(lambda: None)

    # ── 服务器地址获取 ────────────────────────────────────────
    def _get_server(self) -> bool:
        """弹出对话框让用户输入服务器地址，返回是否成功"""
        dlg = ServerDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._server_host = dlg.host
            self._server_port = dlg.port
            return True
        return False

    # ── 验证 ──────────────────────────────────────────────────
    def _validate_login(self) -> tuple[bool, dict]:
        id_text  = self.idInputer.getInput().strip()
        pwd_text = self.pwdInputer.getInput().strip()

        err = _validate_id(id_text)
        if err:
            QMessageBox.warning(self, "输入错误", err); return False, {}

        err = _validate_password(pwd_text)
        if err:
            QMessageBox.warning(self, "输入错误", err); return False, {}

        payload = {"type": "login", "password": pwd_text}
        if _is_uid(id_text):
            payload["uid"] = id_text
        else:
            payload["nickname"] = id_text
        return True, payload

    def _validate_register(self) -> tuple[bool, dict]:
        nick_text = self.nicknameInputer.getInput().strip()
        pwd_text  = self.pwdInputer.getInput().strip()
        pwd2_text = self.pwdVerification.getInput().strip()

        # 昵称验证（注册时只允许昵称，不允许纯数字）
        if not nick_text:
            QMessageBox.warning(self, "输入错误", "昵称不能为空"); return False, {}
        if len(nick_text) > MAX_LEN:
            QMessageBox.warning(self, "输入错误", f"昵称长度不能超过 {MAX_LEN} 个字符"); return False, {}
        if _is_uid(nick_text):
            QMessageBox.warning(self, "输入错误", "昵称不能由纯数字组成"); return False, {}
        if nick_text[0].isdigit():
            QMessageBox.warning(self, "输入错误", "昵称不能以数字开头"); return False, {}
        if not _RE_NICKNAME.match(nick_text):
            QMessageBox.warning(self, "输入错误", "昵称只能包含汉字、英文字母、数字、下划线"); return False, {}

        err = _validate_password(pwd_text)
        if err:
            QMessageBox.warning(self, "输入错误", err); return False, {}

        if pwd_text != pwd2_text:
            QMessageBox.warning(self, "输入错误", "两次输入的密码不一致"); return False, {}

        return True, {"type": "register", "nickname": nick_text, "password": pwd_text}

    # ── 网络请求 ──────────────────────────────────────────────
    def _send_request(self, payload: dict, on_success, on_fail=None):
        if not self._get_server():
            return
        self._set_buttons_enabled(False)
        self._net_thread = NetThread(self._server_host, self._server_port, payload)
        self._net_thread.finished.connect(lambda resp: self._on_response(resp, on_success, on_fail))
        self._net_thread.error.connect(self._on_net_error)
        self._net_thread.start()

    def _on_response(self, resp: dict, on_success, on_fail):
        self._set_buttons_enabled(True)
        if resp.get("status") == "ok":
            on_success(resp)
        else:
            msg = resp.get("message", "操作失败，请重试")
            if on_fail:
                on_fail(msg)
            else:
                QMessageBox.warning(self, "失败", msg)

    def _on_net_error(self, msg: str):
        self._set_buttons_enabled(True)
        QMessageBox.critical(self, "网络错误", msg)

    def _set_buttons_enabled(self, enabled: bool):
        self.loginButton.setEnabled(enabled)
        self.registerButton.setEnabled(enabled)

    # ── 登录 / 注册 ───────────────────────────────────────────
    def _on_login(self):
        ok, payload = self._validate_login()
        if not ok:
            return
        self._send_request(payload, self._login_success)

    def _login_success(self, _):
        # TODO: 替换为实际主界面
        QMessageBox.information(self, "登录成功", "欢迎回来！（主界面待实现）")

    def _on_register(self):
        ok, payload = self._validate_register()
        if not ok:
            return
        self._send_request(payload, self._register_success)

    def _register_success(self, _):
        QMessageBox.information(self, "注册成功", "账户注册成功，请登录")
        self.switchLayout.setCurrentIndex(0)


if __name__ == '__main__':
    MMApp = QApplication(sys.argv)
    Window = LoginWindow()
    Window.show()
    MMApp.exec()
