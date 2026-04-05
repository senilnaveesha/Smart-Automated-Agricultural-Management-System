from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame
)
from PyQt6.QtCore import Qt
from components.section_card import SectionCard
from backend.udp_listener import UDPListener   # 🔥 NEW


# 🔹 LEFT PANEL FUNCTION
def create_left_panel():
    panel = QFrame()
    panel.setFixedWidth(250)

    panel.setStyleSheet("""
        QFrame {
            background-color: #2b2b3c;
            border-radius: 10px;
            padding: 15px;
        }
        QLabel {
            color: white;
            font-size: 13px;
        }
    """)

    layout = QVBoxLayout()

    title = QLabel("System Status")
    title.setStyleSheet("font-weight: bold; font-size: 15px;")
    layout.addWidget(title)

    layout.addSpacing(15)

    layout.addWidget(QLabel("Total Sections: 8"))
    layout.addWidget(QLabel("Active Alerts: 2"))
    layout.addWidget(QLabel("System Health: GOOD"))
    layout.addWidget(QLabel("Connectivity: ONLINE"))

    layout.addStretch()

    panel.setLayout(layout)
    return panel


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        # 🔥 MAIN LAYOUT
        main_layout = QHBoxLayout()

        # 🔹 LEFT PANEL
        left_panel = create_left_panel()

        # 🔹 RIGHT SIDE
        right_container = QVBoxLayout()

        # 🔹 TITLE
        title = QLabel("Smart Field Dashboard")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: white;
        """)
        right_container.addWidget(title)

        # 🔹 GRID
        self.grid = QGridLayout()
        self.grid.setSpacing(20)

        self.sections = []

        section_names = [
            "Section A", "Section B", "Section C", "Section D",
            "Section E", "Section F", "Section G", "Section H"
        ]

        row, col = 0, 0

        for name in section_names:
            card = SectionCard(name)
            self.sections.append(card)

            self.grid.addWidget(card, row, col)

            col += 1
            if col == 4:
                col = 0
                row += 1

        right_container.addLayout(self.grid)

        # 🔹 BOTTOM CONTROL BAR
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(15)

        def create_button(text):
            btn = QLabel(text)
            btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
            btn.setStyleSheet("""
                background-color: #2b2b3c;
                padding: 12px;
                border-radius: 8px;
                color: white;
                font-weight: bold;
            """)
            return btn

        controls_layout.addWidget(create_button("Force Pump ON"))
        controls_layout.addWidget(create_button("Force Pump OFF"))
        controls_layout.addWidget(create_button("Auto Mode"))

        right_container.addSpacing(15)
        right_container.addLayout(controls_layout)

        # 🔹 ADD TO MAIN
        main_layout.addWidget(left_panel)
        main_layout.addLayout(right_container)

        self.setLayout(main_layout)

        # 🔥 LOAD TEST DATA (initial UI state)
        self.load_dummy_data()

        # 🔥 START UDP LISTENER (AFTER UI IS READY)
        self.udp = UDPListener(port=5005)
        self.udp.data_received.connect(self.handle_udp_data)
        self.udp.start()

    # 🔥 UDP DATA HANDLER
    def handle_udp_data(self, data):
        print("[UI RECEIVED]", data)

        try:
            section = data.get("section")
            soil = data.get("soil")
            temp = data.get("temp")
            rain = data.get("rain")
            pump = data.get("pump")
            status = data.get("status", "Unknown")

            if not section:
                return

            # Map section letter → index
            index = ord(section.upper()) - ord('A')

            if 0 <= index < len(self.sections):
                self.sections[index].update_data(
                    soil, temp, rain, pump, status
                )

        except Exception as e:
            print("[UI ERROR]", e)

    # 🔥 DUMMY DATA (for testing UI)
    def load_dummy_data(self):
        print("Loading dummy data...")

        demo_data = [
            (45, 30, "No", "OFF", "Healthy"),
            (20, 33, "No", "ON", "Dry"),
            (55, 28, "Light", "OFF", "Optimal"),
            (60, 27, "No", "OFF", "Healthy"),
            (48, 31, "No", "ON", "Healthy"),
            (35, 34, "No", "OFF", "Warning"),
            (25, 35, "No", "ON", "Dry"),
            (70, 26, "No", "OFF", "Optimal"),
        ]

        for card, data in zip(self.sections, demo_data):
            card.update_data(*data)