import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFileSystemModel


class GitFileSystemModel(QFileSystemModel):
    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.theme_tokens = theme_tokens
        self.git_changed_files = set()

    def set_git_changes(self, changed_files):
        self.git_changed_files = {os.path.abspath(f) for f in changed_files}
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole and index.isValid():
            file_path = os.path.abspath(self.filePath(index))
            if file_path in self.git_changed_files:
                return QColor(self.theme_tokens.get("warning-color"))
        return super().data(index, role)

    def update_theme(self, theme_tokens):
        self.theme_tokens = theme_tokens
        self.layoutChanged.emit()
