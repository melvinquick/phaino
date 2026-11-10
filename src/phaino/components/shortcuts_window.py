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

        bg_color = theme_tokens.get("background-color")
        color = theme_tokens.get("color")
        muted = theme_tokens.get("muted-color")
        surface = theme_tokens.get("surface-color")
        accent = theme_tokens.get("accent-color")

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
            }}
            QLabel {{
                color: {color};
                background-color: transparent;
            }}
            QLabel#ShortcutsTitle {{
                font-size: 20px;
                font-weight: bold;
                margin-bottom: 20px;
            }}
            QLabel#ShortcutSection {{
                color: {color};
                font-size: 14px;
                font-weight: bold;
                margin-top: 15px;
                margin-bottom: 5px;
                border-bottom: 1px solid {surface};
                padding-bottom: 4px;
            }}
            QLabel#ShortcutKey {{
                color: {color};
                font-family: 'Fira Code', 'JetBrains Mono', monospace;
                font-size: 13px;
            }}
            QLabel#ShortcutDesc {{
                color: {muted};
                font-size: 13px;
            }}
            QScrollArea {{
                border: none;
                background-color: transparent;
            }}
            QScrollArea > QWidget > QWidget {{
                background-color: {bg_color};
            }}
            QPushButton#PrimaryButton {{
                background-color: {surface};
                color: {color};
                border: 1px solid {muted};
                border-radius: 4px;
                padding: 8px 24px;
                font-weight: bold;
            }}
            QPushButton#PrimaryButton:hover {{
                background-color: {accent};
                color: white;
                border: 1px solid {accent};
            }}
        """)

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
