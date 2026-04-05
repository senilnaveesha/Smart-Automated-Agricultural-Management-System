from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt


class SectionCard(QFrame):
    def __init__(self, section_name="Section A"):
        super().__init__()

        self.setMinimumSize(220, 160)

        # 🔥 Base Style
        self.setStyleSheet("""
            QFrame {
                background-color: #2b2b3c;
                border-radius: 12px;
                padding: 10px;
            }
            QLabel {
                color: white;
            }
        """)

        main_layout = QVBoxLayout()

        # 🔹 HEADER
        header = QHBoxLayout()
        self.title = QLabel(f"🌱 {section_name}")
        self.title.setStyleSheet("font-weight: bold; font-size: 14px;")
        header.addWidget(self.title)
        header.addStretch()

        # 🔹 ROW 1 (Soil + Temp)
        self.soil = QLabel("💧 Soil: --")
        self.temp = QLabel("🌡 --°C")

        row1 = QHBoxLayout()
        row1.addWidget(self.soil)
        row1.addStretch()
        row1.addWidget(self.temp)

        # 🔹 ROW 2 (Rain + Pump)
        self.rain = QLabel("🌧 Rain: --")
        self.pump = QLabel("⚙ Pump: --")

        row2 = QHBoxLayout()
        row2.addWidget(self.rain)
        row2.addStretch()
        row2.addWidget(self.pump)

        # 🔹 STATUS BAR
        self.status = QLabel("Status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setFixedHeight(28)

        # Layout assembly
        main_layout.addLayout(header)
        main_layout.addSpacing(8)
        main_layout.addLayout(row1)
        main_layout.addLayout(row2)
        main_layout.addStretch()
        main_layout.addWidget(self.status)

        self.setLayout(main_layout)

    # 🔥 DATA UPDATE METHOD
    def update_data(self, soil, temp, rain, pump, status):
        self.soil.setText(f"💧 Soil: {soil}%")
        self.temp.setText(f"🌡 {temp}°C")
        self.rain.setText(f"🌧 {rain}")
        self.pump.setText(f"⚙ {pump}")

        status_lower = status.lower()

        # 🔥 STATUS COLORS + BACKGROUND BAR
        if status_lower == "healthy":
            self.status.setText("🟢 Healthy")
            self.status.setStyleSheet("""
                background-color: #1f5c3a;
                color: #00ff9d;
                border-radius: 6px;
                font-weight: bold;
            """)

        elif status_lower == "dry":
            self.status.setText("🟡 Dry Soil")
            self.status.setStyleSheet("""
                background-color: #5c4a1f;
                color: #ffcc00;
                border-radius: 6px;
                font-weight: bold;
            """)

        elif status_lower == "warning":
            self.status.setText("⚠ Warning")
            self.status.setStyleSheet("""
                background-color: #5c2f1f;
                color: orange;
                border-radius: 6px;
                font-weight: bold;
            """)

        elif status_lower == "optimal":
            self.status.setText("🟢 Optimal")
            self.status.setStyleSheet("""
                background-color: #1f5c3a;
                color: #00ff9d;
                border-radius: 6px;
                font-weight: bold;
            """)

        else:
            self.status.setText(f"⚪ {status}")
            self.status.setStyleSheet("""
                background-color: #444;
                color: white;
                border-radius: 6px;
            """)