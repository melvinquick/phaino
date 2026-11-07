import os
import re

from PySide6.QtCore import QPoint, QRect, QSize, QStringListModel, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QPen,
    QTextCharFormat,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import QCompleter, QMenu, QPlainTextEdit, QTextEdit, QWidget

COMMENT_PREFIXES = {
    ".py": "# ",
    ".toml": "# ",
    ".yaml": "# ",
    ".yml": "# ",
    ".js": "// ",
    ".ts": "// ",
    ".rs": "// ",
    ".go": "// ",
}


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class RightMargin(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(35, 0)

    def paintEvent(self, event):
        self.code_editor.right_margin_paint_event(event)


class CodeEditor(QPlainTextEdit):
    escape_pressed = Signal()
    format_requested = Signal()

    BRACKET_PAIRS = {
        "(": ")",
        "[": "]",
        "{": "}",
        '"': '"',
        "'": "'",
    }

    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.theme_tokens = theme_tokens

        self.bg_color = self.theme_tokens.get("background-color")
        self.muted_color = self.theme_tokens.get("muted-color")
        self.surface_color = self.theme_tokens.get("surface-color")
        self.show_trailing_ws = False
        self._show_line_numbers = True

        self.line_number_area = LineNumberArea(self)
        self.right_margin = RightMargin(self)

        self.blockCountChanged.connect(self.update_margin_widths)
        self.updateRequest.connect(self.update_margins)
        self.cursorPositionChanged.connect(self._update_trailing_ws_highlight)
        self.textChanged.connect(self._update_trailing_ws_highlight)

        self.update_margin_widths(0)

        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)
        self.textChanged.connect(self.update_completer_model)
        self.completer.setModel(QStringListModel([]))

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self.update_editor_preferences("Fira Code", 15, True, False, False)

    def _show_context_menu(self, pos: QPoint):
        menu = QMenu(self)
        format_action = menu.addAction("Format Document")
        format_action.triggered.connect(self.format_requested.emit)
        menu.exec(self.mapToGlobal(pos))

    def update_editor_preferences(
        self,
        font_family,
        font_size,
        show_line_numbers,
        line_wrap,
        show_trailing_ws=False,
    ):
        font = QFont(font_family, font_size)
        self.setFont(font)
        self.document().setDefaultFont(font)

        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setLineWrapMode(
            QPlainTextEdit.WidgetWidth if line_wrap else QPlainTextEdit.NoWrap
        )

        self._show_line_numbers = show_line_numbers
        self.line_number_area.setVisible(show_line_numbers)
        self.update_margin_widths(0)

        saved_cursor = self.textCursor().position()
        saved_vscroll = self.verticalScrollBar().value()
        saved_hscroll = self.horizontalScrollBar().value()

        cursor = self.textCursor()
        cursor.setPosition(min(saved_cursor, len(self.toPlainText())))
        self.setTextCursor(cursor)
        self.verticalScrollBar().setValue(saved_vscroll)
        self.horizontalScrollBar().setValue(saved_hscroll)

        self.show_trailing_ws = show_trailing_ws
        self._update_trailing_ws_highlight()

    def _update_trailing_ws_highlight(self):
        extra_selections = []

        if getattr(self, "show_trailing_ws", False):
            block = self.document().firstBlock()
            while block.isValid():
                text = block.text()
                stripped_len = len(text.rstrip())
                full_len = len(text)
                if stripped_len < full_len:
                    selection = QTextEdit.ExtraSelection()
                    cursor = QTextCursor(block)
                    cursor.setPosition(block.position() + stripped_len)
                    cursor.setPosition(
                        block.position() + full_len,
                        QTextCursor.KeepAnchor,
                    )
                    selection.cursor = cursor
                    fmt = QTextCharFormat()
                    bg = QColor(self.theme_tokens.get("danger-color"))
                    bg.setAlpha(180)
                    fmt.setBackground(bg)
                    selection.format = fmt
                    extra_selections.append(selection)
                block = block.next()

        if not self.isReadOnly():
            line_selection = QTextEdit.ExtraSelection()
            line_color = QColor(self.surface_color)
            line_selection.format.setBackground(line_color)
            line_selection.format.setProperty(
                QTextFormat.Property.FullWidthSelection, True
            )
            line_selection.cursor = self.textCursor()
            line_selection.cursor.clearSelection()
            extra_selections.append(line_selection)

        self.setExtraSelections(extra_selections)

    def update_margin_widths(self, new_block_count):
        left_margin = self.line_number_area_width() if self._show_line_numbers else 0
        self.setViewportMargins(left_margin, 0, 35, 0)

    def update_margins(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
            self.right_margin.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
            self.right_margin.update(
                0, rect.y(), self.right_margin.width(), rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_margin_widths(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )
        self.right_margin.setGeometry(QRect(cr.right() - 35, cr.top(), 35, cr.height()))

    def right_margin_paint_event(self, event):
        painter = QPainter(self.right_margin)
        painter.fillRect(event.rect(), QColor(self.bg_color))

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        hex_pattern = re.compile(r"#(?:[0-9a-fA-F]{3}){1,2}\b")

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                text = block.text()
                match = hex_pattern.search(text)

                if match:
                    color_hex = match.group(0)
                    painter.setBrush(QColor(color_hex))
                    painter.setPen(QPen(QColor(self.muted_color), 1))

                    rect_size = 14
                    y_offset = top + (self.fontMetrics().height() - rect_size) // 2

                    painter.drawRoundedRect(5, y_offset, rect_size, rect_size, 3, 3)

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def line_number_area_width(self):
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num *= 0.1
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(self.bg_color))
        painter.setPen(QColor(self.muted_color))
        painter.setFont(self.font())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + round(self.blockBoundingRect(block).height())

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 5,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def update_theme(self, theme_tokens):
        self.theme_tokens = theme_tokens
        self.bg_color = self.theme_tokens.get("background-color")
        self.muted_color = self.theme_tokens.get("muted-color")
        self.surface_color = self.theme_tokens.get("widget-background-color")

        self.line_number_area.update()
        self.right_margin.update()
        self._update_trailing_ws_highlight()

    def toggle_comment(self):
        prefix = self._comment_prefix()
        if not prefix:
            return

        cursor = self.textCursor()

        if cursor.hasSelection():
            start_block = self.document().findBlock(cursor.selectionStart())
            end_block = self.document().findBlock(cursor.selectionEnd())
        else:
            start_block = cursor.block()
            end_block = start_block

        blocks = []
        block = start_block
        while block.isValid():
            blocks.append(block)
            if block == end_block:
                break
            block = block.next()

        all_commented = all(b.text().lstrip().startswith(prefix) for b in blocks)

        cursor.beginEditBlock()
        for block in blocks:
            block_cursor = QTextCursor(block)
            block_cursor.movePosition(QTextCursor.StartOfBlock)
            text = block.text()
            leading = len(text) - len(text.lstrip())
            block_cursor.setPosition(block.position() + leading)

            if all_commented:
                block_cursor.setPosition(
                    block.position() + leading + len(prefix),
                    QTextCursor.KeepAnchor,
                )
                block_cursor.removeSelectedText()
            else:
                block_cursor.insertText(prefix)
        cursor.endEditBlock()

    def _comment_prefix(self):
        file_path = getattr(self, "file_path", None)
        if not file_path:
            return None

        _, ext = os.path.splitext(file_path)
        return COMMENT_PREFIXES.get(ext.lower())

    def update_completer_model(self):
        text = self.toPlainText()
        tc = self.textCursor()
        tc.select(tc.SelectionType.WordUnderCursor)
        current_word = tc.selectedText()
        words = set(
            [
                w
                for w in re.findall(r"\b\w+\b", text)
                if len(w) > 2 and w != current_word
            ]
        )
        if hasattr(self, "highlighter") and self.highlighter is not None:
            if hasattr(self.highlighter, "keywords"):
                words.update(self.highlighter.keywords)
        self.completer.setModel(QStringListModel(sorted(list(words))))

    def insert_completion(self, completion):
        tc = self.textCursor()
        prefix = self.completer.completionPrefix()
        tc.movePosition(tc.MoveOperation.Left, tc.MoveMode.KeepAnchor, len(prefix))
        tc.insertText(completion)
        self.setTextCursor(tc)

    def _insert_bracket_pair(self, char):
        if char not in self.BRACKET_PAIRS:
            return False

        cursor = self.textCursor()
        closer = self.BRACKET_PAIRS[char]

        if cursor.hasSelection():
            selected = cursor.selectedText()
            cursor.insertText(char + selected + closer)
            self.setTextCursor(cursor)
            return True

        next_char = self.document().characterAt(cursor.position())
        if next_char == closer:
            cursor.movePosition(QTextCursor.Right)
            self.setTextCursor(cursor)
            return True

        cursor.insertText(char + closer)
        cursor.movePosition(QTextCursor.Left)
        self.setTextCursor(cursor)
        return True

    def keyPressEvent(self, event):
        if event.key() in (
            Qt.Key_Control,
            Qt.Key_Shift,
            Qt.Key_Alt,
            Qt.Key_Meta,
        ):
            event.accept()
            return

        if event.key() == Qt.Key_Escape:
            if self.completer and self.completer.popup().isVisible():
                self.completer.popup().hide()
                event.accept()
                return
            else:
                self.escape_pressed.emit()
                return

        if self.completer and self.completer.popup().isVisible():
            if event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Tab, Qt.Key_Backtab):
                event.ignore()
                return

        char = event.text()
        if char in self.BRACKET_PAIRS and event.modifiers() in (
            Qt.NoModifier,
            Qt.ShiftModifier,
        ):
            if self._insert_bracket_pair(char):
                event.accept()
                return

        if event.key() == Qt.Key_Tab:
            self.insertPlainText("    ")
            return

        if event.key() == Qt.Key_Backtab or (
            event.key() == Qt.Key_Tab and event.modifiers() == Qt.ShiftModifier
        ):
            cursor = self.textCursor()
            cursor.movePosition(QTextCursor.StartOfBlock)
            block_text = cursor.block().text()
            spaces = 0
            for c in block_text:
                if c == " ":
                    spaces += 1
                else:
                    break
            spaces_to_delete = min(4, spaces)
            if spaces_to_delete > 0:
                cursor.movePosition(
                    QTextCursor.Right, QTextCursor.KeepAnchor, spaces_to_delete
                )
                cursor.removeSelectedText()
            return

        if event.key() in (Qt.Key_Return, Qt.Key_Enter):
            cursor = self.textCursor()
            current_line = cursor.block().text()
            leading_whitespace = ""
            for c in current_line:
                if c.isspace():
                    leading_whitespace += c
                else:
                    break
            super().keyPressEvent(event)
            if current_line.rstrip().endswith(":"):
                cursor.insertText(leading_whitespace + "    ")
            else:
                cursor.insertText(leading_whitespace)
            self.setTextCursor(cursor)
            return

        is_shortcut = (
            event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Space
        )

        if not self.completer or not is_shortcut:
            super().keyPressEvent(event)

        tc = self.textCursor()
        tc.select(tc.SelectionType.WordUnderCursor)
        prefix = tc.selectedText()

        if len(prefix) >= 2 or is_shortcut:
            if is_shortcut:
                self.completer.setCompletionPrefix("")
            else:
                self.completer.setCompletionPrefix(prefix)

            popup = self.completer.popup()
            if self.completer.completionCount() > 0:
                popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
                cr = self.cursorRect()
                cr.setWidth(
                    self.completer.popup().sizeHintForColumn(0)
                    + self.completer.popup().verticalScrollBar().sizeHint().width()
                )
                self.completer.complete(cr)
            else:
                popup.hide()
        else:
            self.completer.popup().hide()

    def inputMethodEvent(self, event):
        commit = event.commitString()
        if commit and len(commit) == 1 and commit in self.BRACKET_PAIRS:
            if self._insert_bracket_pair(commit):
                event.accept()
                return
        super().inputMethodEvent(event)
