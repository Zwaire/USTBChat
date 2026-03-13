# -*- coding: utf-8 -*-

class Theme:
    Dark = '''
        QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-family: "Segoe UI", Arial, sans-serif;
            font-size: 14px;
        }

        QMainWindow, QDialog {
            background-color: #1e1e2e;
        }

        QPushButton {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 4px 12px;
        }
        QPushButton:hover {
            background-color: #45475a;
            border-color: #89b4fa;
        }
        QPushButton:pressed {
            background-color: #89b4fa;
            color: #1e1e2e;
        }
        QPushButton:disabled {
            background-color: #313244;
            color: #585b70;
            border-color: #313244;
        }

        QLineEdit, QPlainTextEdit, QTextEdit {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 4px 8px;
            selection-background-color: #89b4fa;
            selection-color: #1e1e2e;
        }
        QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
            border-color: #89b4fa;
        }
        QLineEdit::placeholder {
            color: #585b70;
        }

        QLabel {
            background-color: transparent;
            color: #cdd6f4;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }
        QScrollBar:vertical {
            background-color: #1e1e2e;
            width: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical {
            background-color: #45475a;
            border-radius: 4px;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background-color: #585b70;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            background-color: #1e1e2e;
            height: 8px;
            border-radius: 4px;
        }
        QScrollBar::handle:horizontal {
            background-color: #45475a;
            border-radius: 4px;
            min-width: 20px;
        }
        QScrollBar::handle:horizontal:hover {
            background-color: #585b70;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        QFrame[frameShape="4"], QFrame[frameShape="5"] {
            background-color: #45475a;
            border: none;
        }

        QMenu {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 6px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 20px;
            border-radius: 4px;
        }
        QMenu::item:selected {
            background-color: #45475a;
        }

        QMessageBox {
            background-color: #1e1e2e;
        }
        QMessageBox QLabel {
            color: #cdd6f4;
        }
    '''

    Normal = '''
        QWidget {
            background-color: #f4f7fb;
            color: #1f2937;
            font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
            font-size: 14px;
        }

        QLabel {
            background-color: transparent;
            color: #1f2937;
        }

        QPushButton {
            background-color: #2f80ed;
            color: #ffffff;
            border: 1px solid #2f80ed;
            border-radius: 8px;
            padding: 5px 10px;
        }
        QPushButton:hover {
            background-color: #256fd1;
            border-color: #256fd1;
        }
        QPushButton:pressed {
            background-color: #1f5fb3;
            border-color: #1f5fb3;
        }

        QLineEdit, QPlainTextEdit, QTextEdit {
            background-color: #ffffff;
            color: #1f2937;
            border: 1px solid #d5deea;
            border-radius: 8px;
            padding: 6px 8px;
            selection-background-color: #dbeafe;
            selection-color: #1f2937;
        }
        QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus {
            border: 1px solid #2f80ed;
        }

        QMenu {
            background-color: #ffffff;
            border: 1px solid #d5deea;
            border-radius: 8px;
            padding: 4px;
        }
        QMenu::item {
            padding: 6px 16px;
            border-radius: 6px;
        }
        QMenu::item:selected {
            background-color: #eef4ff;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }
        QScrollBar:vertical {
            width: 8px;
            background: transparent;
        }
        QScrollBar::handle:vertical {
            border-radius: 4px;
            background: #cad7e6;
            min-height: 20px;
        }
        QScrollBar::handle:vertical:hover {
            background: #9fb2c8;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0px;
        }
        QScrollBar:horizontal {
            height: 8px;
            background: transparent;
        }
        QScrollBar::handle:horizontal {
            border-radius: 4px;
            background: #cad7e6;
            min-width: 20px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            width: 0px;
        }

        QWidget#FriendBar {
            border: 1px solid #c9d9ef;
            border-radius: 8px;
            background-color: #ffffff;
        }
    '''
