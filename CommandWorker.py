from PyQt5.QtCore import QThread, pyqtSignal
import subprocess

class CommandWorker(QThread):
    output_signal = pyqtSignal(str)
    done_signal = pyqtSignal(str)

    def __init__(self, description, command):
        super().__init__()
        self.description = description
        self.command = command

    def run(self):
        # Emit description to signal start of command
        self.output_signal.emit(self.description)
        
        # Run the command
        process = subprocess.Popen(self.command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Capture output in real-time
        while True:
            line = process.stdout.readline()
            if not line:
                break
            self.output_signal.emit(line.strip())  # Emit each line to be logged in the GUI

        process.wait()  # Wait for process to complete
        # Emit result based on return code
        if process.returncode == 0:
            self.done_signal.emit(f"{self.description}: OK")
        else:
            self.done_signal.emit(f"{self.description}: FAIL")
