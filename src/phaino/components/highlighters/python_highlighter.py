from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class PythonHighlighter(QSyntaxHighlighter):
    keywords = [
        "and",
        "as",
        "assert",
        "async",
        "await",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "False",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "None",
        "nonlocal",
        "not",
        "or",
        "pass",
        "raise",
        "return",
        "True",
        "try",
        "while",
        "with",
        "yield",
    ]

    def __init__(self, document, theme_tokens):
        super().__init__(document)

        accent_color = theme_tokens.get("accent-color")
        muted_color = theme_tokens.get("muted-color")
        string_color = theme_tokens.get("success-color")
        keyword_color = theme_tokens.get("warning-color")
        function_color = theme_tokens.get("function-color")
        class_color = theme_tokens.get("class-color")
        decorator_color = theme_tokens.get("decorator-color")

        self.fstring_format = QTextCharFormat()
        self.fstring_format.setForeground(QColor(accent_color))

        self.highlighting_rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor(keyword_color))
        keyword_format.setFontWeight(QFont.Weight.Bold)
        keyword_pattern = r"\b(" + "|".join(self.keywords) + r")\b"
        self.highlighting_rules.append(
            (QRegularExpression(keyword_pattern), keyword_format)
        )

        builtins = [
            "print",
            "len",
            "range",
            "str",
            "int",
            "float",
            "list",
            "dict",
            "set",
            "tuple",
            "open",
            "file",
            "input",
            "type",
            "isinstance",
        ]
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor(accent_color))
        builtin_pattern = r"\b(" + "|".join(builtins) + r")\b"
        self.highlighting_rules.append(
            (QRegularExpression(builtin_pattern), builtin_format)
        )

        function_format = QTextCharFormat()
        function_format.setForeground(QColor(function_color))
        function_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"(?<=def\s)\w+"), function_format)
        )

        class_format = QTextCharFormat()
        class_format.setForeground(QColor(class_color))
        class_format.setFontWeight(QFont.Weight.Bold)
        self.highlighting_rules.append(
            (QRegularExpression(r"(?<=class\s)\w+"), class_format)
        )

        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor(decorator_color))
        self.highlighting_rules.append((QRegularExpression(r"^@\w+"), decorator_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor(string_color))
        self.highlighting_rules.append((QRegularExpression(r'".*?"'), string_format))
        self.highlighting_rules.append((QRegularExpression(r"'.*?'"), string_format))

        func_call_format = QTextCharFormat()
        func_call_format.setForeground(QColor(function_color))
        self.highlighting_rules.append(
            (
                QRegularExpression(r"\b(?!if\b|while\b|for\b|print\b)\w+(?=\()"),
                func_call_format,
            )
        )

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor(muted_color))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((QRegularExpression(r"#[^\n]*"), comment_format))

        number_format = QTextCharFormat()
        number_format.setForeground(QColor(accent_color))
        self.highlighting_rules.append(
            (QRegularExpression(r"\b[0-9]+\b"), number_format)
        )

    def highlightBlock(self, text):
        for pattern, format in self.highlighting_rules:
            match_iterator = pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), format)

        if 'f"' in text or "f'" in text:
            bracket_pattern = QRegularExpression(r"\{[^}]+\}")
            match_iterator = bracket_pattern.globalMatch(text)
            while match_iterator.hasNext():
                match = match_iterator.next()
                self.setFormat(
                    match.capturedStart(), match.capturedLength(), self.fstring_format
                )
