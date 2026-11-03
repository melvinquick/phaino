from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat


class HtmlHighlighter(QSyntaxHighlighter):
    keywords = []

    def __init__(self, document, theme_tokens):
        super().__init__(document)

        accent_color = theme_tokens.get("accent-color")
        string_color = theme_tokens.get("success-color")
        muted_color = theme_tokens.get("muted-color")
        function_color = theme_tokens.get("function-color")

        self.highlighting_rules = []

        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor(accent_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"</?[a-zA-Z0-9-]+"), tag_format)
        )

        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor(function_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[a-zA-Z-]+(?==)"), attr_format)
        )

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(string_color))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(muted_color))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression(r"<!--[\s\S]*?-->"), comment_format)
        )

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
