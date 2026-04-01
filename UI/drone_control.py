import socket
import json

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QGroupBox, QTextEdit
)
from PyQt6.QtCore import Qt, QTimer


class DroneControlTab(QWidget):
    def __init__(self):
        super().__init__()

        # =============================
        # UDP CONFIG
        # =============================
        self.ESP_IP = "192.168.1.108"
        self.ESP_PORT = 14550

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # =============================
        # CONTROL STATE (RC VALUES)
        # =============================
        self.roll = 1500
        self.pitch = 1500
        self.yaw = 1500
        self.throttle = 1000
        self.arm = 0

        # =============================
        # UI
        # =============================
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()  # 🔥 force focus

        layout = QVBoxLayout()

        title = QLabel("🎮 Drone Manual Control (UDP)")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(title)

        self.status_box = QGroupBox("Control Status")
        status_layout = QVBoxLayout()

        self.connection_label = QLabel("UDP: READY")
        self.arm_status = QLabel("Drone: DISARMED")
        self.last_command = QLabel("Last Command: None")

        status_layout.addWidget(self.connection_label)
        status_layout.addWidget(self.arm_status)
        status_layout.addWidget(self.last_command)

        self.status_box.setLayout(status_layout)
        layout.addWidget(self.status_box)

        # 🔥 FIX: prevent QTextEdit from stealing keyboard
        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setFocusPolicy(Qt.FocusPolicy.NoFocus)  # 🔥 critical fix
        instructions.setPlainText(
            "Controls:\n"
            "W/S → Pitch\n"
            "A/D → Roll\n"
            "Q/E → Yaw\n"
            "SPACE → Throttle Up\n"
            "SHIFT → Throttle Down\n"
            "R → ARM\n"
            "F → DISARM"
        )
        layout.addWidget(instructions)

        self.setLayout(layout)

        # =============================
        # SEND LOOP (50Hz)
        # =============================
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_udp)
        self.timer.start(20)

    # =============================
    # Focus fix
    # =============================
    def showEvent(self, event):
        self.setFocus()
        super().showEvent(event)

    # =============================
    # KEYBOARD INPUT
    # =============================
    def keyPressEvent(self, event):
        key = event.key()
        cmd = None

        print("KEY PRESSED:", key)  # 🔥 DEBUG

        step = 50

        if key == Qt.Key.Key_W:
            self.pitch = min(2000, self.pitch + step)
            cmd = "PITCH +"
        elif key == Qt.Key.Key_S:
            self.pitch = max(1000, self.pitch - step)
            cmd = "PITCH -"
        elif key == Qt.Key.Key_A:
            self.roll = max(1000, self.roll - step)
            cmd = "ROLL -"
        elif key == Qt.Key.Key_D:
            self.roll = min(2000, self.roll + step)
            cmd = "ROLL +"
        elif key == Qt.Key.Key_Q:
            self.yaw = max(1000, self.yaw - step)
            cmd = "YAW -"
        elif key == Qt.Key.Key_E:
            self.yaw = min(2000, self.yaw + step)
            cmd = "YAW +"
        elif key == Qt.Key.Key_Space:
            self.throttle = min(2000, self.throttle + step)
            cmd = "THROTTLE +"
        elif key == Qt.Key.Key_Shift:
            self.throttle = max(1000, self.throttle - step)
            cmd = "THROTTLE -"
        elif key == Qt.Key.Key_R:
            self.arm = 1
            self.arm_status.setText("Drone: ARMED")
            cmd = "ARM"
        elif key == Qt.Key.Key_F:
            self.arm = 0
            self.arm_status.setText("Drone: DISARMED")
            cmd = "DISARM"

        if cmd:
            self.last_command.setText(f"Last Command: {cmd}")

    # =============================
    # UDP SEND FUNCTION
    # =============================
    def send_udp(self):
        try:
            data = {
                "roll": self.roll,
                "pitch": self.pitch,
                "yaw": self.yaw,
                "throttle": self.throttle,
                "arm": self.arm
            }

            print("Sending:", data)  # 🔥 DEBUG

            message = json.dumps(data).encode()

            self.sock.sendto(message, (self.ESP_IP, self.ESP_PORT))

        except Exception as e:
            self.connection_label.setText(f"UDP ERROR: {e}")