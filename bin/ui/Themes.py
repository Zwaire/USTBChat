# -*- coding: utf-8 -*-

class Theme:
    Dark = '''
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
            QMessageBox { background-color: #1e1e2e; color: #cdd6f4; }
            QMessageBox QLabel { color: #cdd6f4; }
            QMessageBox QPushButton {
                background: #89b4fa; color: #1e1e2e; border-radius: 6px;
                font-weight: bold; min-width: 80px; min-height: 30px;
            }
            QMessageBox QPushButton:hover { background: #b4befe; }


'''
