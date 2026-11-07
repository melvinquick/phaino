import os
import shutil
import subprocess
from sys import argv, exit

from PySide6.QtCore import QDir, QRegularExpression, QSettings, Qt
from PySide6.QtGui import (
    QAction,
    QColor,
    QIcon,
    QKeySequence,
    QPainter,
    QPixmap,
    QSyntaxHighlighter,
    QTextCharFormat,
    QTextCursor,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
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

from .components.command_palette import CommandPalette
from .components.find_replace import FindReplaceWidget
from .components.formatter_factory import format_code
from .components.git_file_model import GitFileSystemModel
from .components.git_panel import GitPanel
from .components.highlighter_factory import get_highlighter
from .components.preferences_dialog import PreferencesDialog
from .components.projects_panel import ProjectsPanel
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


class DiffHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme_tokens):
        super().__init__(document)
        self.highlighting_rules = []

        string_color = theme_tokens.get("success-color")
        danger_color = theme_tokens.get("danger-color")
        function_color = theme_tokens.get("function-color")

        add_format = QTextCharFormat()
        add_format.setForeground(QColor(string_color))
        self.highlighting_rules.append((QRegularExpression(r"^\+.*$"), add_format))

        del_format = QTextCharFormat()
        del_format.setForeground(QColor(danger_color))
        self.highlighting_rules.append((QRegularExpression(r"^-.*$"), del_format))

        header_format = QTextCharFormat()
        header_format.setForeground(QColor(function_color))
        header_format.setFontWeight(700)
        self.highlighting_rules.append((QRegularExpression(r"^@@.*$"), header_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)


class Phaino(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)

        self.settings = QSettings("Phaino", "Phaino")
        saved_theme = self.settings.value("theme", "phaino_dark", type=str)
        if saved_theme not in themes or saved_theme == "general":
            saved_theme = "phaino_dark"

        self.theme_name = saved_theme
        self.theme_tokens = {**themes[self.theme_name], **themes["general"]}

        self.format_on_save = self.settings.value("format_on_save", True, type=bool)
        disabled = self.settings.value("format_disabled_languages", [], type=list)
        self.format_disabled_languages = set(disabled)

        saved_root = self.settings.value("current_root", "", type=str)
        if saved_root and os.path.isdir(saved_root):
            self.current_root = saved_root
        else:
            self.current_root = os.getcwd()

        self.drag_position = None

        self.init_ui()

    # ==========================================
    # INITIALIZATION
    # ==========================================

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
        btn_help = QPushButton("Help")
        btn_help.setObjectName("MenuButton")
        btn_settings = QPushButton("Preferences")
        btn_settings.setObjectName("MenuButton")

        title_layout.addWidget(btn_file)
        title_layout.addWidget(btn_edit)
        title_layout.addWidget(btn_help)
        title_layout.addWidget(btn_settings)
        title_layout.addStretch()

        self.btn_close = QPushButton()
        self.btn_close.setObjectName("WindowDot")
        self.btn_close.setIcon(
            self.create_window_dot(self.theme_tokens.get("danger-color"))
        )
        self.btn_close.setToolTip("Close")
        self.btn_close.setFixedSize(24, 24)
        self.btn_close.clicked.connect(self.close)

        self.btn_min = QPushButton()
        self.btn_min.setObjectName("WindowDot")
        self.btn_min.setIcon(
            self.create_window_dot(self.theme_tokens.get("warning-color"))
        )
        self.btn_min.setToolTip("Minimize")
        self.btn_min.setFixedSize(24, 24)
        self.btn_min.clicked.connect(self.showMinimized)

        self.btn_max = QPushButton()
        self.btn_max.setObjectName("WindowDot")
        self.btn_max.setIcon(
            self.create_window_dot(self.theme_tokens.get("success-color"))
        )
        self.btn_max.setToolTip("Maximize")
        self.btn_max.setFixedSize(24, 24)
        self.btn_max.clicked.connect(self.toggle_maximize)

        title_layout.addWidget(self.btn_close)
        title_layout.addWidget(self.btn_min)
        title_layout.addWidget(self.btn_max)

        self.main_layout.addWidget(self.title_bar)

        self._zen_mode = False
        self._saved_main_splitter_sizes = None
        self._saved_editor_splitter_sizes = None

        # * Setup Menus
        self.file_menu = QMenu(self)
        self.edit_menu = QMenu(self)
        self.help_menu = QMenu(self)
        self.theme_menu = QMenu(self)

        btn_file.setMenu(self.file_menu)
        btn_edit.setMenu(self.edit_menu)
        btn_help.setMenu(self.help_menu)
        btn_settings.clicked.connect(self.show_preferences)

        open_action = QAction("&Open", self)
        open_action.setShortcut(QKeySequence.Open)
        open_action.triggered.connect(self.open_file)
        self.file_menu.addAction(open_action)

        open_folder_action = QAction("Open &Folder...", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
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

        self.recent_submenu = QMenu("Recent", self)
        self.file_menu.addMenu(self.recent_submenu)
        self._refresh_recent_menu()

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.Undo)
        undo_action.triggered.connect(self.undo)
        self.edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcuts([QKeySequence.Redo, QKeySequence("Ctrl+Y")])
        redo_action.triggered.connect(self.redo)
        self.edit_menu.addAction(redo_action)

        wrap_action = QAction("Toggle Line &Wrap", self)
        wrap_action.setShortcut("Alt+Z")
        wrap_action.triggered.connect(self.toggle_line_wrap)
        self.edit_menu.addAction(wrap_action)

        zen_action = QAction("Toggle &Zen Mode", self)
        zen_action.setShortcut("Ctrl+K")
        zen_action.triggered.connect(self.toggle_zen_mode)
        self.edit_menu.addAction(zen_action)

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

        comment_action = QAction("Toggle &Comment", self)
        comment_action.setShortcut("Ctrl+/")
        comment_action.triggered.connect(self._toggle_comment)
        self.edit_menu.addAction(comment_action)

        self.edit_menu.addSeparator()

        find_action = QAction("&Find/Replace", self)
        find_action.setShortcut(QKeySequence.Find)
        find_action.triggered.connect(self.show_find_widget)
        self.edit_menu.addAction(find_action)

        search_action = QAction("Search in &Files", self)
        search_action.setShortcut("Ctrl+Shift+F")
        search_action.triggered.connect(self.show_search_panel)
        self.edit_menu.addAction(search_action)

        goto_action = QAction("&Go to Line...", self)
        goto_action.setShortcut("Ctrl+G")
        goto_action.triggered.connect(self.go_to_line)
        self.edit_menu.addAction(goto_action)

        palette_action = QAction("Command Palette", self)
        palette_action.setShortcut("Ctrl+Shift+P")
        palette_action.triggered.connect(self.show_command_palette)
        self.edit_menu.addAction(palette_action)

        prefs_action = QAction("Preferences", self)
        prefs_action.setShortcut("Ctrl+,")
        prefs_action.triggered.connect(self.show_preferences)
        self.edit_menu.addAction(prefs_action)

        line_numbers_action = QAction("Toggle Line &Numbers", self)
        line_numbers_action.setShortcut("Ctrl+Shift+L")
        line_numbers_action.triggered.connect(self.toggle_line_numbers)
        self.edit_menu.addAction(line_numbers_action)

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcuts(
            [
                QKeySequence("Ctrl+="),
                QKeySequence("Ctrl++"),
                QKeySequence("Ctrl+Shift+="),
            ]
        )
        zoom_in_action.triggered.connect(self.zoom_in)
        self.edit_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        self.edit_menu.addAction(zoom_out_action)

        zoom_reset_action = QAction("&Reset Zoom", self)
        zoom_reset_action.setShortcut("Ctrl+0")
        zoom_reset_action.triggered.connect(self.reset_zoom)
        self.edit_menu.addAction(zoom_reset_action)

        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.triggered.connect(self.show_shortcuts)
        self.help_menu.addAction(shortcuts_action)

        # * Create Widgets
        self.file_model = GitFileSystemModel(self.theme_tokens)
        self.file_model.setRootPath(self.current_root)
        self.file_model.setFilter(QDir.NoDotAndDotDot | QDir.AllEntries)

        self.tree_view = QTreeView()
        self.tree_view.setModel(self.file_model)
        self.tree_view.setRootIndex(self.file_model.index(self.current_root))
        self.tree_view.setHeaderHidden(True)
        for i in range(1, 4):
            self.tree_view.setColumnHidden(i, True)
        self.tree_view.doubleClicked.connect(self.open_file_from_tree)
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.show_context_menu)
        self.tree_view.installEventFilter(self)

        self.path_input = QLineEdit()
        self.path_input.setText(self.current_root)
        self.path_input.setPlaceholderText("Enter directory path...")
        self.path_input.returnPressed.connect(self.go_to_directory)
        self.path_input.setObjectName("PathInput")

        # * Setup Status Bar with Breadcrumbs
        self.status_bar = self.statusBar()
        self.status_bar.setSizeGripEnabled(False)

        self.breadcrumb_container = QWidget()
        self.breadcrumb_container.setObjectName("BreadcrumbContainer")
        self.breadcrumb_layout = QHBoxLayout(self.breadcrumb_container)
        self.breadcrumb_layout.setContentsMargins(8, 0, 8, 0)
        self.breadcrumb_layout.setSpacing(0)
        self.breadcrumb_layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.lbl_git = QLabel("")
        self.lbl_git.setObjectName("GitLabel")
        self.lbl_git.hide()
        self.lbl_position = QLabel("Ln 1, Col 1")
        self.lbl_language = QLabel("Plain Text")

        self.status_bar.addPermanentWidget(self.breadcrumb_container, 1)
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

        self.terminal = TerminalWidget(self.theme_tokens, self)

        self.find_widget = FindReplaceWidget(None)
        self.find_widget.closed.connect(self.hide_find_widget)

        self.search_panel = SearchPanel()
        self.search_panel.result_clicked.connect(self.jump_to_search_result)
        self.search_panel.replace_requested.connect(self.replace_in_files)
        self.search_panel.closed.connect(self.hide_search_panel)

        self.git_panel = GitPanel(self.theme_tokens)
        self.git_panel.file_selected.connect(self.load_file)
        self.git_panel.diff_requested.connect(self.show_diff)
        self.git_panel.repo_changed.connect(self.update_git_status)
        self.git_panel.set_working_dir(self.current_root)

        self.projects_panel = ProjectsPanel(self.settings, self.theme_tokens)
        self.projects_panel.project_opened.connect(self._open_project)
        self.projects_panel.add_current_requested.connect(
            self._add_current_root_as_project
        )

        self.tabs.create_tab()

        # * Create Layouts
        explorer_tab = QWidget()
        explorer_layout = QVBoxLayout(explorer_tab)
        explorer_layout.setContentsMargins(0, 0, 0, 0)
        explorer_layout.setSpacing(0)
        explorer_layout.addWidget(self.path_input)
        explorer_layout.addWidget(self.tree_view)

        self.sidebar_tabs = QTabWidget()
        self.sidebar_tabs.setObjectName("SidebarTabs")
        self.sidebar_tabs.setDocumentMode(True)
        self.sidebar_tabs.tabBar().setDrawBase(False)
        self.sidebar_tabs.addTab(explorer_tab, "Explorer")
        self.sidebar_tabs.addTab(self.git_panel, "Source Control")
        self.sidebar_tabs.addTab(self.projects_panel, "Projects")
        self.sidebar_tabs.setMinimumWidth(self.sidebar_tabs.tabBar().sizeHint().width())

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

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.addWidget(self.sidebar_tabs)
        self.main_splitter.addWidget(self.editor_container)
        self.main_splitter.setSizes([250, 750])
        self.main_splitter.setCollapsible(0, False)

        page = QGridLayout()
        page.addWidget(self.main_splitter, 0, 0)

        gui = QWidget()
        gui.setObjectName("MainWindowContent")
        gui.setLayout(page)

        self.main_layout.addWidget(gui)

        central_widget = QWidget()
        central_widget.setLayout(self.main_layout)
        self.setCentralWidget(central_widget)

        self.update_window_title()
        self.update_cursor_position(self.tabs.current_editor())
        self.update_git_status()
        self._apply_editor_preferences()

    # ==========================================
    # THEME & STATE MANAGEMENT
    # ==========================================

    def apply_theme(self, theme_name):
        self.theme_name = theme_name if theme_name in themes else "dark"
        self.theme_tokens = {**themes[self.theme_name], **themes["general"]}

        base = self.settings.value("font_size", 15, type=int)
        self.theme_tokens["font-size"] = f"{base}px"
        self.theme_tokens["font-size-lg"] = f"{max(8, round(base * 16 / 15))}px"
        self.theme_tokens["font-size-md"] = f"{max(8, round(base * 13 / 15))}px"
        self.theme_tokens["font-size-sm"] = f"{max(8, round(base * 12 / 15))}px"
        self.theme_tokens["font-size-xs"] = f"{max(8, round(base * 11 / 15))}px"

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

        self._refresh_window_dots()

        if hasattr(self, "file_model"):
            self.file_model.update_theme(self.theme_tokens)

        if hasattr(self, "tabs"):
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                file_path = getattr(editor, "file_path", None)

                if self.tabs.tabText(i).endswith("(diff)"):
                    self.apply_diff_highlighting(editor)
                    continue

                new_highlighter = get_highlighter(
                    file_path, editor.document(), self.theme_tokens
                )

                if hasattr(editor, "highlighter") and editor.highlighter is not None:
                    editor.highlighter.setDocument(None)
                    del editor.highlighter

                if new_highlighter is not None:
                    editor.highlighter = new_highlighter
                    editor.highlighter.rehighlight()

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

    def _refresh_window_dots(self):
        self.btn_close.setIcon(
            self.create_window_dot(self.theme_tokens.get("danger-color"))
        )
        self.btn_min.setIcon(
            self.create_window_dot(self.theme_tokens.get("warning-color"))
        )
        self.btn_max.setIcon(
            self.create_window_dot(self.theme_tokens.get("success-color"))
        )

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

            try:
                editor.escape_pressed.disconnect()
            except TypeError:
                pass
            editor.escape_pressed.connect(self.hide_find_widget)
            editor.escape_pressed.connect(self.hide_search_panel)

            try:
                editor.format_requested.disconnect()
            except TypeError:
                pass
            editor.format_requested.connect(self._on_format_requested)

            if file_path and not self.tabs.tabText(self.tabs.currentIndex()).endswith(
                "(diff)"
            ):
                self._update_breadcrumbs(file_path)
            else:
                self._update_breadcrumbs(None)

    def update_window_title(self):
        editor = self.tabs.current_editor()
        if not editor:
            self.setWindowTitle("Phaino")
            return

        file_path = getattr(editor, "file_path", None)
        filename = os.path.basename(file_path) if file_path else "Untitled"
        modified = "*" if editor.document().isModified() else ""
        self.setWindowTitle(f"{filename}{modified} - Phaino")

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

    # ==========================================
    # BREADCRUMBS
    # ==========================================

    def _update_breadcrumbs(self, file_path):
        while self.breadcrumb_layout.count():
            item = self.breadcrumb_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not file_path or not self.current_root:
            return

        try:
            rel_path = os.path.relpath(file_path, self.current_root)
        except ValueError:
            return

        if rel_path.startswith(".."):
            return

        parts = rel_path.split(os.sep)
        num_parts = len(parts)

        for i, part in enumerate(parts):
            is_last = i == num_parts - 1
            dir_path = os.path.join(self.current_root, *parts[: i + 1])
            target_path = file_path if is_last else dir_path

            btn = QPushButton(part)
            btn.setObjectName("BreadcrumbFile" if is_last else "BreadcrumbSegment")
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked, p=target_path: self._highlight_in_explorer(p)
            )
            self.breadcrumb_layout.addWidget(btn)

            if not is_last:
                sep = QLabel("›")
                sep.setObjectName("BreadcrumbSeparator")
                self.breadcrumb_layout.addWidget(sep)

    def _highlight_in_explorer(self, path):
        self.sidebar_tabs.setCurrentWidget(self.sidebar_tabs.widget(0))
        index = self.file_model.index(path)
        if not index.isValid():
            return
        self.tree_view.setCurrentIndex(index)
        self.tree_view.scrollTo(index)
        self.tree_view.setFocus()

    # ==========================================
    # WIDGET VISIBILITY
    # ==========================================

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

    def replace_in_files(self, query, replacement, file_paths):
        modified_count = 0
        skipped_files = []

        for file_path in file_paths:
            open_editor = None
            for i in range(self.tabs.count()):
                editor = self.tabs.widget(i)
                if getattr(editor, "file_path", None) == file_path:
                    open_editor = editor
                    break

            if open_editor is not None:
                if open_editor.document().isModified():
                    skipped_files.append(file_path)
                    continue
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = content.replace(query, replacement)
                if new_content != content:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    modified_count += 1
            except Exception as e:
                print(f"Error replacing in {file_path}: {e}")

        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            file_path = getattr(editor, "file_path", None)
            if file_path in file_paths and editor.document().isModified() is False:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    cursor_pos = editor.textCursor().position()
                    editor.blockSignals(True)
                    editor.setPlainText(content)
                    editor.blockSignals(False)
                    new_cursor = editor.textCursor()
                    new_cursor.setPosition(min(cursor_pos, len(content)))
                    editor.setTextCursor(new_cursor)
                    if (
                        hasattr(editor, "highlighter")
                        and editor.highlighter is not None
                    ):
                        editor.highlighter.rehighlight()
                except Exception as e:
                    print(f"Error reloading {file_path}: {e}")

        self.update_git_status()
        if hasattr(self, "git_panel"):
            self.git_panel.refresh()

        if modified_count == 0 and skipped_files:
            self.terminal.append(
                "\n[Replace] No files were modified. All matched files are open "
                "with unsaved changes and were skipped to protect your work.\n"
                "Save or close the affected tabs and try again.\n"
            )
            for path in skipped_files:
                self.terminal.append(f"  Skipped: {os.path.basename(path)}\n")
            return

        if modified_count > 0:
            self.terminal.append(
                f"\n[Replace] Replaced '{query}' in {modified_count} file(s).\n"
            )

        if skipped_files:
            self.terminal.append(
                f"[Replace] Skipped {len(skipped_files)} file(s) with unsaved changes:\n"
            )
            for path in skipped_files:
                self.terminal.append(f"  Skipped: {os.path.basename(path)}\n")

    def go_to_line(self):
        editor = self.tabs.current_editor()
        if not editor:
            return

        max_line = editor.blockCount()
        current_line = editor.textCursor().blockNumber() + 1

        line_num, ok = QInputDialog.getInt(
            self,
            "Go to Line",
            f"Line number (1-{max_line}):",
            current_line,
            1,
            max_line,
            1,
        )
        if ok:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line_num - 1)
            editor.setTextCursor(cursor)
            editor.centerCursor()
            editor.setFocus()

    # ==========================================
    # COMMAND PALETTE & PREFERENCES
    # ==========================================

    def show_command_palette(self):
        self._palette_clipboard_text = QApplication.clipboard().text()
        if not hasattr(self, "command_palette"):
            self.command_palette = CommandPalette(
                self._command_palette_focus_target, self
            )
            self.command_palette.paste_requested.connect(self._paste_from_palette)
        actions = []
        for menu in (self.file_menu, self.edit_menu, self.help_menu):
            actions.extend(menu.actions())
        self.command_palette.populate(actions)
        self.command_palette.show()
        self.command_palette.raise_()
        self.command_palette.activateWindow()

    def _command_palette_focus_target(self):
        return self.tabs.current_editor()

    def _paste_from_palette(self):
        editor = self.tabs.current_editor()
        if editor:
            editor.setFocus()
            editor.insertPlainText(self._palette_clipboard_text)

    def show_preferences(self):
        dialog = PreferencesDialog(self.settings, themes, self)
        dialog.settings_changed.connect(self._apply_preferences)
        dialog.exec()

    def _apply_preferences(self):
        new_theme = self.settings.value("theme", "phaino_dark", type=str)
        if new_theme != self.theme_name:
            self.change_theme(new_theme)

        self.format_on_save = self.settings.value("format_on_save", True, type=bool)
        disabled = self.settings.value("format_disabled_languages", [], type=list)
        self.format_disabled_languages = set(disabled)

        self._apply_editor_preferences()

    def _apply_editor_preferences(self):
        self.apply_theme(self.theme_name)

        font_family = self.settings.value("font_family", "Fira Code", type=str)
        font_size = self.settings.value("font_size", 15, type=int)
        show_numbers = self.settings.value("show_line_numbers", True, type=bool)
        wrap = self.settings.value("line_wrap", False, type=bool)
        show_trailing_ws = self.settings.value(
            "show_trailing_whitespace", False, type=bool
        )

        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            if hasattr(editor, "update_editor_preferences"):
                editor.update_editor_preferences(
                    font_family, font_size, show_numbers, wrap, show_trailing_ws
                )

    # ==========================================
    # FORMATTING
    # ==========================================

    def _format_editor(self, editor, force=False):
        file_path = getattr(editor, "file_path", None)
        if not file_path:
            return False

        ext = os.path.splitext(file_path)[1].lower()
        if not force:
            if not self.format_on_save:
                return False
            if ext in self.format_disabled_languages:
                return False

        source = editor.toPlainText()
        if not source.strip():
            return False

        formatted = format_code(
            ext, source, on_error=lambda msg: self.terminal.append(msg + "\n")
        )

        if formatted != source:
            cursor_pos = editor.textCursor().position()
            editor.blockSignals(True)
            editor.setPlainText(formatted)
            editor.blockSignals(False)
            cursor = editor.textCursor()
            cursor.setPosition(min(cursor_pos, len(formatted)))
            editor.setTextCursor(cursor)
            return True

        return False

    def _format_current_editor(self):
        editor = self.tabs.current_editor()
        if not editor:
            return
        self._format_editor(editor, force=True)

    def _on_format_requested(self):
        self._format_current_editor()

    # ==========================================
    # GIT INTEGRATION
    # ==========================================

    def find_git_root(self, start_path):
        current = os.path.abspath(start_path)
        while True:
            if os.path.isdir(os.path.join(current, ".git")):
                return current
            parent = os.path.dirname(current)
            if parent == current:
                return None
            current = parent

    def update_git_status(self):
        editor = self.tabs.current_editor()
        file_path = getattr(editor, "file_path", None) if editor else None

        if file_path:
            git_root = self.find_git_root(os.path.dirname(file_path))
        else:
            git_root = self.find_git_root(self.current_root)

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
                    full_path = os.path.abspath(os.path.join(git_root, rel_path))
                    changed_files.add(full_path)
            self.file_model.set_git_changes(changed_files)
        except subprocess.CalledProcessError:
            pass

    def show_diff(self, file_path):
        git_root = self.find_git_root(os.path.dirname(file_path))
        if not git_root:
            return

        try:
            diff_output = subprocess.check_output(
                ["git", "diff", "HEAD", "--no-color", "--", file_path],
                cwd=git_root,
                text=True,
            )

            if not diff_output:
                diff_output = subprocess.check_output(
                    ["git", "diff", "--cached", "--no-color", "--", file_path],
                    cwd=git_root,
                    text=True,
                )

            if not diff_output:
                with open(file_path, "r", encoding="utf-8") as f:
                    diff_output = f.read()

            if not diff_output:
                diff_output = "[Empty file]"

            base_name = os.path.basename(file_path)
            tab_name = f"{base_name} (diff)"

            for i in range(self.tabs.count()):
                if self.tabs.tabText(i) == tab_name:
                    self.tabs.setCurrentIndex(i)
                    editor = self.tabs.widget(i)
                    editor.setReadOnly(False)
                    editor.setPlainText(diff_output)
                    editor.setReadOnly(True)
                    self.apply_diff_highlighting(editor)
                    return

            current_editor = self.tabs.current_editor()
            current_index = self.tabs.currentIndex()

            is_blank_untitled = (
                current_editor is not None
                and getattr(current_editor, "file_path", None) is None
                and current_editor.toPlainText() == ""
            )

            if is_blank_untitled:
                editor = current_editor
                self.tabs.setTabText(current_index, tab_name)
            else:
                editor = self.tabs.create_tab(tab_name)
                self.tabs.setTabText(self.tabs.currentIndex(), tab_name)

            editor.setPlainText(diff_output)
            editor.setReadOnly(True)
            self.apply_diff_highlighting(editor)

        except subprocess.CalledProcessError as e:
            print(f"Error generating diff: {e}")

    def apply_diff_highlighting(self, editor):
        if hasattr(editor, "highlighter") and editor.highlighter is not None:
            editor.highlighter.setDocument(None)
            del editor.highlighter

        editor.highlighter = DiffHighlighter(editor.document(), self.theme_tokens)
        editor.highlighter.rehighlight()

    # ==========================================
    # EXECUTION
    # ==========================================

    def run_file_in_terminal(self):
        editor = self.tabs.current_editor()
        if not editor:
            return

        current_index = self.tabs.currentIndex()
        if self.tabs.tabText(current_index).endswith("(diff)"):
            return

        file_path = getattr(editor, "file_path", None)
        if not file_path:
            if not self.save_file_as():
                return
            file_path = editor.file_path

        self.save_file()

        working_dir = os.path.dirname(file_path)

        self.terminal.run_command([file_path], working_directory=working_dir)

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

    def show_shortcuts(self):
        dialog = ShortcutsWindow(self.theme_tokens, self)
        dialog.exec()

    def toggle_line_wrap(self):
        new_value = not self.settings.value("line_wrap", False, type=bool)
        self.settings.setValue("line_wrap", new_value)
        self._apply_editor_preferences()

    def toggle_line_numbers(self):
        new_value = not self.settings.value("show_line_numbers", True, type=bool)
        self.settings.setValue("show_line_numbers", new_value)
        self._apply_editor_preferences()

    def zoom_in(self):
        self._set_font_size(self._current_font_size() + 1)

    def zoom_out(self):
        self._set_font_size(self._current_font_size() - 1)

    def reset_zoom(self):
        self._set_font_size(15)

    def _current_font_size(self):
        return self.settings.value("font_size", 15, type=int)

    def _set_font_size(self, size):
        size = max(8, min(32, size))
        if size == self._current_font_size():
            return
        self.settings.setValue("font_size", size)
        self._apply_editor_preferences()

    def _toggle_comment(self):
        editor = self.tabs.current_editor()
        if editor and hasattr(editor, "toggle_comment"):
            editor.toggle_comment()

    def toggle_zen_mode(self):
        self._zen_mode = not self._zen_mode
        if self._zen_mode:
            self._enter_zen_mode()
        else:
            self._exit_zen_mode()

    def _enter_zen_mode(self):
        self._saved_main_splitter_sizes = self.main_splitter.sizes()
        self._saved_editor_splitter_sizes = self.editor_splitter.sizes()

        self.sidebar_tabs.hide()
        self.status_bar.hide()
        self.find_widget.hide()
        self.search_panel.hide()
        self.terminal.hide()
        self.tabs.set_zen_mode(True)

    def _exit_zen_mode(self):
        self.sidebar_tabs.show()
        self.status_bar.show()
        self.terminal.show()
        self.tabs.set_zen_mode(False)

        if self._saved_main_splitter_sizes:
            self.main_splitter.setSizes(self._saved_main_splitter_sizes)
        if self._saved_editor_splitter_sizes:
            self.editor_splitter.setSizes(self._saved_editor_splitter_sizes)

    # ==========================================
    # FILE EXPLORER CONTEXT MENU
    # ==========================================

    def show_context_menu(self, pos):
        index = self.tree_view.indexAt(pos)
        menu = QMenu(self)

        action_new_file = menu.addAction("New File")
        action_new_folder = menu.addAction("New Folder")
        action_save_project = menu.addAction("Save as Project")
        action_open_terminal = menu.addAction("Open in Terminal")

        if index.isValid():
            menu.addSeparator()
            action_rename = menu.addAction("Rename")
            action_delete = menu.addAction("Delete")
        else:
            action_rename = None
            action_delete = None

        action = menu.exec(self.tree_view.viewport().mapToGlobal(pos))
        if action is None:
            return

        if action == action_new_file:
            self.create_file(pos)
        elif action == action_new_folder:
            self.create_folder(pos)
        elif action == action_save_project:
            self._save_current_as_project(pos)
        elif action == action_open_terminal:
            self._open_terminal_at(pos)
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

    def _save_current_as_project(self, pos):
        index = self.tree_view.indexAt(pos)
        if index.isValid():
            path = self.file_model.filePath(index)
            if not os.path.isdir(path):
                path = os.path.dirname(path)
            default_name = os.path.basename(path.rstrip("/")) or path
        else:
            path = self.current_root
            default_name = os.path.basename(path.rstrip("/")) or path
        self.projects_panel.add_project(path, default_name)

    # ==========================================
    # FILE & FOLDER OPERATIONS
    # ==========================================

    def open_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Open Folder")
        if folder_path:
            self.set_tree_root(folder_path)

    def _add_current_root_as_project(self):
        default_name = (
            os.path.basename(self.current_root.rstrip("/")) or self.current_root
        )
        self.projects_panel.add_project(self.current_root, default_name)

    def go_to_directory(self):
        new_path = self.path_input.text().strip()
        new_path = os.path.expanduser(new_path)

        if os.path.isdir(new_path):
            self.set_tree_root(new_path)
        else:
            self.path_input.setText(self.file_model.rootPath())

    def set_tree_root(self, path):
        self.current_root = path
        self.settings.setValue("current_root", path)
        self.file_model.setRootPath(path)
        self.tree_view.setRootIndex(self.file_model.index(path))
        self.path_input.setText(path)

        git_root = self.find_git_root(path)
        if git_root:
            self.git_panel.set_working_dir(git_root)
        else:
            self.git_panel.set_working_dir("")

        self.update_git_status()

        editor = self.tabs.current_editor()
        if editor:
            file_path = getattr(editor, "file_path", None)
            if file_path and not self.tabs.tabText(self.tabs.currentIndex()).endswith(
                "(diff)"
            ):
                self._update_breadcrumbs(file_path)
            else:
                self._update_breadcrumbs(None)

    def _open_project(self, path):
        self.set_tree_root(path)
        self.sidebar_tabs.setCurrentWidget(self.sidebar_tabs.widget(0))

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

            if self.tabs.currentIndex() >= 0:
                self._update_breadcrumbs(file_path)

            self._add_recent_file(file_path)

        except Exception as e:
            print(f"Error opening file: {e}")

    def save_file(self) -> bool:
        editor = self.tabs.current_editor()
        if not editor:
            return False

        file_path = getattr(editor, "file_path", None)
        if not file_path:
            return self.save_file_as()

        self._format_editor(editor, force=False)

        try:
            with open(file_path, "w", encoding="utf-8") as file:
                file.write(editor.toPlainText())

            editor.document().setModified(False)
            self.update_window_title()

            self.update_git_status()
            if hasattr(self, "git_panel"):
                self.git_panel.refresh()

            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def save_file_as(self) -> bool:
        editor = self.tabs.current_editor()
        if not editor:
            return False

        if self.tabs.tabText(self.tabs.currentIndex()).endswith("(diff)"):
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

            success = self.save_file()

            if success:
                self.refresh_tree()
                if hasattr(self, "git_panel"):
                    self.git_panel.refresh()
                self._update_breadcrumbs(file_path)

            return success

        return False

    def handle_unsaved_tab_close(self, index):
        editor = self.tabs.widget(index)
        file_path = getattr(editor, "file_path", None)
        filename = os.path.basename(file_path) if file_path else "Untitled"

        if self.tabs.tabText(index).endswith("(diff)"):
            self.tabs._force_close_tab(index)
            return

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

    def _open_terminal_at(self, pos):
        index = self.tree_view.indexAt(pos)
        if index.isValid():
            path = self.file_model.filePath(index)
            if not os.path.isdir(path):
                path = os.path.dirname(path)
        else:
            path = self.current_root
        self._open_terminal_here(path)

    def _open_terminal_here(self, path):
        candidates = []
        env_terminal = os.environ.get("TERMINAL")
        if env_terminal:
            candidates.append(env_terminal)
        candidates.extend(
            [
                "x-terminal-emulator",
                "kitty",
                "alacritty",
                "foot",
                "wezterm",
                "gnome-terminal",
                "konsole",
                "xfce4-terminal",
                "xterm",
            ]
        )

        for name in candidates:
            executable = shutil.which(name)
            if executable:
                try:
                    if name == "gnome-terminal":
                        subprocess.Popen([executable, "--working-directory", path])
                    elif name == "konsole":
                        subprocess.Popen([executable, "--workdir", path])
                    elif name == "xfce4-terminal":
                        subprocess.Popen([executable, "--working-directory", path])
                    elif name == "wezterm":
                        subprocess.Popen([executable, "start", "--cwd", path])
                    else:
                        subprocess.Popen([executable], cwd=path)
                    return
                except Exception as e:
                    print(f"Failed to launch {name}: {e}")
                    continue

        self.terminal.append(
            "\n[Terminal] No terminal emulator found on PATH. "
            "Set $TERMINAL to your preferred terminal.\n"
        )

    def _load_recent_files(self):
        raw = self.settings.value("recent_files", [], type=list)
        return [p for p in raw if isinstance(p, str) and os.path.isfile(p)]

    def _save_recent_files(self, files):
        self.settings.setValue("recent_files", files)

    def _add_recent_file(self, file_path):
        files = self._load_recent_files()
        if file_path in files:
            files.remove(file_path)
        files.insert(0, file_path)
        files = files[:10]
        self._save_recent_files(files)
        self._refresh_recent_menu()

    def _refresh_recent_menu(self):
        self.recent_submenu.clear()
        files = self._load_recent_files()

        if not files:
            empty_action = QAction("(No recent files)", self)
            empty_action.setEnabled(False)
            self.recent_submenu.addAction(empty_action)
            return

        for path in files:
            display = os.path.basename(path)
            action = QAction(display, self)
            action.setToolTip(path)
            action.triggered.connect(lambda checked, p=path: self._open_recent_file(p))
            self.recent_submenu.addAction(action)

        self.recent_submenu.addSeparator()
        clear_action = QAction("Clear Recent", self)
        clear_action.triggered.connect(self._clear_recent_files)
        self.recent_submenu.addAction(clear_action)

    def _open_recent_file(self, file_path):
        if not os.path.isfile(file_path):
            self.terminal.append(f"\n[Recent] File no longer exists: {file_path}\n")
            files = self._load_recent_files()
            if file_path in files:
                files.remove(file_path)
                self._save_recent_files(files)
                self._refresh_recent_menu()
            return
        self.load_file(file_path)

    def _clear_recent_files(self):
        self._save_recent_files([])
        self._refresh_recent_menu()

    # ==========================================
    # WINDOW CONTROL
    # ==========================================

    def eventFilter(self, obj, event):
        if obj == self.tree_view and event.type() == event.Type.KeyPress:
            if event.key() in (Qt.Key_Return, Qt.Key_Enter):
                index = self.tree_view.currentIndex()
                if index.isValid():
                    path = self.file_model.filePath(index)
                    if os.path.isdir(path):
                        self.set_tree_root(path)
                    elif os.path.isfile(path):
                        self.load_file(path)
                return True
            if event.key() == Qt.Key_Backspace:
                parent = os.path.dirname(self.current_root.rstrip("/"))
                if parent and parent != self.current_root:
                    self.set_tree_root(parent)
                return True
        return super().eventFilter(obj, event)

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
