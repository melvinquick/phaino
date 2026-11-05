from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class CommandPalette(QDialog):
    command_selected = Signal(QAction)
    paste_requested = Signal()

    def __init__(self, get_focus_target, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Command Palette")
        self.setObjectName("CommandPalette")
        self.resize(600, 400)
        self.setModal(True)

        self.all_actions = []
        self.get_focus_target = get_focus_target

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a command...")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._execute_selected)
        layout.addWidget(self.input)

        self.list_widget = QListWidget()
        self.list_widget.itemActivated.connect(self._execute_item)
        layout.addWidget(self.list_widget)

        self.lbl_hint = QLabel("Enter to run, Esc to cancel")
        self.lbl_hint.setObjectName("CommandPaletteHint")
        layout.addWidget(self.lbl_hint)

    def populate(self, actions):
        self.all_actions = [a for a in actions if a.text() and a.isEnabled()]
        self._rebuild_list(self.all_actions)
        self.input.clear()
        self.input.setFocus()

    def _rebuild_list(self, actions):
        self.list_widget.clear()
        for action in actions:
            shortcut = ""
            if action.shortcut():
                shortcut = action.shortcut().toString(QKeySequence.NativeText)
            text = action.text().replace("&", "")
            item_text = f"{text}    {shortcut}" if shortcut else text
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, action)
            self.list_widget.addItem(item)
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter(self, query):
        query = query.strip().lower()
        if not query:
            self._rebuild_list(self.all_actions)
            return
        filtered = [
            a for a in self.all_actions if query in a.text().replace("&", "").lower()
        ]
        self._rebuild_list(filtered)

    def _execute_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._execute_item(item)

    def _execute_item(self, item):
        action = item.data(Qt.UserRole)
        if not action:
            return
        self.accept()
        # Special-case Paste: emit signal so app.py can insert the pre-captured clipboard text
        if action.text().replace("&", "").lower() == "paste":
            self.paste_requested.emit()
            return
        target = self.get_focus_target()
        if target:
            target.setFocus()
        action.trigger()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
