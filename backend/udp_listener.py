import socket
import json
from PyQt6.QtCore import QThread, pyqtSignal


class UDPListener(QThread):
    data_received = pyqtSignal(dict)

    def __init__(self, host="0.0.0.0", port=5005):
        super().__init__()
        self.host = host
        self.port = port
        self.running = True

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((self.host, self.port))

        print(f"[UDP] Listening on {self.host}:{self.port}")

        while self.running:
            try:
                data, addr = sock.recvfrom(1024)
                message = data.decode()

                print(f"[UDP RECEIVED] {message}")

                # Parse JSON
                parsed = json.loads(message)

                # Emit to UI
                self.data_received.emit(parsed)

            except Exception as e:
                print("[UDP ERROR]", e)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()