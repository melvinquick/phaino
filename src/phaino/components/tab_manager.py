import os

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPalette, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .editor import CodeEditor


class TabManager(QWidget):
    current_tab_changed = Signal()
    tab_closed = Signal(int)
    tab_close_requested_with_unsaved_changes = Signal(int)
    cursor_position_changed = Signal(object)
    editor_text_changed = Signal()

    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.theme_tokens = theme_tokens

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(False)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.tabBar().setDrawBase(False)
        self.tabs.tabBar().setExpanding(False)

        self.tabs.currentChanged.connect(self.emit_current_changed)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.tabBar().installEventFilter(self)

        self.new_tab_btn = QPushButton("+")
        self.new_tab_btn.setObjectName("NewTabButton")
        self.new_tab_btn.setCursor(Qt.PointingHandCursor)
        self.new_tab_btn.setToolTip("New Tab (Ctrl+T)")
        self.new_tab_btn.clicked.connect(lambda: self.create_tab())
        self.new_tab_btn.setFixedSize(28, 28)

        corner_container = QWidget()
        corner_layout = QHBoxLayout(corner_container)
        corner_layout.setContentsMargins(0, 0, 0, 4)
        corner_layout.setSpacing(0)
        corner_layout.addWidget(self.new_tab_btn)
        corner_layout.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

        self.tabs.setCornerWidget(corner_container, Qt.TopRightCorner)

        self.main_layout.addWidget(self.tabs)

        self.setAutoFillBackground(True)
        self.apply_palette()

    def eventFilter(self, obj, event):
        if obj == self.tabs.tabBar() and event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.MiddleButton:
                index = self.tabs.tabBar().tabAt(event.pos())
                if index >= 0:
                    self.close_tab(index)
                    return True
        return super().eventFilter(obj, event)

    def create_red_dot_widget(self, index):
        pixmap = QPixmap(12, 12)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        red_color = self.theme_tokens.get("danger-color")
        painter.setBrush(QColor(red_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 8, 8)
        painter.end()

        label = QLabel()
        label.setPixmap(pixmap)
        label.setCursor(Qt.PointingHandCursor)
        label.setToolTip("Close Tab")

        label.mousePressEvent = lambda event, idx=index: (
            self.tabs.tabCloseRequested.emit(idx)
        )

        return label

    def apply_palette(self):
        palette = self.palette()
        bg_color = QColor(self.theme_tokens.get("background-color"))
        palette.setColor(QPalette.Window, bg_color)
        palette.setColor(QPalette.Base, bg_color)
        palette.setColor(QPalette.Button, bg_color)
        self.setPalette(palette)

        tabs_palette = self.tabs.palette()
        tabs_palette.setColor(QPalette.Window, bg_color)
        tabs_palette.setColor(QPalette.Base, bg_color)
        self.tabs.setPalette(tabs_palette)

        tabbar_palette = self.tabs.tabBar().palette()
        tabbar_palette.setColor(QPalette.Window, bg_color)
        self.tabs.tabBar().setPalette(tabbar_palette)

    def update_theme(self, theme_tokens):
        self.theme_tokens = theme_tokens
        self.apply_palette()
        for i in range(self.count()):
            editor = self.widget(i)
            if editor and hasattr(editor, "update_theme"):
                editor.update_theme(self.theme_tokens)
            self.tabs.tabBar().setTabButton(
                i,
                self.tabs.tabBar().ButtonPosition.RightSide,
                self.create_red_dot_widget(i),
            )

    def create_tab(self, title="Untitled"):
        editor = CodeEditor(self.theme_tokens, self)
        editor.setPlaceholderText("Type your code here...")

        index = self.tabs.addTab(editor, title)
        self.tabs.setCurrentIndex(index)

        red_dot = self.create_red_dot_widget(index)
        self.tabs.tabBar().setTabButton(
            index, self.tabs.tabBar().ButtonPosition.RightSide, red_dot
        )

        editor.document().modificationChanged.connect(
            lambda modified, e=editor: self.update_tab_title(e, modified)
        )

        editor.cursorPositionChanged.connect(
            lambda e=editor: self.cursor_position_changed.emit(e)
        )

        editor.textChanged.connect(lambda: self.editor_text_changed.emit())

        if self.parent() and hasattr(self.parent(), "update_window_title"):
            editor.document().modificationChanged.connect(
                self.parent().update_window_title
            )

        return editor

    def update_tab_title(self, editor, modified):
        index = self.tabs.indexOf(editor)
        if index == -1:
            return

        current_title = self.tabs.tabText(index)

        if current_title.endswith("(diff)"):
            return

        file_path = getattr(editor, "file_path", None)
        base_name = os.path.basename(file_path) if file_path else "Untitled"

        display_name = f"{base_name}*" if modified else base_name
        self.tabs.setTabText(index, display_name)

    def close_tab(self, index):
        editor = self.widget(index)

        if editor and editor.document().isModified():
            self.tab_close_requested_with_unsaved_changes.emit(index)
            return

        self._force_close_tab(index)

    def _force_close_tab(self, index):
        self.tabs.removeTab(index)
        self.tab_closed.emit(index)

        if self.count() == 0:
            self.create_tab()
        else:
            for i in range(self.count()):
                self.tabs.tabBar().setTabButton(
                    i,
                    self.tabs.tabBar().ButtonPosition.RightSide,
                    self.create_red_dot_widget(i),
                )
            self.emit_current_changed(self.tabs.currentIndex())

    def current_editor(self):
        return self.tabs.currentWidget()

    def emit_current_changed(self, index):
        self.current_tab_changed.emit()

    def count(self):
        return self.tabs.count()

    def widget(self, index):
        return self.tabs.widget(index)

    def setTabText(self, index, text):
        editor = self.widget(index)
        base_name = text.replace("*", "")
        if editor and editor.document().isModified():
            base_name += "*"
        self.tabs.setTabText(index, base_name)

    def setCurrentIndex(self, index):
        self.tabs.setCurrentIndex(index)

    def currentIndex(self):
        return self.tabs.currentIndex()

    def get_current_file_path(self):
        editor = self.current_editor()
        if editor:
            return getattr(editor, "file_path", None)
        return None

    def tabText(self, index):
        return self.tabs.tabText(index)
