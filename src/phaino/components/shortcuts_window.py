from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ShortcutsWindow(QDialog):
    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Phaino - Keyboard Shortcuts")
        self.resize(500, 600)
        self.setObjectName("ShortcutsWindow")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("Keyboard Shortcuts")
        title.setObjectName("ShortcutsTitle")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)

        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setAlignment(Qt.AlignTop)
        content_layout.setSpacing(8)

        shortcuts = [
            ("File Operations", None),
            ("Ctrl+O", "Open File"),
            ("Ctrl+P", "Quick Open File"),
            ("Ctrl+Shift+O", "Open Folder"),
            ("Ctrl+S", "Save File"),
            ("Ctrl+Shift+S", "Save As..."),
            ("Ctrl+T", "New Tab"),
            ("", ""),
            ("Editing", None),
            ("Ctrl+Z", "Undo"),
            ("Ctrl+Y / Ctrl+Shift+Z", "Redo"),
            ("Ctrl+X", "Cut"),
            ("Ctrl+C", "Copy"),
            ("Ctrl+V", "Paste"),
            ("Tab", "Insert 4 Spaces"),
            ("Shift+Tab", "Un-indent"),
            ("Ctrl+/", "Toggle Comment"),
            ("", ""),
            ("Search & Navigation", None),
            ("Ctrl+F", "Find / Replace"),
            ("Ctrl+Shift+F", "Search Across Files"),
            ("Ctrl+Space", "Trigger Auto-complete"),
            ("Ctrl+G", "Go to Line"),
            ("Ctrl+Shift+P", "Command Palette"),
            ("Esc", "Close Panel / Hide Popup"),
            ("", ""),
            ("View", None),
            ("Ctrl+= / Ctrl++", "Zoom In"),
            ("Ctrl+-", "Zoom Out"),
            ("Ctrl+0", "Reset Zoom"),
            ("", ""),
            ("Execution", None),
            ("Ctrl+R", "Run Current File"),
            ("", ""),
            ("Application", None),
            ("Ctrl+,", "Open Preferences"),
            ("Ctrl+K", "Toggle Zen Mode"),
            ("F1", "Show this window"),
        ]

        for key, desc in shortcuts:
            if key == "":
                spacer = QWidget()
                spacer.setFixedHeight(10)
                content_layout.addWidget(spacer)
                continue

            if desc is None:
                section = QLabel(key)
                section.setObjectName("ShortcutSection")
                content_layout.addWidget(section)
            else:
                row = QWidget()
                row_layout = QHBoxLayout(row)
                row_layout.setContentsMargins(0, 0, 0, 0)

                key_label = QLabel(key)
                key_label.setObjectName("ShortcutKey")
                key_label.setFixedWidth(180)

                desc_label = QLabel(desc)
                desc_label.setObjectName("ShortcutDesc")

                row_layout.addWidget(key_label)
                row_layout.addWidget(desc_label)
                row_layout.addStretch()
                content_layout.addWidget(row)

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        btn_close = QPushButton("Close")
        btn_close.setObjectName("PrimaryButton")
        btn_close.clicked.connect(self.accept)
        main_layout.addWidget(btn_close, alignment=Qt.AlignCenter)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
