from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, document, theme_tokens):
        super().__init__(document)

        accent_color = theme_tokens.get("accent-color")
        string_color = theme_tokens.get("success-color")
        muted_color = theme_tokens.get("muted-color")
        function_color = theme_tokens.get("function-color")

        self.highlighting_rules = []

        header_format = QTextCharFormat()
        header_format.setForeground(QColor(accent_color))
        header_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"^#{1,6}\s.*$"), header_format)
        )

        bold_format = QTextCharFormat()
        bold_format.setFontWeight(QFont.Weight.Bold)
        bold_format.setForeground(QColor(function_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"\*\*.*?\*\*"), bold_format)
        )

        italic_format = QTextCharFormat()
        italic_format.setFontItalic(True)
        italic_format.setForeground(QColor(function_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"(?<!\*)\*[^\*]+\*(?!\*)"), italic_format)
        )
        self.highlighting_rules.append((QRegularExpression(r"_.*?_"), italic_format))

        inline_code_format = QTextCharFormat()
        inline_code_format.setForeground(QColor(string_color))
        inline_code_format.setFontFamilies(["Fira Code", "Consolas", "monospace"])
        self.highlighting_rules.append(
            (QRegularExpression(r"`[^`\n]+`"), inline_code_format)
        )

        quote_format = QTextCharFormat()
        quote_format.setForeground(QColor(muted_color))
        quote_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"^>.*$"), quote_format))

        link_format = QTextCharFormat()
        link_format.setForeground(QColor(accent_color))
        link_format.setFontUnderline(True)
        self.highlighting_rules.append(
            (QRegularExpression(r"\[.*?\]\(.*?\)"), link_format)
        )

        self.fence_format = QTextCharFormat()
        self.fence_format.setForeground(QColor(muted_color))

        self.fence_lang_format = QTextCharFormat()
        self.fence_lang_format.setForeground(QColor(function_color))
        self.fence_lang_format.setFontWeight(QFont.Weight.Bold)
        self.fence_lang_format.setFontFamilies(["Fira Code", "Consolas", "monospace"])

        self.code_block_format = QTextCharFormat()
        self.code_block_format.setForeground(QColor(string_color))
        self.code_block_format.setFontFamilies(["Fira Code", "Consolas", "monospace"])

    def _style_fence_line(self, text):
        """Style a ``` fence line: dim the backticks, highlight the language tag."""
        stripped = text.lstrip()
        leading = len(text) - len(stripped)
        # Apply muted color to the whole line first
        self.setFormat(leading, len(stripped), self.fence_format)
        # Then highlight the language tag (everything after the backticks)
        if stripped.startswith("```"):
            lang = stripped[3:].strip()
            if lang:
                lang_start = (
                    leading + 3 + (len(stripped[3:]) - len(stripped[3:].lstrip()))
                )
                self.setFormat(lang_start, len(lang), self.fence_lang_format)

    def highlightBlock(self, text):
        in_fence = self.previousBlockState() == 1
        is_fence_line = text.lstrip().startswith("```")

        if in_fence:
            if is_fence_line:
                self._style_fence_line(text)
                self.setCurrentBlockState(0)
                return
            self.setFormat(0, len(text), self.code_block_format)
            self.setCurrentBlockState(1)
            return
        else:
            if is_fence_line:
                self._style_fence_line(text)
                self.setCurrentBlockState(1)
                return
            self.setCurrentBlockState(0)

        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
