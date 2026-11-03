import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)


class SearchPanel(QWidget):
    result_clicked = Signal(str, int)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        top_bar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in folder...")
        self.search_input.returnPressed.connect(self.perform_search)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.perform_search)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("CloseFindButton")
        self.btn_close.setFixedWidth(30)
        self.btn_close.clicked.connect(self.close_panel)

        top_bar.addWidget(self.search_input)
        top_bar.addWidget(self.btn_search)
        top_bar.addWidget(self.btn_close)
        layout.addLayout(top_bar)

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["File / Line", "Match"])
        self.results_tree.setColumnWidth(0, 200)
        self.results_tree.itemDoubleClicked.connect(self.on_result_clicked)
        layout.addWidget(self.results_tree)

        self.current_root = ""

    def close_panel(self):
        self.hide()
        self.closed.emit()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close_panel()
        else:
            super().keyPressEvent(event)

    def set_root(self, path):
        self.current_root = path

    def perform_search(self):
        query = self.search_input.text().strip()
        if not query or not self.current_root:
            return

        self.results_tree.clear()
        IGNORE_DIRS = {"__pycache__", "node_modules", ".venv"}

        for root, dirs, files in os.walk(self.current_root):
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS
            ]

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line_num, line in enumerate(f, 1):
                            if query in line:
                                rel_path = os.path.relpath(file_path, self.current_root)
                                file_item = QTreeWidgetItem(
                                    self.results_tree, [rel_path, ""]
                                )
                                match_item = QTreeWidgetItem(
                                    file_item, [f"Line {line_num}", line.strip()]
                                )
                                match_item.setData(
                                    0, Qt.UserRole, (file_path, line_num)
                                )
                                file_item.setExpanded(True)
                except (UnicodeDecodeError, PermissionError):
                    continue

    def on_result_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if data:
            file_path, line_num = data
            self.result_clicked.emit(file_path, line_num)
