import os
import json
import threading

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QScrollArea, QPlainTextEdit
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings, QWebEnginePage
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtCore import QUrl, QTimer, pyqtSignal, Qt
from PyQt6.QtGui import QPixmap

from backend.map_bridge import MapBridge
from backend.path_planner import generate_grid_path
from backend.udp_listener import UDPListener
from backend.drone_comm.drone_controller import DroneController
from backend.report_generator import (
    generate_disease_summary,
    format_summary_for_display,
    prettify_disease_name,
)
from simulation.fake_scan_runner import run_fake_scan


class DebugPage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        print(f"[JS:{level.name}] {sourceID}:{lineNumber} - {message}")


class DiseaseMapPage(QWidget):
    point_scanned = pyqtSignal(dict)
    scan_completed = pyqtSignal(list)
    scan_failed = pyqtSignal(str)

    def __init__(self, ai_advisor=None):
        super().__init__()

        self.ai_advisor = ai_advisor
        self.page_loaded = False
        self.heatmap_loaded = False
        self.scan_results = []
        self.drone_path_status = None
        self.project_root = os.path.dirname(os.path.dirname(__file__))

        self.main_map_file = os.path.join(self.project_root, "map_main.html")
        self.heat_map_file = os.path.join(self.project_root, "map_heat.html")

        # =========================
        # 🚁 DRONE COMMAND CONTROLLER
        # =========================
        self.drone_controller = DroneController(
            drone_ip="192.168.1.200",
            command_port=5007
        )

        main_layout = QVBoxLayout()

        # =========================
        # 🗺️ TOP MAP
        # =========================
        map_container = QFrame()
        map_layout = QVBoxLayout()

        title = QLabel("🗺️ Field Selection")
        map_layout.addWidget(title)

        self.map_view = QWebEngineView()
        self.map_view.setPage(DebugPage(self))
        self._configure_webview(self.map_view)

        self.bridge = MapBridge()
        self.channel = QWebChannel()
        self.channel.registerObject("bridge", self.bridge)
        self.map_view.page().setWebChannel(self.channel)

        self.map_view.setUrl(QUrl.fromLocalFile(self.main_map_file))
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

        self.clear_btn.clicked.connect(self.clear_field)
        self.start_btn.clicked.connect(self.start_scan)

        main_layout.addLayout(control_layout)

        # =========================
        # 📜 SCROLLABLE AREA
        # =========================
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout()

        # =========================
        # 🔥 HEATMAP
        # =========================
        scroll_layout.addWidget(QLabel("🔥 Disease Heatmap"))

        self.heatmap_view = QWebEngineView()
        self.heatmap_view.setPage(DebugPage(self))
        self._configure_webview(self.heatmap_view)
        self.heatmap_view.setMinimumHeight(300)

        self.heatmap_view.setUrl(QUrl.fromLocalFile(self.heat_map_file))
        self.heatmap_view.loadFinished.connect(self.on_heatmap_loaded)

        scroll_layout.addWidget(self.heatmap_view)

        # =========================
        # 📊 STATUS
        # =========================
        self.output_label = QLabel("📊 Waiting for scan...")
        scroll_layout.addWidget(self.output_label)

        # =========================
        # 🧾 REPORT BOX
        # =========================
        scroll_layout.addWidget(QLabel("🧾 Disease Monitoring Report"))

        self.report_box = QPlainTextEdit()
        self.report_box.setReadOnly(True)
        self.report_box.setPlaceholderText(
            "Disease report will appear here after scan completion..."
        )
        self.report_box.setMinimumHeight(240)
        scroll_layout.addWidget(self.report_box)

        # =========================
        # 🖼️ MOST COMMON DISEASE IMAGE
        # =========================
        scroll_layout.addWidget(QLabel("🖼️ Most Common Disease Example"))

        self.main_disease_name_label = QLabel("No disease example available.")
        scroll_layout.addWidget(self.main_disease_name_label)

        self.main_disease_image = QLabel()
        self.main_disease_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.main_disease_image.setMinimumHeight(220)
        self.main_disease_image.setStyleSheet(
            "border: 1px solid #555; background-color: #2b2b3c; padding: 8px;"
        )
        scroll_layout.addWidget(self.main_disease_image)

        # =========================
        # 🧬 ALL DETECTED DISEASE IMAGES
        # =========================
        scroll_layout.addWidget(QLabel("🧬 Detected Disease Image Samples"))

        self.disease_image_container = QWidget()
        self.disease_image_layout = QVBoxLayout()
        self.disease_image_container.setLayout(self.disease_image_layout)
        scroll_layout.addWidget(self.disease_image_container)

        scroll_content.setLayout(scroll_layout)
        scroll.setWidget(scroll_content)

        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        # =========================
        # SIGNALS
        # =========================
        self.point_scanned.connect(self.on_point_scanned)
        self.scan_completed.connect(self.on_scan_completed)
        self.scan_failed.connect(self.on_scan_failed)

        # =========================
        # 📡 UDP LISTENER (DRONE GPS + STATUS)
        # =========================
        self.udp_listener = UDPListener(port=5006)
        self.udp_listener.data_received.connect(self.handle_udp_data)
        self.udp_listener.start()

    # =========================
    # WEBVIEW CONFIG
    # =========================
    def _configure_webview(self, webview: QWebEngineView):
        settings = webview.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)

    # =========================
    # LOAD EVENTS
    # =========================
    def on_load_finished(self, ok):
        self.page_loaded = ok
        print("✅ Main map loaded" if ok else "❌ Main map failed to load")

    def on_heatmap_loaded(self, ok):
        self.heatmap_loaded = ok
        print("✅ Heatmap view loaded" if ok else "❌ Heatmap view failed to load")

    # =========================
    # HELPERS
    # =========================
    def run_js_main(self, js_code: str):
        if self.page_loaded:
            self.map_view.page().runJavaScript(js_code)
        else:
            print("⚠️ Main map JS skipped: page not ready")

    def run_js_heat(self, js_code: str):
        if self.heatmap_loaded:
            self.heatmap_view.page().runJavaScript(js_code)
        else:
            print("⚠️ Heatmap JS skipped: page not ready")

    def clear_image_previews(self):
        self.main_disease_name_label.setText("No disease example available.")
        self.main_disease_image.clear()
        self.main_disease_image.setText("No image")

        while self.disease_image_layout.count():
            item = self.disease_image_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def resolve_image_path(self, image_path: str) -> str:
        if not image_path:
            return ""

        if os.path.isabs(image_path):
            return image_path

        return os.path.join(self.project_root, image_path)

    def set_preview_image(self, label_widget: QLabel, image_path: str, width=320, height=220):
        resolved = self.resolve_image_path(image_path)

        if not resolved or not os.path.exists(resolved):
            label_widget.clear()
            label_widget.setText("Image not found")
            return

        pixmap = QPixmap(resolved)
        if pixmap.isNull():
            label_widget.clear()
            label_widget.setText("Failed to load image")
            return

        scaled = pixmap.scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        label_widget.setPixmap(scaled)

    def populate_disease_images(self, summary: dict):
        self.clear_image_previews()

        disease_examples = summary.get("disease_examples", {})
        most_common = summary.get("most_common_disease", "None")

        if most_common != "None" and most_common in disease_examples:
            self.main_disease_name_label.setText(
                f"Most Common Disease: {prettify_disease_name(most_common)}"
            )
            self.set_preview_image(self.main_disease_image, disease_examples[most_common])
        else:
            self.main_disease_name_label.setText("No disease example available.")
            self.main_disease_image.setText("No image")

        if not disease_examples:
            empty_label = QLabel("No disease image samples available.")
            self.disease_image_layout.addWidget(empty_label)
            return

        for disease, image_path in disease_examples.items():
            card = QFrame()
            card.setStyleSheet(
                "QFrame { border: 1px solid #555; background-color: #2b2b3c; padding: 8px; }"
            )

            card_layout = QVBoxLayout(card)

            disease_label = QLabel(f"{prettify_disease_name(disease)}")
            disease_label.setStyleSheet("font-weight: bold;")
            card_layout.addWidget(disease_label)

            image_label = QLabel()
            image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image_label.setMinimumHeight(180)
            self.set_preview_image(image_label, image_path, width=280, height=180)
            card_layout.addWidget(image_label)

            path_label = QLabel(f"Image: {image_path}")
            path_label.setWordWrap(True)
            path_label.setStyleSheet("color: #bbbbbb;")
            card_layout.addWidget(path_label)

            self.disease_image_layout.addWidget(card)

    def clear_field(self):
        if self.page_loaded:
            self.run_js_main("clearField();")

        if self.heatmap_loaded:
            self.run_js_heat("clearHeatmap();")

        self.bridge.coordinates = []
        self.scan_results = []
        self.drone_path_status = None
        self.report_box.clear()
        self.clear_image_previews()
        self.output_label.setText("📊 Field cleared.")

    # =========================
    # SIGNAL HANDLERS
    # =========================
    def on_point_scanned(self, point):
        self.scan_results.append(point)

        js_move = f"moveDrone([{point['lat']}, {point['lon']}]);"
        js_draw = f"drawScanPoints([{json.dumps(point)}]);"

        self.run_js_main(js_move)
        self.run_js_main(js_draw)

    def on_scan_completed(self, points):
        print("✅ on_scan_completed received on UI thread")
        self.output_label.setText("🧪 Rendering heatmap and generating report...")

        try:
            summary = generate_disease_summary(points)

            if self.ai_advisor is not None:
                self.ai_advisor.update_disease_context(summary)

            report_text = format_summary_for_display(summary)
            self.report_box.setPlainText(report_text)
            self.populate_disease_images(summary)

        except Exception as report_error:
            print("❌ Report generation error:", report_error)
            self.report_box.setPlainText("❌ Failed to generate disease report.")
            self.clear_image_previews()

        QTimer.singleShot(300, lambda: self.send_heatmap_safe(points))
        QTimer.singleShot(500, lambda: self.output_label.setText("✅ Scan Complete + Report Ready"))

    def on_scan_failed(self, message):
        print("❌ on_scan_failed:", message)
        self.output_label.setText(message)

    # =========================
    # 📡 UDP HANDLER
    # =========================
    def handle_udp_data(self, data):
        try:
            msg_type = data.get("type")

            if msg_type == "gps":
                lat = data.get("lat")
                lon = data.get("lon")

                if lat is None or lon is None:
                    return

                js = f"updateDronePosition({lat}, {lon});"
                self.run_js_main(js)

            elif msg_type == "status":
                level = data.get("level", "info")
                message = data.get("message", "No message")

                self.drone_path_status = {
                    "level": level,
                    "message": message
                }

                print(f"📡 Drone status [{level}]: {message}")

                if level == "error":
                    self.output_label.setText(f"❌ Drone: {message}")
                elif level == "ok":
                    self.output_label.setText(f"✅ Drone: {message}")
                else:
                    self.output_label.setText(f"ℹ️ Drone: {message}")

        except Exception as e:
            print("❌ UDP handling error:", e)

    # =========================
    # HEATMAP SEND
    # =========================
    def send_heatmap_safe(self, points):
        js_points = json.dumps(points)

        def try_send():
            if not self.heatmap_loaded:
                print("⏳ Waiting for heatmap view load...")
                QTimer.singleShot(200, try_send)
                return

            check_js = """
            (() => {
                return JSON.stringify({
                    readyState: document.readyState,
                    hasLeaflet: typeof window.L !== 'undefined',
                    hasHeatLayer: typeof window.L !== 'undefined' && typeof window.L.heatLayer === 'function',
                    hasDrawHeatmap: typeof window.drawHeatmap === 'function',
                    hasMap: !!window.map,
                    leafletReady: !!window.leafletReady
                });
            })();
            """

            def after_check(result):
                if isinstance(result, str):
                    try:
                        result = json.loads(result)
                    except Exception:
                        print("❌ Failed to parse JS result:", result)
                        result = None

                print("🔥 Heatmap page status:", result)

                if (
                    result
                    and result.get("hasLeaflet")
                    and result.get("hasHeatLayer")
                    and result.get("hasDrawHeatmap")
                    and result.get("hasMap")
                    and result.get("leafletReady")
                ):
                    print("✅ Heatmap page ready, sending heatmap data")
                    self.run_js_heat(f"drawHeatmap({js_points});")
                else:
                    print("⏳ Heatmap page not fully ready, retrying...")
                    QTimer.singleShot(200, try_send)

            self.heatmap_view.page().runJavaScript(check_js, after_check)

        QTimer.singleShot(0, try_send)

    # =========================
    # START SCAN
    # =========================
    def start_scan(self):
        coords = self.bridge.coordinates

        if not coords or len(coords) < 3:
            self.output_label.setText("⚠️ Select a valid field")
            return

        if not self.page_loaded:
            self.output_label.setText("⚠️ Main map is not ready")
            print("❌ Main map not ready")
            return

        try:
            path = generate_grid_path(coords, spacing=0.00005, sample_step=0.00002)

            if not path:
                self.output_label.setText("⚠️ Could not generate scan path")
                print("❌ Empty path generated")
                return

            self.scan_results = []
            self.drone_path_status = None
            self.report_box.clear()
            self.clear_image_previews()

            self.run_js_main(f"drawPath({json.dumps(path)});")
            self.run_js_main(f"initDrone({json.dumps(path[0])});")

            # =========================
            # 📡 SEND PATH TO ESP32 RECEIVER
            # =========================
            try:
                sent_count = self.drone_controller.send_path(path, step=25, delay=0.08)
                print(f"📡 Sent {sent_count} waypoints to drone receiver")

                self.output_label.setText(
                    f"📡 Path sent to drone receiver ({sent_count} waypoints). Waiting for drone status..."
                )

                self.drone_controller.start_scan()
                print("📡 Sent START_SCAN command to drone receiver")

            except Exception as drone_error:
                print("❌ Drone command send error:", drone_error)
                self.output_label.setText("⚠️ Path generated, but failed to send to drone receiver.")

            self.output_label.setText("🚁 Scanning...")

            def run_and_finalize():
                try:
                    local_results = []

                    def callback_and_store(point):
                        local_results.append(point)
                        self.point_scanned.emit(point)

                    run_fake_scan(path, callback=callback_and_store, delay=0.03)

                    print("🔥 Scan complete, preparing heatmap...")
                    self.scan_completed.emit(local_results)

                except Exception as scan_error:
                    print("❌ Scan thread error:", scan_error)
                    self.scan_failed.emit("❌ Scan failed during execution")

            threading.Thread(target=run_and_finalize, daemon=True).start()

        except Exception as e:
            print("❌ Error:", e)
            self.output_label.setText("❌ Scan failed")

    # =========================
    # CLOSE EVENT
    # =========================
    def closeEvent(self, event):
        if hasattr(self, "udp_listener"):
            self.udp_listener.stop()

        if hasattr(self, "drone_controller"):
            self.drone_controller.close()

        event.accept()