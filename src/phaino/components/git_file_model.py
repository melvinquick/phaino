from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QFileSystemModel


class GitFileSystemModel(QFileSystemModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.git_changed_files = set()

    def set_git_changes(self, changed_files):
        self.git_changed_files = changed_files
        self.layoutChanged.emit()

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ForegroundRole and index.isValid():
            file_path = self.filePath(index)
            if file_path in self.git_changed_files:
                return QColor("#EBCB8B")  # Warning yellow color
        return super().data(index, role)
