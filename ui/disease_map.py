import os
import json

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFrame
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl

from backend.map_bridge import MapBridge
from backend.path_planner import generate_grid_path


class DiseaseMapPage(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()

        # =========================
        # 🗺️ MAP SECTION
        # =========================
        map_container = QFrame()
        map_container.setFrameShape(QFrame.Shape.StyledPanel)
        map_layout = QVBoxLayout()

        title = QLabel("🗺️ Field Selection")
        map_layout.addWidget(title)

        # 🌍 Map View
        self.map_view = QWebEngineView()

        # 🔥 Enable WebEngine settings
        settings = self.map_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, True)

        # =========================
        # 🔥 WebChannel Bridge
        # =========================
        self.bridge = MapBridge()

        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)

        self.map_view.page().setWebChannel(self.channel)

        # =========================
        # 📄 Load Map
        # =========================
        file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "map.html")
        print("Map Path:", file_path)

        self.map_view.setUrl(QUrl.fromLocalFile(file_path))

        # 🔥 LOAD FLAG (VERY IMPORTANT)
        self.page_loaded = False
        self.map_view.loadFinished.connect(self.on_load_finished)

        map_layout.addWidget(self.map_view)
        map_container.setLayout(map_layout)
        map_container.setMinimumHeight(400)

        main_layout.addWidget(map_container)

        # =========================
        # 🎛️ CONTROLS
        # =========================
        control_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Clear Field")
        self.start_btn = QPushButton("Start Scan")

        control_layout.addWidget(self.clear_btn)
        control_layout.addWidget(self.start_btn)

        main_layout.addLayout(control_layout)

        # 🔘 BUTTONS
        self.clear_btn.clicked.connect(self.clear_field)
        self.start_btn.clicked.connect(self.start_scan)

        # =========================
        # 📊 OUTPUT
        # =========================
        self.output_label = QLabel("📊 Disease map will appear here...")
        main_layout.addWidget(self.output_label)

        self.setLayout(main_layout)

    # =========================
    # ✅ PAGE LOADED
    # =========================
    def on_load_finished(self):
        print("✅ Map fully loaded")
        self.page_loaded = True

    # =========================
    # 🧹 CLEAR FIELD
    # =========================
    def clear_field(self):
        print("🧹 Clearing field...")

        if self.page_loaded:
            self.map_view.page().runJavaScript("clearField();")

        self.bridge.coordinates = []
        self.output_label.setText("📊 Field cleared.")

    # =========================
    # 🚁 START SCAN
    # =========================
    def start_scan(self):
        print("🚁 Start Scan pressed")

        coords = self.bridge.coordinates

        # Validation
        if not coords or len(coords) < 3:
            self.output_label.setText("⚠️ Please select a valid field (at least 3 points).")
            print("❌ Not enough points")
            return

        print("✅ Field ready:", coords)

        try:
            # 🔥 Generate path
            path = generate_grid_path(coords, spacing=0.00005)

            print("🛣️ Generated Path:", path[:10], "...")

            # 🔥 CRITICAL FIX — SEND TO JS
            if self.page_loaded:
                js_code = f"drawPath({json.dumps(path)})"
                self.map_view.page().runJavaScript(js_code)
                print("📡 Path sent to map")
            else:
                print("⚠️ Map not ready yet")

            self.output_label.setText(f"🚁 Path generated with {len(path)} points")

        except Exception as e:
            print("❌ Path generation error:", e)
            self.output_label.setText("❌ Error generating path")