import subprocess

FORMATTER_MAP = {
    ".py": ["ruff", "format", "-"],
    ".toml": ["taplo", "fmt", "-"],
    ".json": ["prettier", "--parser", "json"],
    ".yaml": ["prettier", "--parser", "yaml"],
    ".yml": ["prettier", "--parser", "yaml"],
    ".md": ["prettier", "--parser", "markdown"],
    ".html": ["prettier", "--parser", "html"],
    ".htm": ["prettier", "--parser", "html"],
    ".js": ["prettier", "--parser", "babel"],
    ".ts": ["prettier", "--parser", "typescript"],
    ".rs": ["rustfmt"],
    ".go": ["gofmt"],
}

FORMATTER_NAMES = {
    ".py": "ruff",
    ".toml": "taplo",
    ".json": "prettier",
    ".yaml": "prettier",
    ".yml": "prettier",
    ".md": "prettier",
    ".html": "prettier",
    ".htm": "prettier",
    ".js": "prettier",
    ".ts": "prettier",
    ".rs": "rustfmt",
    ".go": "gofmt",
}

WARNED_EXTENSIONS = set()


def format_code(ext, source, on_error=None):
    ext = ext.lower()
    command = FORMATTER_MAP.get(ext)
    if not command:
        return source

    try:
        result = subprocess.run(
            command,
            input=source,
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout
    except Exception:
        pass

    if ext not in WARNED_EXTENSIONS:
        WARNED_EXTENSIONS.add(ext)
        formatter_name = FORMATTER_NAMES.get(ext, command[0])
        if on_error:
            on_error(
                f"[Formatter] '{formatter_name}' was not found. "
                f"Install it using your system's package manager to enable "
                f"formatting for {ext} files.\n"
            )
    return source
