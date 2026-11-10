import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)


class QuickOpen(QDialog):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Quick Open")
        self.setObjectName("CommandPalette")
        self.resize(600, 400)
        self.setModal(True)

        self.all_files = []
        self.root_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Search files by name...")
        self.input.textChanged.connect(self._filter)
        self.input.returnPressed.connect(self._execute_selected)
        layout.addWidget(self.input)

        self.list_widget = QListWidget()
        self.list_widget.itemActivated.connect(self._execute_item)
        layout.addWidget(self.list_widget)

        self.lbl_hint = QLabel("Enter to open, Esc to cancel")
        self.lbl_hint.setObjectName("CommandPaletteHint")
        layout.addWidget(self.lbl_hint)

    def populate(self, root_path):
        self.root_path = root_path
        self.all_files = []

        ignore_dirs = {
            ".git",
            "__pycache__",
            "node_modules",
            ".venv",
            "venv",
            "dist",
            "build",
        }

        for root, dirs, files in os.walk(self.root_path):
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in ignore_dirs
            ]
            for file in files:
                if not file.startswith("."):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, self.root_path)
                    self.all_files.append((file, rel_path, full_path))

        self.all_files.sort(key=lambda x: x[1].lower())

        self._rebuild_list(self.all_files)
        self.input.clear()
        self.input.setFocus()

    def _rebuild_list(self, files):
        self.list_widget.clear()
        for name, rel_path, full_path in files:
            item = QListWidgetItem(rel_path)
            item.setData(Qt.UserRole, full_path)
            self.list_widget.addItem(item)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _filter(self, query):
        query = query.strip().lower()
        if not query:
            self._rebuild_list(self.all_files)
            return

        filtered = [
            f for f in self.all_files if query in f[0].lower() or query in f[1].lower()
        ]
        self._rebuild_list(filtered)

    def _execute_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._execute_item(item)

    def _execute_item(self, item):
        file_path = item.data(Qt.UserRole)
        if file_path:
            self.accept()
            self.file_selected.emit(file_path)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
