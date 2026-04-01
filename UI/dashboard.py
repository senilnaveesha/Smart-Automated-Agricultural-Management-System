from drone_control import DroneControlTab
import sys
from dataclasses import dataclass
from datetime import datetime

import requests
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTabWidget, QGroupBox, QPushButton, QTextEdit


)

# ----------------------------
# Data models
# ----------------------------
@dataclass
class SensorSnapshot:
    soil1_raw: int
    soil2_raw: int
    rain: bool
    pump_on: bool
    updated_at: datetime
    connectivity: str
    node_id: str = "node01"

    # Optional / future
    temperature: float | None = None
    humidity: float | None = None


# ----------------------------
# Data source: Laptop FastAPI (ground station)
# ----------------------------
class LaptopAPIDataSource:
    def __init__(self, base_url="http://127.0.0.1:8000", node_id="node01"):
        self.base_url = base_url.rstrip("/")
        self.node_id = node_id

    def get_latest(self) -> SensorSnapshot:
        r = requests.get(
            f"{self.base_url}/api/v1/nodes/{self.node_id}/latest",
            timeout=1.5
        )
        r.raise_for_status()
        data = r.json()

        return SensorSnapshot(
            soil1_raw=int(data["soil1_raw"]),
            soil2_raw=int(data["soil2_raw"]),
            rain=bool(data["rain"]),
            pump_on=bool(data["pump_on"]),
            updated_at=datetime.fromtimestamp(int(data["received_at"])),
            connectivity="WIFI (LOCAL)",
            node_id=self.node_id,
            temperature=data.get("temperature", None),
            humidity=data.get("humidity", None),
        )

    def set_pump(self, state: str) -> None:
        """
        state: "on" | "off" | "auto"
        Requires the FastAPI server to implement:
          POST /api/v1/nodes/{node_id}/command  with JSON body {"pump": "on/off/auto"}
        """
        r = requests.post(
            f"{self.base_url}/api/v1/nodes/{self.node_id}/command",
            json={"pump": state},
            timeout=1.5
        )
        r.raise_for_status()


