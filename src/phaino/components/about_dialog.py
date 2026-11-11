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
            app_license = "MIT"

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

        accent = theme_tokens.get("accent-color")
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
