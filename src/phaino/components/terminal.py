from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QColor, QFont, QPalette, QTextCursor
from PySide6.QtWidgets import QLineEdit, QPlainTextEdit, QVBoxLayout, QWidget


class TerminalWidget(QWidget):
    def __init__(self, theme_tokens, parent=None):
        super().__init__(parent)
        self.theme_tokens = theme_tokens
        self.last_sent_input = None

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        self.output = QPlainTextEdit()
        self.output.setObjectName("TerminalOutput")
        self.output.setFont(QFont("Fira Code", 13))
        self.output.setUndoRedoEnabled(False)
        self.output.setReadOnly(True)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("TerminalInput")
        self.input_field.setFont(QFont("Fira Code", 13))
        self.input_field.setPlaceholderText("Type input and press Enter...")
        self.input_field.returnPressed.connect(self.send_input)
        self.input_field.hide()

        self.layout.addWidget(self.output)
        self.layout.addWidget(self.input_field)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)

        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_output)
        self.process.finished.connect(self.process_finished)

        self.apply_palette()
        self.append("Terminal ready. Press Ctrl+R to run the current file.\n")

    def apply_palette(self):
        palette = self.palette()
        bg_color = QColor(self.theme_tokens.get("background-color", "#121212"))
        text_color = QColor(self.theme_tokens.get("color", "#E0E0E0"))
        palette.setColor(QPalette.Base, bg_color)
        palette.setColor(QPalette.Text, text_color)
        self.output.setPalette(palette)

        input_palette = self.input_field.palette()
        input_palette.setColor(
            QPalette.Base, QColor(self.theme_tokens.get("surface-color", "#1E1E1E"))
        )
        input_palette.setColor(QPalette.Text, text_color)
        self.input_field.setPalette(input_palette)

    def append(self, text):
        self.output.moveCursor(QTextCursor.End)
        self.output.insertPlainText(text)
        self.output.moveCursor(QTextCursor.End)

    def read_output(self):
        data = (
            self.process.readAllStandardOutput()
            .data()
            .decode("utf-8", errors="replace")
        )

        # If the data is exactly the echo of what we just sent, ignore it
        if self.last_sent_input and data.strip() == self.last_sent_input.strip():
            self.last_sent_input = None
            return

        self.append(data)

    def process_finished(self, exit_code, exit_status):
        self.append(f"\n[Process finished with exit code {exit_code}]\n")
        self.input_field.hide()

    def run_command(self, command_list, working_directory=None):
        self.output.clear()
        self.append(f"> {' '.join(command_list)}\n")

        if working_directory:
            self.process.setWorkingDirectory(working_directory)

        self.process.start(command_list[0], command_list[1:])

        self.input_field.show()
        self.input_field.setFocus()

    def send_input(self):
        text = self.input_field.text()
        if self.process.state() == QProcess.Running:
            # 1. Force a newline in the UI before sending the input
            self.append("\n")

            # 2. Send the input to the process
            self.process.write((text + "\n").encode("utf-8"))

            # 3. Clear the input field
            self.input_field.clear()