# ----------------------------
# Dashboard UI
# ----------------------------
class DashboardTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        # Top cards row
        cards_row = QHBoxLayout()

        # Repurpose cards for what we have NOW
        self.soil1_label = self._make_card("Soil Sensor 1 (RAW)", "--")
        self.soil2_label = self._make_card("Soil Sensor 2 (RAW)", "--")
        self.temp_label = self._make_card("Temperature (later)", "--")
        self.rain_label = self._make_card("Rain", "--")
        self.pump_label = self._make_card("Pump", "--")

        cards_row.addWidget(self.soil1_label["box"])
        cards_row.addWidget(self.soil2_label["box"])
        cards_row.addWidget(self.temp_label["box"])
        cards_row.addWidget(self.rain_label["box"])
        cards_row.addWidget(self.pump_label["box"])

        layout.addLayout(cards_row)

        # Status + Alerts
        status_row = QHBoxLayout()

        self.status_box = QGroupBox("System Status")
        status_layout = QVBoxLayout()

        self.connectivity_text = QLabel("Connectivity: --")
        self.last_update_text = QLabel("Last update: --")
        self.node_text = QLabel("Node: --")
        self.health_text = QLabel("Health: --")  # OK / NO DATA / ERROR

        status_layout.addWidget(self.node_text)
        status_layout.addWidget(self.connectivity_text)
        status_layout.addWidget(self.last_update_text)
        status_layout.addWidget(self.health_text)

        self.status_box.setLayout(status_layout)

        self.alerts_box = QGroupBox("Alerts / Logs")
        alerts_layout = QVBoxLayout()
        self.alerts_text = QTextEdit()
        self.alerts_text.setReadOnly(True)
        self.alerts_text.setPlaceholderText("Waiting for data...")
        alerts_layout.addWidget(self.alerts_text)
        self.alerts_box.setLayout(alerts_layout)

        status_row.addWidget(self.status_box, 1)
        status_row.addWidget(self.alerts_box, 2)

        layout.addLayout(status_row)

        # Manual quick controls
        controls_row = QHBoxLayout()
        self.btn_force_on = QPushButton("Force Pump ON")
        self.btn_force_off = QPushButton("Force Pump OFF")
        self.btn_auto = QPushButton("Auto Mode")
        controls_row.addWidget(self.btn_force_on)
        controls_row.addWidget(self.btn_force_off)
        controls_row.addWidget(self.btn_auto)
        layout.addLayout(controls_row)

        self.setLayout(layout)

    def _make_card(self, title: str, value: str):
        box = QGroupBox(title)
        v = QVBoxLayout()
        label = QLabel(value)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("font-size: 18px; font-weight: 600;")
        v.addWidget(label)
        box.setLayout(v)
        box.setMinimumWidth(180)
        return {"box": box, "label": label}

    def set_health(self, text: str):
        self.health_text.setText(f"Health: {text}")

    def show_error(self, msg: str):
        self.set_health("ERROR")
        self.alerts_text.setPlainText(f"❌ {msg}")

    def show_waiting(self):
        self.set_health("NO DATA")
        self.alerts_text.setPlainText("Waiting for first sensor payload...")

    def update_view(self, snap: SensorSnapshot):
        self.node_text.setText(f"Node: {snap.node_id}")
        self.soil1_label["label"].setText(f"{snap.soil1_raw}")
        self.soil2_label["label"].setText(f"{snap.soil2_raw}")

        # temperature card (optional / later)
        if snap.temperature is None:
            self.temp_label["label"].setText("--")
        else:
            self.temp_label["label"].setText(f"{snap.temperature:.1f} °C")

        self.rain_label["label"].setText("YES" if snap.rain else "NO")
        self.pump_label["label"].setText("ON" if snap.pump_on else "OFF")

        self.connectivity_text.setText(f"Connectivity: {snap.connectivity}")
        self.last_update_text.setText(f"Last update: {snap.updated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        self.set_health("OK")

        # Alerts (prototype rules using RAW)
        alerts = []

        # These raw thresholds are placeholders (you'll calibrate later)
        # ESP32 ADC range: 0..4095
        if snap.soil1_raw > 3500 and not snap.rain:
            alerts.append("⚠ Soil1 looks DRY (raw high) → irrigation may be needed soon.")
        if snap.soil2_raw > 3500 and not snap.rain:
            alerts.append("⚠ Soil2 looks DRY (raw high) → irrigation may be needed soon.")
        if snap.rain:
            alerts.append("ℹ Rain detected → irrigation should be blocked.")

        self.alerts_text.setPlainText("\n".join(alerts) if alerts else "No active alerts.")


# ----------------------------
# Main window
# ----------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Agriculture Desktop App (Prototype)")
        self.resize(1100, 600)

        self.tabs = QTabWidget()
        self.dashboard = DashboardTab()

        self.tabs.addTab(self.dashboard, "Dashboard")
        self.tabs.addTab(QLabel("Sensors & Graphs (Coming next)"), "Sensors")
        self.tabs.addTab(QLabel("Disease Heatmap (Coming next)"), "Disease Map")
        self.tabs.addTab(QLabel("Manual Controls (Coming next)"), "Controls")
        self.drone_control = DroneControlTab()
        self.tabs.addTab(self.drone_control, "Drone Control")

        self.setCentralWidget(self.tabs)

        self.data_source = LaptopAPIDataSource(base_url="http://127.0.0.1:8000", node_id="node01")

        # Buttons -> commands (server must implement /command)
        self.dashboard.btn_force_on.clicked.connect(lambda: self.send_pump_command("on"))
        self.dashboard.btn_force_off.clicked.connect(lambda: self.send_pump_command("off"))
        self.dashboard.btn_auto.clicked.connect(lambda: self.send_pump_command("auto"))

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(1000)

        self._had_any_data = False

    def refresh_data(self):
        try:
            snap = self.data_source.get_latest()
            self.dashboard.update_view(snap)
            self._had_any_data = True
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 404:
                self.dashboard.show_waiting()
            else:
                self.dashboard.show_error(f"HTTP error: {e}")
        except Exception as e:
            if not self._had_any_data:
                self.dashboard.show_waiting()
            else:
                self.dashboard.show_error(f"Connection error: {e}")

    def send_pump_command(self, state: str):
        try:
            self.data_source.set_pump(state)
            self.dashboard.alerts_text.setPlainText(f"✅ Command sent: pump={state}")
        except Exception as e:
            self.dashboard.show_error(f"Failed to send command: {e}")


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()