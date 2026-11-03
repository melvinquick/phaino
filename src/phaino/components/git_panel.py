import os
import subprocess

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QBrush, QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMenu,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class GitPanel(QWidget):
    file_selected = Signal(str)
    diff_requested = Signal(str)
    repo_changed = Signal()

    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.setObjectName("GitPanel")
        self.theme_tokens = theme_tokens
        self.working_dir = ""

        self.current_staged_files = []
        self.current_unstaged_files = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)

        self.lbl_branch = QLabel("Branch: (not a repo)")
        self.lbl_branch.setObjectName("GitBranchLabel")
        layout.addWidget(self.lbl_branch)

        self.changes_table = QTableWidget()
        self.changes_table.setColumnCount(2)
        self.changes_table.setHorizontalHeaderLabels(["File", "Status"])
        self.changes_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.Stretch
        )
        self.changes_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeToContents
        )
        self.changes_table.verticalHeader().setVisible(False)
        self.changes_table.setShowGrid(False)
        self.changes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.changes_table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.changes_table.cellDoubleClicked.connect(self.on_cell_double_clicked)
        self.changes_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.changes_table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addWidget(self.changes_table)

        layout.addWidget(QLabel("Commit Message:"))
        self.commit_input = QTextEdit()
        self.commit_input.setPlaceholderText("Enter commit message...")
        self.commit_input.setFixedHeight(60)
        layout.addWidget(self.commit_input)

        btn_layout = QHBoxLayout()
        self.btn_pull = QPushButton("Pull")
        self.btn_pull.clicked.connect(self.pull)

        self.btn_stage_toggle = QPushButton("Stage All")
        self.btn_stage_toggle.clicked.connect(self.toggle_stage_all)
        self.btn_stage_toggle.setFixedWidth(100)

        self.btn_commit = QPushButton("Commit")
        self.btn_commit.setObjectName("PrimaryButton")
        self.btn_commit.clicked.connect(self.commit)

        self.btn_push = QPushButton("Push")
        self.btn_push.clicked.connect(self.push)

        self.btn_undo = QPushButton("Undo Commit")
        self.btn_undo.clicked.connect(self.undo_commit)

        btn_layout.addWidget(self.btn_pull)
        btn_layout.addWidget(self.btn_stage_toggle)
        btn_layout.addWidget(self.btn_commit)
        btn_layout.addWidget(self.btn_push)
        btn_layout.addWidget(self.btn_undo)
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
                timeout=60,
            )
            if result.stderr.strip():
                print(f"GIT STDERR ({' '.join(args)}): {result.sptderr.strip()}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            print(f"GIT TIMEOUT: {' '.join(args)}")
            return ""
        except Exception as e:
            print(f"GIT EXCEPTION: {e}")
            return ""

    def refresh(self):
        self.changes_table.setRowCount(0)

        if not self.working_dir or not os.path.isdir(
            os.path.join(self.working_dir, ".git")
        ):
            self.lbl_branch.setText("Branch: (not a repo)")
            return

        branch = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        self.lbl_branch.setText(f"Branch: {branch}")

        staged_output = self.run_git(["diff", "--name-only", "--cached"])
        self.current_staged_files = []
        if staged_output:
            for f in staged_output.splitlines():
                self.current_staged_files.append((f.strip(), "Staged"))

        unstaged_output = self.run_git(["diff", "--name-only"])
        self.current_unstaged_files = []
        if unstaged_output:
            for f in unstaged_output.splitlines():
                self.current_unstaged_files.append((f.strip(), "Modified"))

        untracked_output = self.run_git(["ls-files", "--others", "--exclude-standard"])
        if untracked_output:
            for f in untracked_output.splitlines():
                self.current_unstaged_files.append((f.strip(), "Untracked"))

        if self.current_unstaged_files:
            self.btn_stage_toggle.setText("Stage All")
        elif self.current_staged_files:
            self.btn_stage_toggle.setText("Unstage All")
        else:
            self.btn_stage_toggle.setText("Stage All")

        row_count = 0
        if self.current_staged_files:
            row_count += 1 + len(self.current_staged_files)
        if self.current_unstaged_files:
            row_count += 1 + len(self.current_unstaged_files)

        self.changes_table.setRowCount(row_count)

        current_row = 0
        header_color = QColor(self.theme_tokens.get("muted-color"))

        # --- Staged Section ---
        if self.current_staged_files:
            header_item = QTableWidgetItem("Staged Changes")
            header_item.setFont(QFont("Arial", 10, QFont.Bold))
            header_item.setForeground(QBrush(header_color))
            header_item.setFlags(Qt.ItemIsEnabled)
            self.changes_table.setItem(current_row, 0, header_item)
            self.changes_table.setSpan(current_row, 0, 1, 2)
            current_row += 1

            for file_path, status_text in self.current_staged_files:
                item_file = QTableWidgetItem(file_path)
                item_file.setData(
                    Qt.UserRole, os.path.join(self.working_dir, file_path)
                )
                item_file.setData(Qt.UserRole + 1, file_path)
                item_file.setData(Qt.UserRole + 2, "staged")
                self.changes_table.setItem(current_row, 0, item_file)

                item_status = QTableWidgetItem(status_text)
                self.changes_table.setItem(current_row, 1, item_status)
                current_row += 1

        # --- Unstaged Section ---
        if self.current_unstaged_files:
            header_item = QTableWidgetItem("Unstaged Changes")
            header_item.setFont(QFont("Arial", 10, QFont.Bold))
            header_item.setForeground(QBrush(header_color))
            header_item.setFlags(Qt.ItemIsEnabled)
            self.changes_table.setItem(current_row, 0, header_item)
            self.changes_table.setSpan(current_row, 0, 1, 2)
            current_row += 1

            for file_path, status_text in self.current_unstaged_files:
                item_file = QTableWidgetItem(file_path)
                item_file.setData(
                    Qt.UserRole, os.path.join(self.working_dir, file_path)
                )
                item_file.setData(Qt.UserRole + 1, file_path)
                item_file.setData(Qt.UserRole + 2, "unstaged")
                self.changes_table.setItem(current_row, 0, item_file)

                item_status = QTableWidgetItem(status_text)
                self.changes_table.setItem(current_row, 1, item_status)
                current_row += 1

    def toggle_stage_all(self):
        if self.current_unstaged_files:
            self.run_git(["add", "-A"])
        else:
            self.run_git(["reset", "HEAD"])
        self.refresh()
        self.repo_changed.emit()

    def show_context_menu(self, pos):
        item = self.changes_table.itemAt(pos)
        if not item:
            return

        row = item.row()
        file_item = self.changes_table.item(row, 0)
        if not file_item:
            return

        section_type = file_item.data(Qt.UserRole + 2)
        if section_type is None:
            return

        file_path = file_item.data(Qt.UserRole + 1)
        full_path = file_item.data(Qt.UserRole)

        menu = QMenu(self)
        open_file_action = menu.addAction("Open File")
        menu.addSeparator()

        if section_type == "unstaged":
            stage_action = menu.addAction("Stage File")
            unstage_action = None
        elif section_type == "staged":
            stage_action = None
            unstage_action = menu.addAction("Unstage File")
        else:
            stage_action = None
            unstage_action = None

        action = menu.exec(self.changes_table.viewport().mapToGlobal(pos))

        if action is None:
            return

        if action == open_file_action:
            if full_path and os.path.isfile(full_path):
                self.file_selected.emit(full_path)
        elif action == stage_action:
            self.run_git(["add", file_path])
            self.refresh()
        elif action == unstage_action:
            self.run_git(["reset", "HEAD", file_path])
            self.refresh()

    def on_cell_double_clicked(self, row, column):
        file_item = self.changes_table.item(row, 0)
        if file_item and file_item.data(Qt.UserRole + 2) is not None:
            full_path = file_item.data(Qt.UserRole)
            if full_path:
                self.diff_requested.emit(full_path)

    def pull(self):
        self.run_git(["pull"])
        self.refresh()
        self.repo_changed.emit()

    def commit(self):
        msg = self.commit_input.toPlainText().strip()
        if not msg:
            return
        self.run_git(["commit", "-m", msg])
        self.commit_input.clear()
        self.refresh()
        self.repo_changed.emit()

    def push(self):
        branch = self.run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        if not branch:
            print("PUSH: could not determine current branch")
            return
        result = self.run_git(["push", "--set-upstream", "origin", branch])
        print(f"PUSH RESULT: {result!r}")
        self.refresh()
        self.repo_changed.emit()

    def undo_commit(self):
        self.run_git(["reset", "--soft", "HEAD~1"])
        self.refresh()
        self.repo_changed.emit()
