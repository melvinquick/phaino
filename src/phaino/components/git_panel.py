import subprocess
import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QMenu,
)


class GitPanel(QWidget):
    file_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("GitPanel")
        self.working_dir = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        # --- Header ---
        self.lbl_branch = QLabel("Branch: (not a repo)")
        self.lbl_branch.setObjectName("GitBranchLabel")
        layout.addWidget(self.lbl_branch)

        # --- Changed Files ---
        layout.addWidget(QLabel("Changes:"))
        self.changes_tree = QTreeWidget()
        self.changes_tree.setHeaderLabels(["File", "Status"])
        self.changes_tree.setColumnWidth(0, 150)
        self.changes_tree.itemDoubleClicked.connect(self.on_file_double_clicked)

        # Add right-click context menu
        self.changes_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.changes_tree.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.changes_tree)

        # --- Commit Message ---
        layout.addWidget(QLabel("Commit Message:"))
        self.commit_input = QTextEdit()
        self.commit_input.setPlaceholderText("Enter commit message...")
        self.commit_input.setFixedHeight(60)
        layout.addWidget(self.commit_input)

        # --- Action Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_stage_all = QPushButton("Stage All")
        self.btn_stage_all.clicked.connect(self.stage_all)

        self.btn_commit = QPushButton("Commit")
        self.btn_commit.setObjectName("PrimaryButton")
        self.btn_commit.clicked.connect(self.commit)

        self.btn_push = QPushButton("Push")
        self.btn_push.clicked.connect(self.push)

        btn_layout.addWidget(self.btn_stage_all)
        btn_layout.addWidget(self.btn_commit)
        btn_layout.addWidget(self.btn_push)
        layout.addLayout(btn_layout)

    def set_working_dir(self, path):
        self.working_dir = path
        self.refresh()

    def run_git(self, args):
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.stdout.strip()
        except Exception:
            return ""

    def refresh(self):
        if not self.working_dir or not os.path.isdir(
            os.path.join(self.working_dir, ".git")
        ):
            self.lbl_branch.setText("Branch: (not a repo)")
            self.changes_tree.clear()
            return

        branch = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        self.lbl_branch.setText(f"Branch: {branch}")

        self.changes_tree.clear()
        status_output = self.run_git(["status", "--porcelain"])

        for line in status_output.splitlines():
            if len(line) > 3:
                status_code = line[:2].strip()
                file_path = line[3:].strip()

                status_map = {
                    "M": "Modified",
                    "A": "Added",
                    "D": "Deleted",
                    "R": "Renamed",
                    "??": "Untracked",
                    "MM": "Staged+Modified",
                    "AM": "Staged+Modified",
                }
                status_text = status_map.get(status_code, status_code)

                item = QTreeWidgetItem(self.changes_tree, [file_path, status_text])
                item.setData(0, Qt.UserRole, os.path.join(self.working_dir, file_path))
                item.setData(0, Qt.UserRole + 1, file_path)

    def show_context_menu(self, pos):
        item = self.changes_tree.itemAt(pos)
        if not item:
            return

        file_path = item.data(0, Qt.UserRole + 1)
        status = item.text(1)

        menu = QMenu(self)

        # If the file is untracked or modified (but not staged), show Stage
        if status in ["Modified", "Untracked", "Deleted"]:
            stage_action = menu.addAction("Stage File")
        # If the file is staged or staged+modified, show Unstage
        elif status in ["Added", "Staged+Modified", "AM"]:
            stage_action = menu.addAction("Unstage File")
        else:
            stage_action = None

        action = menu.exec(self.changes_tree.viewport().mapToGlobal(pos))

        if action and action == stage_action:
            if action.text() == "Stage File":
                self.run_git(["add", file_path])
            else:
                self.run_git(["reset", "HEAD", file_path])
            self.refresh()

    def on_file_double_clicked(self, item, column):
        file_path = item.data(0, Qt.UserRole)
        if file_path and os.path.isfile(file_path):
            self.file_selected.emit(file_path)

    def stage_all(self):
        self.run_git(["add", "."])
        self.refresh()

    def commit(self):
        msg = self.commit_input.toPlainText().strip()
        if not msg:
            return

        self.run_git(["commit", "-m", msg])
        self.commit_input.clear()
        self.refresh()

    def push(self):
        branch = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if branch:
            self.run_git(["push", "--set-upstream", "origin", branch])
        self.refresh()
