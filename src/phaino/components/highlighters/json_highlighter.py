from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class JsonHighlighter(QSyntaxHighlighter):
    keywords = []

    def __init__(self, document, theme_tokens):
        super().__init__(document)

        accent_color = theme_tokens.get("accent-color")
        string_color = theme_tokens.get("success-color")
        keyword_color = theme_tokens.get("warning-color")
        muted_color = theme_tokens.get("muted-color")
        function_color = theme_tokens.get("function-color")

        self.highlighting_rules = []

        key_format = QTextCharFormat()
        key_format.setForeground(QColor(function_color))
        self.highlighting_rules.append(
            (QRegularExpression(r'"[^"]*"(?=\s*:)'), key_format)
        )

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(string_color))
        self.highlighting_rules.append((QRegularExpression(r'"[^"]*"'), string_format))

        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor(keyword_color))
        bool_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"\b(true|false|null)\b"), bool_format)
        )

        number_format = QTextCharFormat()
        number_format.setForeground(QColor(accent_color))
        self.highlighting_rules.append(
            (
                QRegularExpression(r"\b-?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?\b"),
                number_format,
            )
        )

        brace_format = QTextCharFormat()
        brace_format.setForeground(QColor(muted_color))
        self.highlighting_rules.append((QRegularExpression(r"[{}\[\]]"), brace_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
