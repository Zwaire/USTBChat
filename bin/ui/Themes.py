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

    Button:hover {
        background-color: #888888;
        border: 1px solid #007acc;
    }



'''
