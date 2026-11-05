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
    replace_requested = Signal(str, str, list)
    closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("SearchPanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search in folder...")
        self.search_input.returnPressed.connect(self.perform_search)

        self.btn_search = QPushButton("Search")
        self.btn_search.clicked.connect(self.perform_search)

        self.btn_close = QPushButton("✕")
        self.btn_close.setObjectName("CloseFindButton")
        self.btn_close.setFixedWidth(30)
        self.btn_close.clicked.connect(self.close_panel)

        search_row.addWidget(self.search_input)
        search_row.addWidget(self.btn_search)
        search_row.addWidget(self.btn_close)
        layout.addLayout(search_row)

        replace_row = QHBoxLayout()
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("Replace with...")

        self.btn_check_all = QPushButton("Check All")
        self.btn_check_all.clicked.connect(self._toggle_all_checks)

        self.btn_replace = QPushButton("Replace Checked")
        self.btn_replace.clicked.connect(self.replace_checked)

        replace_row.addWidget(self.replace_input)
        replace_row.addWidget(self.btn_check_all)
        replace_row.addWidget(self.btn_replace)
        layout.addLayout(replace_row)

        self.results_tree = QTreeWidget()
        self.results_tree.setHeaderLabels(["File / Line", "Match"])
        self.results_tree.setColumnWidth(0, 250)
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
        IGNORE_DIRS = {"__pycache__", "node_modules", ".venv", ".git"}

        for root, dirs, files in os.walk(self.current_root):
            dirs[:] = [
                d for d in dirs if not d.startswith(".") and d not in IGNORE_DIRS
            ]

            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()

                    matches = []
                    for line_num, line in enumerate(lines, 1):
                        if query in line:
                            matches.append((line_num, line.strip()))

                    if matches:
                        rel_path = os.path.relpath(file_path, self.current_root)
                        file_item = QTreeWidgetItem(self.results_tree, [rel_path, ""])
                        file_item.setFlags(file_item.flags() | Qt.ItemIsUserCheckable)
                        file_item.setCheckState(0, Qt.Unchecked)
                        file_item.setData(0, Qt.UserRole, file_path)

                        for line_num, line_text in matches:
                            match_item = QTreeWidgetItem(
                                file_item, [f"Line {line_num}", line_text]
                            )
                            match_item.setData(0, Qt.UserRole, (file_path, line_num))

                        file_item.setExpanded(True)
                except (UnicodeDecodeError, PermissionError):
                    continue

    def on_result_clicked(self, item, column):
        data = item.data(0, Qt.UserRole)
        if isinstance(data, tuple):
            file_path, line_num = data
            self.result_clicked.emit(file_path, line_num)

    def _toggle_all_checks(self):
        if self.results_tree.topLevelItemCount() == 0:
            return

        first_item = self.results_tree.topLevelItem(0)
        target_state = (
            Qt.Unchecked if first_item.checkState(0) == Qt.Checked else Qt.Checked
        )

        for i in range(self.results_tree.topLevelItemCount()):
            item = self.results_tree.topLevelItem(i)
            item.setCheckState(0, target_state)

        self.btn_check_all.setText(
            "Uncheck All" if target_state == Qt.Checked else "Check All"
        )

    def replace_checked(self):
        query = self.search_input.text().strip()
        replacement = self.replace_input.text()
        if not query or not self.current_root:
            return

        checked_files = []
        for i in range(self.results_tree.topLevelItemCount()):
            file_item = self.results_tree.topLevelItem(i)
            if file_item.checkState(0) == Qt.Checked:
                file_path = file_item.data(0, Qt.UserRole)
                if file_path:
                    checked_files.append(file_path)

        if not checked_files:
            return

        self.replace_requested.emit(query, replacement, checked_files)
