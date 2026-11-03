import re

from PySide6.QtCore import QRect, QSize, QStringListModel, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QTextCursor, QTextFormat
from PySide6.QtWidgets import QCompleter, QPlainTextEdit, QTextEdit, QWidget


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

    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.theme_tokens = theme_tokens

        self.bg_color = self.theme_tokens.get("background-color")
        self.muted_color = self.theme_tokens.get("muted-color")
        self.surface_color = self.theme_tokens.get("surface-color")

        self.line_number_area = LineNumberArea(self)
        self.right_margin = RightMargin(self)

        self.blockCountChanged.connect(self.update_margin_widths)
        self.updateRequest.connect(self.update_margins)
        self.cursorPositionChanged.connect(self.highlight_current_line)

        self.update_margin_widths(0)

        self.completer = QCompleter(self)
        self.completer.setWidget(self)
        self.completer.setCompletionMode(QCompleter.PopupCompletion)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.activated.connect(self.insert_completion)
        self.textChanged.connect(self.update_completer_model)
        self.completer.setModel(QStringListModel([]))

    def update_margin_widths(self, new_block_count):
        self.setViewportMargins(self.line_number_area_width(), 0, 35, 0)

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

    def keyPressEvent(self, event):
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
            for char in block_text:
                if char == " ":
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
            for char in current_line:
                if char.isspace():
                    leading_whitespace += char
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

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(self.surface_color)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.Property.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def update_theme(self, theme_tokens):
        self.theme_tokens = theme_tokens
        self.bg_color = self.theme_tokens.get("background-color")
        self.muted_color = self.theme_tokens.get("muted-color")
        self.surface_color = self.theme_tokens.get("widget-background-color")

        self.line_number_area.update()
        self.right_margin.update()
        self.highlight_current_line()
