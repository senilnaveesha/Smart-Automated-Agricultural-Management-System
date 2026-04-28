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
        self.sock = None

    def run(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.settimeout(1.0)

            print(f"[UDP] Listening on {self.host}:{self.port}")

            while self.running:
                try:
                    data, addr = self.sock.recvfrom(4096)
                    message = data.decode().strip()

                    print(f"[UDP RECEIVED:{self.port}] {message}")

                    parsed = json.loads(message)
                    self.data_received.emit(parsed)

                except socket.timeout:
                    continue

                except json.JSONDecodeError:
                    print(f"[UDP ERROR:{self.port}] Invalid JSON:", message)

                except Exception as e:
                    if self.running:
                        print(f"[UDP ERROR:{self.port}]", e)

        except OSError as e:
            print(f"[UDP BIND ERROR:{self.port}] {e}")

        finally:
            if self.sock:
                self.sock.close()
                self.sock = None

    def stop(self):
        self.running = False

        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass

        self.quit()
        self.wait(1000)