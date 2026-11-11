from importlib.metadata import metadata

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QPushButton,
    QVBoxLayout,
)


class AboutDialog(QDialog):
    def __init__(self, theme_tokens, logo_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About Phaino")
        self.setFixedSize(400, 450)
        self.setObjectName("AboutDialog")

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
            QLabel#AppName {{
                font-size: 24px;
                font-weight: bold;
                margin-top: 10px;
            }}
            QLabel#AppVersion {{
                font-size: 14px;
                color: {muted};
            }}
            QLabel#AppAuthor, QLabel#AppLicense {{
                font-size: 13px;
                color: {color};
            }}
            QLabel#LinkLabel {{
                color: {accent};
                font-size: 13px;
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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        layout.setSpacing(10)

        logo_label = QLabel()
        pixmap = QPixmap(logo_path)
        logo_label.setPixmap(
            pixmap.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        logo_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(logo_label)

        name_label = QLabel("Phaino")
        name_label.setObjectName("AppName")
        name_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(name_label)

        meta = metadata("phaino")
        app_version = meta.get("Version", "Unknown")

        app_license = meta.get("License-Expression") or meta.get("License")
        if not app_license or app_license == "UNKNOWN":
            app_license = "MIT"  # Fallback

        version_label = QLabel(f"Version {app_version}")
        version_label.setObjectName("AppVersion")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        author_label = QLabel("Created by Melvin Quick")
        author_label.setObjectName("AppAuthor")
        author_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(author_label)

        license_label = QLabel(f"Licensed under {app_license}")
        license_label.setObjectName("AppLicense")
        license_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(license_label)

        links_html = (
            f'<a href="https://github.com/melvinquick/phaino" style="color: {accent}; text-decoration: none;">GitHub Repository</a>'
            " &nbsp;|&nbsp; "
            f'<a href="https://github.com/melvinquick/phaino/blob/main/CHANGELOG" style="color: {accent}; text-decoration: none;">Changelog</a>'
        )

        links_label = QLabel(links_html)
        links_label.setObjectName("LinkLabel")
        links_label.setAlignment(Qt.AlignCenter)
        links_label.setOpenExternalLinks(True)
        layout.addWidget(links_label)

        layout.addStretch()

        btn_close = QPushButton("Close")
        btn_close.setObjectName("PrimaryButton")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignCenter)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.accept()
        else:
            super().keyPressEvent(event)
