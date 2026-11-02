import os
import shutil
import subprocess
import sys
from sys import argv, exit

from PySide6.QtCore import QDir, Qt, QSettings
from PySide6.QtGui import (
    QAction,
    QKeySequence,
    QPixmap,
    QPainter,
    QColor,
    QIcon,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFileSystemModel,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from .components.find_replace import FindReplaceWidget
from .components.git_file_model import GitFileSystemModel
from .components.git_panel import GitPanel
from .components.highlighter_factory import get_highlighter
from .components.qss_file_handler import QssFileHandler
from .components.search_panel import SearchPanel
from .components.shortcuts_window import ShortcutsWindow
from .components.tab_manager import TabManager
from .components.terminal import TerminalWidget
from .components.yaml_file_handler import YamlFileHandler

style_file = QssFileHandler("../resources/styles/styles.qss")
style = style_file.load_qss_file()

themes_file = YamlFileHandler("../resources/styles/themes.yaml")
themes = themes_file.load_yaml_file()

RUN_COMMANDS = {
    ".py": [sys.executable],
    ".sh": ["bash"],
    ".js": ["node"],
}

# Calculate the project root dynamically (2 levels up from src/phaino/app.py)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class Phaino(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.settings = QSettings("Phaino", "Phaino")
        saved_theme = self.settings.value("theme", "phaino_dark")

        if saved_theme not in themes or saved_theme == "general":
            saved_theme = "phaino_dark"

        self.theme_name = saved_theme
        self.theme_tokens = {**themes[self.theme_name], **themes["general"]}
        self.drag_position = None

        self.init_ui()

    def create_window_dot(self, color_hex):
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(color_hex))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(6, 6, 12, 12)
        painter.end()
        return QIcon(pixmap)

    def find_git_root(self, start_path):
        current = os.path.abspath(start_path)
        while True:
            if os.path.isdir(os.path.join(current, ".git")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                return None
            current = parent

    def init_ui(self):
        self.show()
        self.setWindowTitle("Phaino")
        self.apply_theme(self.theme_name)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # * Setup Custom Title Bar
        self.title_bar = QWidget()
        self.title_bar.setObjectName("TitleBar")
        self.title_bar.setFixedHeight(30)

        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        title_layout.setSpacing(0)

        btn_file = QPushButton("File")
        btn_file.setObjectName("MenuButton")
        btn_edit = QPushButton("Edit")
        btn_edit.setObjectName("MenuButton")
        btn_git = QPushButton("Git")
        btn_git.setObjectName("MenuButton")
        btn_help = QPushButton("Help")
        btn_help.setObjectName("MenuButton")
        btn_settings = QPushButton("Settings")
        btn_settings.setObjectName("MenuButton")

        title_layout.addWidget(btn_file)
        title_layout.addWidget(btn_edit)
        title_layout.addWidget(btn_git)
        title_layout.addWidget(btn_help)
        title_layout.addWidget(btn_settings)
        title_layout.addStretch()

        # --- Window Controls ---
        btn_close = QPushButton()
        btn_close.setObjectName("WindowDot")
        btn_close.setIcon(
            self.create_window_dot(self.theme_tokens.get("danger-color", "#E63946"))
        )
        btn_close.setToolTip("Close")
        btn_close.setFixedSize(24, 24)
        btn_close.clicked.connect(self.close)

        btn_min = QPushButton()
        btn_min.setObjectName("WindowDot")
        btn_min.setIcon(
            self.create_window_dot(self.theme_tokens.get("warning-color", "#EBCB8B"))
        )
        btn_min.setToolTip("Minimize")
        btn_min.setFixedSize(24, 24)
        btn_min.clicked.connect(self.showMinimized)

        btn_max = QPushButton()
        btn_max.setObjectName("WindowDot")
        btn_max.setIcon(
            self.create_window_dot(self.theme_tokens.get("success-color", "#A3BE8C"))
        )
        btn_max.setToolTip("Maximize")
        btn_max.setFixedSize(24, 24)
        btn_max.clicked.connect(self.toggle_maximize)

        title_layout.addWidget(btn_close)
        title_layout.addWidget(btn_min)
        title_layout.addWidget(btn_max)

        self.main_layout.addWidget(self.title_bar)

        # * Setup Menus
        self.file_menu = QMenu(self)
        self.edit_menu = QMenu(self)
        self.git_menu = QMenu(self)
        self.help_menu = QMenu(self)
        self.theme_menu = QMenu(self)

        btn_file.setMenu(self.file_menu)
        btn_edit.setMenu(self.edit_menu)
        btn_git.setMenu(self.git_menu)
        btn_help.setMenu(self.help_menu)
        btn_settings.setMenu(self.theme_menu)

        # --- File Menu ---
        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(open_action)

        open_folder_action = QAction("Open &Folder...", self)
        open_folder_action.setShortcut("Ctrl+K")
        open_folder_action.triggered.connect(self.open_folder)
        self.file_menu.addAction(open_folder_action)

        new_tab_action = QAction("&New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(lambda: self.tabs.create_tab())
        self.file_menu.addAction(new_tab_action)

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.Save)
        save_action.triggered.connect(self.save_file)
        self.file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        self.file_menu.addAction(save_as_action)

        run_action = QAction("&Run File", self)
        run_action.setShortcut("Ctrl+R")
        run_action.triggered.connect(self.run_file_in_terminal)
        self.file_menu.addAction(run_action)

        # --- Edit Menu ---
        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        self.edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcuts([QKeySequence.Redo, QKeySequence("Ctrl+Y")])
        redo_action.triggered.connect(self.redo)
        self.edit_menu.addAction(redo_action)

        self.edit_menu.addSeparator()

        cut_action = QAction("Cu&t", self)
        cut_action.setShortcut(QKeySequence.Cut)
        cut_action.triggered.connect(self.cut)
        self.edit_menu.addAction(cut_action)

        copy_action = QAction("&Copy", self)
        copy_action.setShortcut(QKeySequence.Copy)
        copy_action.triggered.connect(self.copy)
        self.edit_menu.addAction(copy_action)

        paste_action = QAction("&Paste", self)
        paste_action.setShortcut(QKeySequence.Paste)
        paste_action.triggered.connect(self.paste)
        self.edit_menu.addAction(paste_action)

        self.edit_menu.addSeparator()

        find_action = QAction("&Find/Replace", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_widget)
        self.edit_menu.addAction(find_action)

        search_action = QAction("Search in &Files", self)
        search_action.setShortcut("Ctrl+Shift+F")
        search_action.triggered.connect(self.show_search_panel)
        self.edit_menu.addAction(search_action)

        # --- Git Menu ---
        commit_action = QAction("&Commit...", self)
        commit_action.triggered.connect(self.git_commit)
        self.git_menu.addAction(commit_action)

        # --- Help Menu ---
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self.show_shortcuts)
        self.help_menu.addAction(shortcuts_action)

        # --- Settings Menu ---
        self.theme_submenu = QMenu("Theme", self)
        self.theme_menu.addMenu(self.theme_submenu)

        for theme_key in themes:
            if theme_key == "general":
                continue
            display_name = theme_key.replace("_", " ").title()
            action = QAction(display_name, self)
            action.triggered.connect(lambda checked, t=theme_key: self.change_theme(t))
            self.theme_submenu.addAction(action)

        # * Create widgets
        self.file_model = GitFileSystemModel()
        self.file_model.setRootPath(PROJECT_ROOT)
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(PROJECT_ROOT))
        self.tree_view.setHeaderHidden(True)
        for i in range(1, 4):
            self.tree_view.setColumnHidden(i, True)
        self.tree_view.doubleClicked.connect(self.open_file_from_tree)

        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)

        self.path_input = QLineEdit()
        self.path_input.setText(PROJECT_ROOT)
        self.path_input.setPlaceholderText("Enter directory path...")
        self.path_input.returnPressed.connect(self.go_to_directory)
        self.path_input.setObjectName("PathInput")

        # * Setup Status Bar
        self.status_bar = self.statusBar()
        self.lbl_git = QLabel("")
        self.lbl_git.setObjectName("GitLabel")
        self.lbl_git.hide()
        self.lbl_position = QLabel("Ln 1, Col 1")
        self.lbl_language = QLabel("Plain Text")

        self.status_bar.addPermanentWidget(self.lbl_git)
        self.status_bar.addPermanentWidget(self.lbl_position)
        self.status_bar.addPermanentWidget(self.lbl_language)

        # * Setup TabManager
        self.tabs = TabManager(self.theme_tokens, self)
        self.tabs.current_tab_changed.connect(self.update_window_title)
        self.tabs.current_tab_changed.connect(self.on_tab_changed)
        self.tabs.tab_close_requested_with_unsaved_changes.connect(
            self.handle_unsaved_tab_close
        )
        self.tabs.cursor_position_changed.connect(self.update_cursor_position)

        # * Create Terminal
        self.terminal = TerminalWidget(self.theme_tokens, self)

        # * Create Find/Replace Widget
        self.find_widget = FindReplaceWidget(None)
        self.find_widget.closed.connect(self.hide_find_widget)

        # * Create Search Panel
        self.search_panel = SearchPanel()
        self.search_panel.result_clicked.connect(self.jump_to_search_result)
        self.search_panel.closed.connect(self.hide_search_panel)

        # * Create Git Panel
        self.git_panel = GitPanel()
        self.git_panel.file_selected.connect(self.load_file)

        # Initialize the Git panel with the project root immediately
        self.git_panel.set_working_dir(PROJECT_ROOT)

        # Now create the first tab
        self.tabs.create_tab()

        # * Create layouts
        explorer_tab = QWidget()
        explorer_layout = QVBoxLayout(explorer_tab)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        explorer_layout.setSpacing(0)
        explorer_layout.addWidget(self.path_input)
        explorer_layout.addWidget(self.tree_view)

        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setDocumentMode(True)
        self.sidebar_tabs.addTab(explorer_tab, "Explorer")
        self.sidebar_tabs.addTab(self.git_panel, "Source Control")

        self.editor_splitter = QSplitter(Qt.Vertical)
        self.editor_splitter.addWidget(self.find_widget)
        self.editor_splitter.addWidget(self.search_panel)
        self.editor_splitter.addWidget(self.tabs)
        self.editor_splitter.addWidget(self.terminal)

        self.editor_splitter.setSizes([0, 0, 600, 200])
        self.editor_splitter.setCollapsible(0, False)
        self.editor_splitter.setCollapsible(1, False)

        self.editor_container = QWidget()
        self.editor_container.setObjectName("EditorContainer")
        editor_layout = QVBoxLayout(self.editor_container)
        editor_layout.setContentsMargins(0, 0, 0, 0)
        editor_layout.setSpacing(0)
        editor_layout.addWidget(self.editor_splitter)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(self.sidebar_tabs)
        main_splitter.addWidget(self.editor_container)
        main_splitter.setSizes([250, 750])

        page = QGridLayout()
        page.addWidget(main_splitter, 0, 0)

        gui = QWidget()
        gui.setObjectName("MainWindowContent")
        gui.setLayout(page)

        self.main_layout.addWidget(gui)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        self.update_window_title()
        self.update_cursor_position(self.tabs.current_editor())

    def on_tab_changed(self):
        editor = self.tabs.current_editor()
        if editor:
            if hasattr(self, "find_widget") and self.find_widget:
                self.find_widget.set_editor(editor)
            self.update_cursor_position(editor)
            self.update_git_status()

            file_path = getattr(editor, "file_path", None)
            if file_path:
                git_root = self.find_git_root(os.path.dirname(file_path))
                if git_root:
                    self.git_panel.set_working_dir(git_root)

            # Safely disconnect previous connections
            try:
                editor.escape_pressed.disconnect()
            except TypeError:
                pass
            editor.escape_pressed.connect(self.hide_find_widget)
            editor.escape_pressed.connect(self.hide_search_panel)

    def update_cursor_position(self, editor):
        if not editor or not hasattr(self, "lbl_position"):
            return
        cursor = editor.textCursor()
        line = cursor.blockNumber() + 1
        col = cursor.columnNumber() + 1
        self.lbl_position.setText(f"Ln {line}, Col {col}")

        file_path = getattr(editor, "file_path", None)
        if file_path:
            _, ext = os.path.splitext(file_path)
            lang = ext.replace(".", "").upper() if ext else "TEXT"
        else:
            lang = "TEXT"
        self.lbl_language.setText(lang)

    def update_git_status(self):
        editor = self.tabs.current_editor()
        if not editor:
            self.lbl_git.hide()
            return

        file_path = getattr(editor, "file_path", None)
        if not file_path:
            self.lbl_git.hide()
            self.file_model.set_git_changes(set())
            return

        git_root = self.find_git_root(os.path.dirname(file_path))
        if not git_root:
            self.lbl_git.hide()
            self.file_model.set_git_changes(set())
            return

        try:
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=git_root,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()

            if branch:
                self.lbl_git.setText(f"⎇ {branch}")
                self.lbl_git.show()
            else:
                self.lbl_git.hide()
        except subprocess.CalledProcessError:
            self.lbl_git.hide()

        try:
            status_output = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=git_root,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            changed_files = set()
            for line in status_output.splitlines():
                if len(line) > 3:
                    rel_path = line[3:].strip()
                    full_path = os.path.join(git_root, rel_path)
                    changed_files.add(full_path)
            self.file_model.set_git_changes(changed_files)
        except subprocess.CalledProcessError:
            pass

    def show_find_widget(self):
        self.search_panel.hide()
        self.find_widget.show()
        self.editor_splitter.setSizes([40, 0, 560, 200])
        self.find_widget.find_input.setFocus()
        self.find_widget.find_input.selectAll()

    def hide_find_widget(self):
        self.editor_splitter.setSizes([0, 0, 600, 200])
        self.find_widget.hide()

    def show_search_panel(self):
        self.find_widget.hide()
        self.search_panel.set_root(self.file_model.rootPath())
        self.search_panel.show()
        self.editor_splitter.setSizes([0, 200, 400, 200])
        self.search_panel.search_input.setFocus()

    def hide_search_panel(self):
        self.editor_splitter.setSizes([0, 0, 600, 200])
        self.search_panel.hide()

    def jump_to_search_result(self, file_path, line_num):
        self.load_file(file_path)
        editor = self.tabs.current_editor()
        if editor:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_num - 1)
            editor.setTextCursor(cursor)
            editor.centerCursor()

    def apply_theme(self, theme_name):
        self.theme_name = theme_name if theme_name in themes else "dark"
        self.theme_tokens = {**themes[self.theme_name], **themes["general"]}

        stylesheet = style
        for key, value in self.theme_tokens.items():
            stylesheet = stylesheet.replace("{{" + key + "}}", str(value))

        self.setStyleSheet(stylesheet)

        if hasattr(self, "tabs"):
            self.tabs.update_theme(self.theme_tokens)

        if hasattr(self, "terminal"):
            self.terminal.theme_tokens = self.theme_tokens
            self.terminal.apply_palette()

    def change_theme(self, theme_name):
        self.apply_theme(theme_name)
        self.settings.setValue("theme", theme_name)

        if hasattr(self, "tabs"):
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                file_path = getattr(editor, "file_path", None)

                new_highlighter = get_highlighter(
                    file_path, editor.document(), self.theme_tokens
                )

                if hasattr(editor, "highlighter") and editor.highlighter is not None:
                    editor.highlighter.setDocument(None)
                    del editor.highlighter

                if new_highlighter is not None:
                    editor.highlighter = new_highlighter
                    editor.highlighter.rehighlight()

    def show_shortcuts(self):
        dialog = ShortcutsWindow(self.theme_tokens, self)
        dialog.exec()

    def git_commit(self):
        self.sidebar_tabs.setCurrentWidget(self.git_panel)

    # ==========================================
    # EXECUTION
    # ==========================================

    def run_file_in_terminal(self):
        editor = self.tabs.current_editor()
        if not editor:
            return

        file_path = getattr(editor, "file_path", None)
        if not file_path:
            if not self.save_file_as():
                return
            file_path = editor.file_path

        self.save_file()

        working_dir = os.path.dirname(file_path)
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        command_prefix = RUN_COMMANDS.get(ext)

        if command_prefix:
            command = command_prefix + [file_path]
        else:
            command = [file_path]

        self.terminal.run_command(command, working_directory=working_dir)

    # ==========================================
    # EDIT ACTIONS
    # ==========================================

    def undo(self):
        editor = self.tabs.current_editor()
        if editor:
            editor.undo()

    def redo(self):
        editor = self.tabs.current_editor()
        if editor:
            editor.redo()

    def cut(self):
        editor = self.tabs.current_editor()
        if editor:
            editor.cut()

    def copy(self):
        editor = self.tabs.current_editor()
        if editor:
            editor.copy()

    def paste(self):
        editor = self.tabs.current_editor()
        if editor:
            editor.paste()

    # ==========================================
    # FILE EXPLORER CONTEXT MENU ACTIONS
    # ==========================================

    def show_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        menu = QMenu(self)

        if index.isValid():
            action_new_file = menu.addAction("New File")
            action_new_folder = menu.addAction("New Folder")
            menu.addSeparator()
            action_rename = menu.addAction("Rename")
            action_delete = menu.addAction("Delete")
        else:
            action_new_file = menu.addAction("New File")
            action_new_folder = menu.addAction("New Folder")
            action_rename = None
            action_delete = None

        action = menu.exec(self.tree_view.viewport().mapToGlobal(pos))

        if action is None:
            return

        if action == action_new_file:
            self.create_file(pos)
        elif action == action_new_folder:
            self.create_folder(pos)
        elif action == action_rename:
            self.rename_item()
        elif action == action_delete:
            self.delete_item()

    def create_file(self, pos):
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            base_path = self.file_model.rootPath()
        else:
            base_path = self.file_model.filePath(index)
            if not os.path.isdir(base_path):
                base_path = os.path.dirname(base_path)

        name, ok = QInputDialog.getText(self, "New File", "Enter file name:")
        if ok and name:
            new_path = os.path.join(base_path, name)
            try:
                with open(new_path, "w") as f:
                    pass
                self.refresh_tree()
            except Exception as e:
                print(f"Error creating file: {e}")

    def create_folder(self, pos):
        index = self.tree_view.indexAt(pos)
        if not index.isValid():
            base_path = self.file_model.rootPath()
        else:
            base_path = self.file_model.filePath(index)
            if not os.path.isdir(base_path):
                base_path = os.path.dirname(base_path)

        name, ok = QInputDialog.getText(self, "New Folder", "Enter folder name:")
        if ok and name:
            new_path = os.path.join(base_path, name)
            try:
                os.makedirs(new_path, exist_ok=True)
                self.refresh_tree()
            except Exception as e:
                print(f"Error creating folder: {e}")

    def rename_item(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            return
        old_path = self.file_model.filePath(index)
        if not old_path:
            return

        old_name = os.path.basename(old_path)
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter new name:", text=old_name
        )

        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
                self.refresh_tree()
            except Exception as e:
                print(f"Error renaming item: {e}")

    def delete_item(self):
        index = self.tree_view.currentIndex()
        if not index.isValid():
            return
        path = self.file_model.filePath(index)
        if not path:
            return

        reply = QMessageBox.question(
            self,
            "Delete",
            f"Are you sure you want to delete {os.path.basename(path)}?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                self.refresh_tree()
            except Exception as e:
                print(f"Error deleting item: {e}")

    def refresh_tree(self):
        self.file_model.setRootPath("")
        self.file_model.setRootPath(self.file_model.rootPath())
        self.update_git_status()

    # ==========================================
    # FILE & FOLDER OPERATIONS
    # ==========================================

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            self.set_tree_root(folder_path)

    def go_to_directory(self):
        new_path = self.path_input.text().strip()
        new_path = os.path.expanduser(new_path)

        if os.path.isdir(new_path):
            self.set_tree_root(new_path)
        else:
            self.path_input.setText(self.file_model.rootPath())

    def set_tree_root(self, path):
        self.file_model.setRootPath(path)
        self.tree_view.setRootIndex(self.file_model.index(path))
        self.path_input.setText(path)

    def open_file_from_tree(self, index):
        file_path = self.file_model.filePath(index)
        if os.path.isfile(file_path):
            self.load_file(file_path)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open File",
            "",
            "All Files (*);;Python Files (*.py);;Text Files (*.txt)",
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if getattr(editor, "file_path", None) == file_path:
                self.tabs.setCurrentIndex(i)
                return

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()

            current_editor = self.tabs.current_editor()
            current_index = self.tabs.currentIndex()

            is_blank_untitled = (
                current_editor is not None
                and getattr(current_editor, "file_path", None) is None
                and current_editor.toPlainText() == ""
            )

            if is_blank_untitled:
                editor = current_editor
                self.tabs.setTabText(current_index, os.path.basename(file_path))
            else:
                editor = self.tabs.create_tab(os.path.basename(file_path))

            editor.file_path = file_path

            if hasattr(editor, "highlighter") and editor.highlighter is not None:
                editor.highlighter.setDocument(None)

            new_highlighter = get_highlighter(
                file_path, editor.document(), self.theme_tokens
            )
            if new_highlighter is not None:
                editor.highlighter = new_highlighter
                editor.highlighter.rehighlight()

            editor.insertPlainText(content)
            editor.document().setModified(False)
            editor.document().clearUndoRedoStacks()
            self.update_window_title()

        except Exception as e:
            print(f"Error opening file: {e}")

    def save_file(self) -> bool:
        editor = self.tabs.current_editor()
        if not editor:
            return False

        file_path = getattr(editor, "file_path", None)
        if not file_path:
            return self.save_file_as()

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(editor.toPlainText())

            editor.document().setModified(False)
            self.update_window_title()
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def save_file_as(self) -> bool:
        editor = self.tabs.current_editor()
        if not editor:
            return False

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save File As", "", "Python Files (*.py);;All Files (*)"
        )
        if file_path:
            editor.file_path = file_path
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(file_path))

            if hasattr(editor, "highlighter") and editor.highlighter is not None:
                editor.highlighter.setDocument(None)

            new_highlighter = get_highlighter(
                file_path, editor.document(), self.theme_tokens
            )
            if new_highlighter is not None:
                editor.highlighter = new_highlighter
                editor.highlighter.rehighlight()

            return self.save_file()

        return False

    def handle_unsaved_tab_close(self, index):
        editor = self.tabs.widget(index)
        file_path = getattr(editor, "file_path", None)
        filename = os.path.basename(file_path) if file_path else "Untitled"

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Unsaved Changes")
        msg_box.setText(f"Do you want to save changes to {filename}?")
        msg_box.setStandardButtons(
            QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.Save)

        reply = msg_box.exec()

        if reply == QMessageBox.Save:
            self.tabs.setCurrentIndex(index)
            success = self.save_file()
            if success:
                self.tabs._force_close_tab(index)
        elif reply == QMessageBox.Discard:
            self.tabs._force_close_tab(index)
        elif reply == QMessageBox.Cancel:
            pass

    def update_window_title(self):
        editor = self.tabs.current_editor()
        if not editor:
            self.setWindowTitle("Phaino")
            return

        file_path = getattr(editor, "file_path", None)
        filename = os.path.basename(file_path) if file_path else "Untitled"
        modified = "*" if editor.document().isModified() else ""
        self.setWindowTitle(f"{filename}{modified} - Phaino")

    # ==========================================
    # WINDOW DRAGGING & CONTROL
    # ==========================================

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            )
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()


def main():
    app = QApplication(argv)
    main_window = Phaino()  # noqa: F841
    exit(app.exec())


if __name__ == "__main__":
    main()
