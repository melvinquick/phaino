from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QTextDocument
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class FindReplaceWidget(QWidget):
    closed = Signal()

    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.setObjectName("FindReplaceWidget")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.editor = editor
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(10, 5, 10, 5)

        self.find_input = QLineEdit()
        self.find_input.setPlaceholderText("Find...")
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")

        self.btn_find_prev = QPushButton("Prev")
        self.btn_find_next = QPushButton("Next")
        self.btn_replace = QPushButton("Replace")
        self.btn_replace_all = QPushButton("Replace All")
        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("CloseFindButton")

        self.layout.addWidget(self.find_input)
        self.layout.addWidget(self.btn_find_prev)
        self.layout.addWidget(self.btn_find_next)
        self.layout.addWidget(self.replace_input)
        self.layout.addWidget(self.btn_replace)
        self.layout.addWidget(self.btn_replace_all)
        self.layout.addWidget(self.btn_close)

        self.btn_find_prev.clicked.connect(self.find_previous)
        self.btn_find_next.clicked.connect(self.find_next)
        self.btn_replace.clicked.connect(self.replace)
        self.btn_replace_all.clicked.connect(self.replace_all)
        self.btn_close.clicked.connect(self.close_widget)
        self.find_input.returnPressed.connect(self.find_next)

        self.hide()

    def set_editor(self, editor):
        self.editor = editor

    def close_widget(self):
        self.hide()
        self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_widget()
        else:
            super().keyPressEvent(event)

    def find_next(self):
        text = self.find_input.text()
        if not text or not self.editor:
            return

        if not self.editor.find(text):
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            self.editor.setTextCursor(cursor)
            self.editor.find(text)

    def find_previous(self):
        text = self.find_input.text()
        if not text or not self.editor:
            return

        if not self.editor.find(text, QTextDocument.FindBackward):
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.End)
            self.editor.setTextCursor(cursor)
            self.editor.find(text, QTextDocument.FindBackward)

    def replace(self):
        text = self.find_input.text()
        repl = self.replace_input.text()
        if not text or not self.editor:
            return

        cursor = self.editor.textCursor()
        if cursor.hasSelection() and cursor.selectedText() == text:
            cursor.insertText(repl)
        self.find_next()

    def replace_all(self):
        text = self.find_input.text()
        repl = self.replace_input.text()
        if not text or not self.editor:
            return

        cursor = self.editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        self.editor.setTextCursor(cursor)

        count = 0
        while self.editor.find(text):
            self.editor.textCursor().insertText(repl)
            count += 1

        self.editor.setTextCursor(cursor)
        print(f"Replaced {count} occurrences.")
