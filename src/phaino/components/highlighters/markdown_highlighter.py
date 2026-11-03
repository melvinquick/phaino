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

        code_format = QTextCharFormat()
        code_format.setForeground(QColor(string_color))
        code_format.setFontFamilies(["Fira Code", "Consolas", "monospace"])
        self.highlighting_rules.append((QRegularExpression(r"`[^`]+`"), code_format))

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

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
