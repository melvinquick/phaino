import os

from .highlighters.html_highlighter import HtmlHighlighter
from .highlighters.json_highlighter import JsonHighlighter
from .highlighters.markdown_highlighter import MarkdownHighlighter
from .highlighters.python_highlighter import PythonHighlighter
from .highlighters.toml_highlighter import TomlHighlighter
from .highlighters.yaml_highlighter import YamlHighlighter

EXTENSION_MAP = {
    ".py": PythonHighlighter,
    ".md": MarkdownHighlighter,
    ".toml": TomlHighlighter,
    ".yaml": YamlHighlighter,
    ".yml": YamlHighlighter,
    ".json": JsonHighlighter,
    ".html": HtmlHighlighter,
    ".htm": HtmlHighlighter,
    ".txt": None,
}


def get_highlighter(file_path, document, theme_tokens):
    if not file_path:
        return None

    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    highlighter_class = EXTENSION_MAP.get(ext)

    if highlighter_class is not None:
        return highlighter_class(document, theme_tokens)

    return None
