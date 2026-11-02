from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class HtmlHighlighter(QSyntaxHighlighter):
    keywords = []

    def __init__(self, document, theme_tokens):
        super().__init__(document)

        accent_color = theme_tokens.get("accent-color", "#E63946")
        string_color = theme_tokens.get("success-color", "#A3BE8C")
        muted_color = theme_tokens.get("muted-color", "#888888")
        function_color = theme_tokens.get("function-color", "#88C0D0")

        self.highlighting_rules = []

        # 1. Tags (<div>, </span>, etc.)
        tag_format = QTextCharFormat()
        tag_format.setForeground(QColor(accent_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"</?[a-zA-Z0-9-]+"), tag_format)
        )

        # 2. Attributes (class=, id=, href=)
        attr_format = QTextCharFormat()
        attr_format.setForeground(QColor(function_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[a-zA-Z-]+(?==)"), attr_format)
        )

        # 3. Strings ("..." and '...')
        string_format = QTextCharFormat()
        string_format.setForeground(QColor(string_color))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        # 4. Comments (<!-- ... -->)
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(muted_color))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append(
            (QRegularExpression(r"<!--[\s\S]*?-->"), comment_format)
        )

        # Note: HTML often spans multiple lines for comments, which is tricky in QSyntaxHighlighter.
        # This rule handles single-line comments well.

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)
