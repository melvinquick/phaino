from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class TomlHighlighter(QSyntaxHighlighter):
    keywords = []

    def __init__(self, document, theme_tokens):
        super().__init__(document)

        accent_color = theme_tokens.get("accent-color", "#E63946")
        string_color = theme_tokens.get("success-color", "#A3BE8C")
        keyword_color = theme_tokens.get("warning-color", "#EBCB8B")
        muted_color = theme_tokens.get("muted-color", "#888888")
        function_color = theme_tokens.get("function-color", "#88C0D0")

        self.highlighting_rules = []

        # 1. Tables / Headers ([section])
        header_format = QTextCharFormat()
        header_format.setForeground(QColor(accent_color))
        header_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"^\s*\[.*?\]"), header_format)
        )

        # 2. Keys (key = value)
        key_format = QTextCharFormat()
        key_format.setForeground(QColor(function_color))
        # Look for word characters before an equals sign
        self.highlighting_rules.append(
            (QRegularExpression(r"^\s*[\w\.-]+(?=\s*=)"), key_format)
        )

        # 3. Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(string_color))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        # 4. Booleans and Dates (basic)
        bool_format = QTextCharFormat()
        bool_format.setForeground(QColor(keyword_color))
        bool_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"\b(true|false)\b"), bool_format)
        )

        # 5. Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor(accent_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[0-9]+(\.[0-9]+)?\b"), number_format)
        )

        # 6. Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(muted_color))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), comment_format))

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
