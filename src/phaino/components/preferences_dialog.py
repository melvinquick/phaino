from PySide6.QtCore import Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .formatter_factory import FORMATTER_MAP, FORMATTER_NAMES


class PreferencesDialog(QDialog):
    settings_changed = Signal()

    def __init__(self, settings, themes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setObjectName("PreferencesDialog")
        self.resize(500, 650)
        self.setModal(True)

        self.settings = settings
        self.themes = themes

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Appearance ---
        appearance_group = QGroupBox("Appearance")
        appearance_layout = QVBoxLayout(appearance_group)

        theme_row = QHBoxLayout()
        theme_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        for key in themes:
            if key == "general":
                continue
            display = key.replace("_", " ").title()
            self.theme_combo.addItem(display, key)
        current_theme = settings.value("theme", "phaino_dark", type=str)
        idx = self.theme_combo.findData(current_theme)
        if idx >= 0:
            self.theme_combo.setCurrentIndex(idx)
        theme_row.addWidget(self.theme_combo, 1)
        appearance_layout.addLayout(theme_row)

        font_row = QHBoxLayout()
        font_row.addWidget(QLabel("Editor Font:"))

        self.font_family_combo = QComboBox()
        mono_families = [
            f for f in QFontDatabase.families() if QFontDatabase.isFixedPitch(f)
        ]
        if not mono_families:
            mono_families = ["Fira Code", "JetBrains Mono", "Consolas"]
        for family in mono_families:
            self.font_family_combo.addItem(family)

        saved_family = settings.value("font_family", "Fira Code", type=str)
        idx = self.font_family_combo.findText(saved_family)
        if idx >= 0:
            self.font_family_combo.setCurrentIndex(idx)

        font_row.addWidget(self.font_family_combo, 1)
        font_row.addWidget(QLabel("Size:"))
        self.font_spin = QSpinBox()
        self.font_spin.setRange(8, 32)
        self.font_spin.setValue(settings.value("font_size", 15, type=int))
        font_row.addWidget(self.font_spin)
        appearance_layout.addLayout(font_row)

        layout.addWidget(appearance_group)

        # --- Editor ---
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout(editor_group)

        self.line_numbers_check = QCheckBox("Show line numbers")
        self.line_numbers_check.setChecked(
            settings.value("show_line_numbers", True, type=bool)
        )
        editor_layout.addWidget(self.line_numbers_check)

        self.line_wrap_check = QCheckBox("Enable line wrapping")
        self.line_wrap_check.setChecked(settings.value("line_wrap", False, type=bool))
        editor_layout.addWidget(self.line_wrap_check)

        self.trailing_ws_check = QCheckBox("Show trailing whitespace")
        self.trailing_ws_check.setChecked(
            settings.value("show_trailing_whitespace", False, type=bool)
        )
        editor_layout.addWidget(self.trailing_ws_check)

        layout.addWidget(editor_group)

        # --- Formatting ---
        formatting_group = QGroupBox("Formatting")
        formatting_layout = QVBoxLayout(formatting_group)

        self.format_on_save_check = QCheckBox("Format on save")
        self.format_on_save_check.setChecked(
            settings.value("format_on_save", True, type=bool)
        )
        formatting_layout.addWidget(self.format_on_save_check)

        formatting_layout.addWidget(QLabel("Languages to format:"))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setMaximumHeight(200)

        lang_container = QWidget()
        lang_layout = QVBoxLayout(lang_container)
        lang_layout.setContentsMargins(5, 5, 5, 5)
        lang_layout.setSpacing(2)

        disabled = set(settings.value("format_disabled_languages", [], type=list))
        self.language_checks = {}

        for ext in FORMATTER_MAP:
            formatter_name = FORMATTER_NAMES.get(ext, "")
            label = f"{ext}  ({formatter_name})" if formatter_name else ext
            check = QCheckBox(label)
            check.setChecked(ext not in disabled)
            check.toggled.connect(self._on_change)
            lang_layout.addWidget(check)
            self.language_checks[ext] = check

        lang_layout.addStretch()
        scroll.setWidget(lang_container)
        formatting_layout.addWidget(scroll)

        layout.addWidget(formatting_group)

        # --- Close Button ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setObjectName("PrimaryButton")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

        # --- Signals ---
        self.theme_combo.currentIndexChanged.connect(self._on_change)
        self.font_family_combo.currentIndexChanged.connect(self._on_change)
        self.font_spin.valueChanged.connect(self._on_change)
        self.line_numbers_check.toggled.connect(self._on_change)
        self.line_wrap_check.toggled.connect(self._on_change)
        self.trailing_ws_check.toggled.connect(self._on_change)
        self.format_on_save_check.toggled.connect(self._on_change)

    def _on_change(self, *args):
        self._save()
        self.settings_changed.emit()

    def _save(self):
        self.settings.setValue("theme", self.theme_combo.currentData())
        self.settings.setValue("font_family", self.font_family_combo.currentText())
        self.settings.setValue("font_size", self.font_spin.value())
        self.settings.setValue("show_line_numbers", self.line_numbers_check.isChecked())
        self.settings.setValue("line_wrap", self.line_wrap_check.isChecked())
        self.settings.setValue(
            "show_trailing_whitespace", self.trailing_ws_check.isChecked()
        )
        self.settings.setValue("format_on_save", self.format_on_save_check.isChecked())

        disabled = [
            ext for ext, check in self.language_checks.items() if not check.isChecked()
        ]
        self.settings.setValue("format_disabled_languages", disabled)
