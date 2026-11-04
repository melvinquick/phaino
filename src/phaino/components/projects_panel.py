import json
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class ProjectsPanel(QWidget):
    project_opened = Signal(str)
    projects_changed = Signal(list)
    add_current_requested = Signal()

    def __init__(self, settings, theme_tokens, parent=None):
        super().__init__(parent)
        self.setObjectName("ProjectsPanel")
        self.settings = settings
        self.theme_tokens = theme_tokens
        self.projects = self._load_projects()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.lbl_hint = QLabel("No saved projects. Use Add Current Folder to save one.")
        self.lbl_hint.setObjectName("ProjectsHintLabel")
        self.lbl_hint.setWordWrap(True)
        layout.addWidget(self.lbl_hint)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(self._on_double_clicked)
        self.list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_widget.customContextMenuRequested.connect(self._show_context_menu)
        layout.addWidget(self.list_widget)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Current Folder")
        self.btn_add.clicked.connect(self._on_add_current_folder)
        self.btn_open = QPushButton("Open Selected")
        self.btn_open.clicked.connect(self._on_open_selected)
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_open)
        layout.addLayout(btn_layout)

        self._refresh_list()

    def set_theme_tokens(self, theme_tokens):
        self.theme_tokens = theme_tokens

    def _load_projects(self):
        raw = self.settings.value("projects", "[]")
        try:
            projects = json.loads(raw)
            if not isinstance(projects, list):
                return []
            return [
                p
                for p in projects
                if isinstance(p, dict) and "name" in p and "path" in p
            ]
        except (json.JSONDecodeError, TypeError):
            return []

    def _save_projects(self):
        self.settings.setValue("projects", json.dumps(self.projects))
        self.projects_changed.emit(self.projects)

    def _refresh_list(self):
        self.list_widget.clear()
        for project in self.projects:
            item_text = f"{project['name']}  —  {project['path']}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, project)
            self.list_widget.addItem(item)

        has_projects = len(self.projects) > 0
        self.lbl_hint.setVisible(not has_projects)
        self.list_widget.setVisible(has_projects)

    def _prompt_name(self, default):
        name, ok = QInputDialog.getText(
            self, "Project Name", "Enter a name for this project:", text=default
        )
        if ok and name.strip():
            return name.strip()
        return None

    def add_project(self, path, default_name=None):
        if not path or not os.path.isdir(path):
            return
        name = self._prompt_name(
            default_name or os.path.basename(path.rstrip("/")) or path
        )
        if not name:
            return
        self.projects.append({"name": name, "path": path})
        self._save_projects()
        self._refresh_list()

    def _on_add_current_folder(self):
        self.add_current_requested.emit()

    def _on_open_selected(self):
        item = self.list_widget.currentItem()
        if item:
            self._open_item(item)

    def _on_double_clicked(self, item):
        self._open_item(item)

    def _open_item(self, item):
        project = item.data(Qt.UserRole)
        if not project:
            return
        path = project["path"]
        if not os.path.isdir(path):
            reply = QMessageBox.question(
                self,
                "Project Not Found",
                f"The folder '{path}' no longer exists.\n\nRemove this project entry?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.projects = [p for p in self.projects if p["path"] != path]
                self._save_projects()
                self._refresh_list()
            return
        self.project_opened.emit(path)

    def _show_context_menu(self, pos):
        item = self.list_widget.itemAt(pos)
        if not item:
            return
        menu = QMenu(self)
        open_action = menu.addAction("Open")
        rename_action = menu.addAction("Rename")
        remove_action = menu.addAction("Remove")
        action = menu.exec(self.list_widget.viewport().mapToGlobal(pos))
        if action == open_action:
            self._open_item(item)
        elif action == rename_action:
            self._rename_item(item)
        elif action == remove_action:
            self._remove_item(item)

    def _rename_item(self, item):
        project = item.data(Qt.UserRole)
        if not project:
            return
        new_name, ok = QInputDialog.getText(
            self, "Rename Project", "New name:", text=project["name"]
        )
        if ok and new_name.strip():
            project["name"] = new_name.strip()
            self._save_projects()
            self._refresh_list()

    def _remove_item(self, item):
        project = item.data(Qt.UserRole)
        if not project:
            return
        self.projects = [p for p in self.projects if p["path"] != project["path"]]
        self._save_projects()
        self._refresh_list()
