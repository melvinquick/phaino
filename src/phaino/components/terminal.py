from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QColor, QFont, QPalette, QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


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

        bottom_bar = QHBoxLayout()
        bottom_bar.setContentsMargins(0, 0, 0, 0)
        bottom_bar.setSpacing(0)

        self.input_field = QLineEdit()
        self.input_field.setObjectName("TerminalInput")
        self.input_field.setFont(QFont("Fira Code", 13))
        self.input_field.setPlaceholderText("Type input and press Enter...")
        self.input_field.returnPressed.connect(self.send_input)

        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("TerminalStopButton")
        self.btn_stop.setFixedWidth(60)
        self.btn_stop.clicked.connect(self.stop_process)
        self.btn_stop.setEnabled(False)

        bottom_bar.addWidget(self.input_field)
        bottom_bar.addWidget(self.btn_stop)

        self.layout.addWidget(self.output)
        self.layout.addLayout(bottom_bar)

        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.read_output)
        self.process.readyReadStandardError.connect(self.read_output)
        self.process.finished.connect(self.process_finished)
        self.process.errorOccurred.connect(self.process_error)

        self.apply_palette()
        self.append("Terminal ready. Press Ctrl+R to run the current file.\n")

    def apply_palette(self):
        palette = self.palette()
        bg_color = QColor(self.theme_tokens.get("background-color"))
        text_color = QColor(self.theme_tokens.get("color"))
        palette.setColor(QPalette.Base, bg_color)
        palette.setColor(QPalette.Text, text_color)
        self.output.setPalette(palette)

        input_palette = self.input_field.palette()
        input_palette.setColor(
            QPalette.Base, QColor(self.theme_tokens.get("surface-color"))
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
        if self.last_sent_input and data.strip() == self.last_sent_input.strip():
            self.last_sent_input = None
            return
        self.append(data)

    def process_finished(self, exit_code, exit_status):
        self.append(f"\n[Process finished with exit code {exit_code}]\n")
        self.btn_stop.setEnabled(False)
        self.input_field.clear()

    def process_error(self, error):
        if error == QProcess.FailedToStart:
            self.append(
                "\n[ERROR] Failed to start the process. The file may not be "
                "executable, or its shebang line may be invalid.\n"
                "Try running `chmod +x <filename>` in a terminal.\n"
            )
            self.btn_stop.setEnabled(False)
        elif error == QProcess.Crashed:
            pass
        else:
            self.append(f"\n[Process error: {error}]\n")
            self.btn_stop.setEnabled(False)

    def run_command(self, command_list, working_directory=None):
        self.output.clear()
        self.append(f"> {' '.join(command_list)}\n")

        if working_directory:
            self.process.setWorkingDirectory(working_directory)

        self.btn_stop.setEnabled(True)
        self.process.start(command_list[0], command_list[1:])

    def stop_process(self):
        if self.process.state() == QProcess.Running:
            self.process.kill()
            self.append("\n[Process terminated by user]\n")
        else:
            self.append("\n[No running process to stop]\n")
            self.btn_stop.setEnabled(False)

    def send_input(self):
        text = self.input_field.text()
        if self.process.state() == QProcess.Running:
            self.append("\n")
            self.process.write((text + "\n").encode("utf-8"))
            self.input_field.clear()
