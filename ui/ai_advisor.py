import html
import threading

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextBrowser,
    QLineEdit, QPushButton, QLabel, QFrame
)

from backend.ai_engine import get_ai_response


class AIAdvisorPage(QWidget):
    ai_response_ready = pyqtSignal(dict)
    ai_error_ready = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        self.setObjectName("root")
        self.setStyleSheet("""
            QWidget#root {
                background-color: #1f2230;
                color: #e8ecf1;
            }

            QFrame#headerCard, QFrame#sensorCard, QFrame#inputCard {
                background-color: #2a2f3f;
                border: 1px solid #3a4154;
                border-radius: 18px;
            }

            QLabel#titleLabel {
                font-size: 22px;
                font-weight: 700;
                color: #f3f6fb;
            }

            QLabel#subtitleLabel {
                font-size: 12px;
                color: #aab4c3;
            }

            QLabel#sensorTitle {
                font-size: 13px;
                font-weight: 600;
                color: #d9e2ef;
            }

            QLabel#sensorData {
                font-size: 13px;
                color: #9ee6b0;
                padding: 4px 0px;
            }

            QTextBrowser {
                background-color: #202433;
                border: 1px solid #3a4154;
                border-radius: 18px;
                padding: 14px;
                font-size: 14px;
                color: #edf2f7;
            }

            QLineEdit {
                background-color: transparent;
                border: none;
                color: #f3f6fb;
                font-size: 14px;
                padding: 10px;
            }

            QLineEdit::placeholder {
                color: #8e99ab;
            }

            QPushButton {
                background-color: #4f8cff;
                color: white;
                border: none;
                border-radius: 14px;
                padding: 10px 18px;
                font-size: 13px;
                font-weight: 600;
            }

            QPushButton:hover {
                background-color: #6a9dff;
            }

            QPushButton:pressed {
                background-color: #3d79eb;
            }

            QPushButton:disabled {
                background-color: #5a6275;
                color: #c7cfdb;
            }

            QLabel#statusLabel {
                font-size: 12px;
                color: #aab4c3;
                padding-left: 6px;
            }
        """)

        self.sensor_data = {
            "soil": 0,
            "temp": 0,
            "rain": "No",
            "disease": "None",
            "crop": "Tea"
        }

        self.disease_summary = None

        self.ai_response_ready.connect(self.handle_ai_response)
        self.ai_error_ready.connect(self.handle_ai_error)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(18, 18, 18, 18)
        self.main_layout.setSpacing(14)

        self.build_header()
        self.build_sensor_card()
        self.build_chat_area()
        self.build_input_area()

        self.setLayout(self.main_layout)

        self.append_ai_message(
            "Hello! I am your agricultural AI advisor. "
            "Ask me about watering, temperature stress, rainfall impact, crop health, or disease scan results."
        )

    def build_header(self):
        header_card = QFrame()
        header_card.setObjectName("headerCard")

        layout = QVBoxLayout(header_card)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(4)

        title = QLabel("🌱 AI Crop Advisor")
        title.setObjectName("titleLabel")

        subtitle = QLabel("Offline field assistant for tea crop decision support")
        subtitle.setObjectName("subtitleLabel")

        layout.addWidget(title)
        layout.addWidget(subtitle)

        self.main_layout.addWidget(header_card)

    def build_sensor_card(self):
        sensor_card = QFrame()
        sensor_card.setObjectName("sensorCard")

        layout = QVBoxLayout(sensor_card)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(6)

        sensor_title = QLabel("Live Field Context")
        sensor_title.setObjectName("sensorTitle")

        self.sensor_label = QLabel("Soil: 0% | Temp: 0°C | Rain: No | Disease: None | Crop: Tea")
        self.sensor_label.setObjectName("sensorData")

        self.scan_context_label = QLabel("Latest Scan: Not Available")
        self.scan_context_label.setObjectName("sensorData")

        layout.addWidget(sensor_title)
        layout.addWidget(self.sensor_label)
        layout.addWidget(self.scan_context_label)

        self.main_layout.addWidget(sensor_card)

    def build_chat_area(self):
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(False)
        self.chat_display.document().setDocumentMargin(10)
        self.main_layout.addWidget(self.chat_display, 1)

    def build_input_area(self):
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")

        input_card = QFrame()
        input_card.setObjectName("inputCard")

        row = QHBoxLayout(input_card)
        row.setContentsMargins(10, 8, 10, 8)
        row.setSpacing(8)

        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask something about your crops...")
        self.input_box.returnPressed.connect(self.send_message)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        row.addWidget(self.input_box, 1)
        row.addWidget(self.send_button)

        self.main_layout.addWidget(self.status_label)
        self.main_layout.addWidget(input_card)

    def update_sensor_data(self, data):
        self.sensor_data = data

        self.sensor_label.setText(
            f"Soil: {data.get('soil', 0)}% | "
            f"Temp: {data.get('temp', 0)}°C | "
            f"Rain: {data.get('rain', 'No')} | "
            f"Disease: {data.get('disease', 'None')} | "
            f"Crop: {data.get('crop', 'Tea')}"
        )

    def update_disease_context(self, summary: dict):
        self.disease_summary = summary

        if not summary or summary.get("total_points", 0) == 0:
            self.scan_context_label.setText("Latest Scan: Not Available")
            return

        most_common = summary.get("most_common_disease", "None")
        field_health = summary.get("overall_field_health", "Unknown")
        diseased_percent = summary.get("diseased_percent", 0.0)

        display_disease = most_common.replace("_", " ").title() if most_common != "None" else "None"

        self.scan_context_label.setText(
            f"Latest Scan: {field_health} | Diseased: {diseased_percent}% | Most Common: {display_disease}"
        )

    def append_user_message(self, text: str):
        safe = html.escape(text)
        self.chat_display.append(f"""
        <div style="margin: 10px 0; text-align: right;">
            <div style="
                display: inline-block;
                max-width: 75%;
                background-color: #4f8cff;
                color: white;
                padding: 12px 14px;
                border-radius: 16px 16px 4px 16px;
                font-size: 14px;
            ">
                <div style="font-size: 11px; opacity: 0.85; margin-bottom: 4px;">You</div>
                <div>{safe}</div>
            </div>
        </div>
        """)
        self.scroll_chat_to_bottom()

    def append_ai_message(self, text: str):
        safe = html.escape(text).replace("\n", "<br>")
        self.chat_display.append(f"""
        <div style="margin: 10px 0; text-align: left;">
            <div style="
                display: inline-block;
                max-width: 80%;
                background-color: #31384b;
                color: #eef3f8;
                padding: 12px 14px;
                border-radius: 16px 16px 16px 4px;
                border: 1px solid #434b61;
                font-size: 14px;
            ">
                <div style="font-size: 11px; color: #8ed0ff; margin-bottom: 4px;">AI Advisor</div>
                <div>{safe}</div>
            </div>
        </div>
        """)
        self.scroll_chat_to_bottom()

    def append_error_message(self, text: str):
        safe = html.escape(text)
        self.chat_display.append(f"""
        <div style="margin: 10px 0; text-align: left;">
            <div style="
                display: inline-block;
                max-width: 80%;
                background-color: #4a2d34;
                color: #ffd7dd;
                padding: 12px 14px;
                border-radius: 16px 16px 16px 4px;
                border: 1px solid #7a4652;
                font-size: 14px;
            ">
                <div style="font-size: 11px; color: #ff9cad; margin-bottom: 4px;">AI Error</div>
                <div>{safe}</div>
            </div>
        </div>
        """)
        self.scroll_chat_to_bottom()

    def scroll_chat_to_bottom(self):
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def format_analysis_response(self, response: dict) -> str:
        actions_list = response.get("recommended_actions", [])
        actions = (
            "\n".join([f"• {action}" for action in actions_list])
            if actions_list else
            "• No immediate action required."
        )

        return (
            f"Problem: {response.get('problem', 'Not specified')}\n\n"
            f"Explanation: {response.get('explanation', 'No explanation provided.')}\n\n"
            f"Recommended Actions:\n{actions}\n\n"
            f"Urgency: {response.get('urgency', 'Low')}"
        )

    def set_busy(self, busy: bool):
        self.send_button.setDisabled(busy)
        self.input_box.setDisabled(busy)
        self.status_label.setText("Thinking..." if busy else "Ready")

    def send_message(self):
        user_text = self.input_box.text().strip()
        if not user_text:
            return

        self.append_user_message(user_text)
        self.input_box.clear()
        self.set_busy(True)

        ai_input = self.sensor_data.copy()
        ai_input["user_query"] = user_text

        if self.disease_summary:
            ai_input["disease_summary"] = self.disease_summary

        threading.Thread(
            target=self._run_ai_request,
            args=(ai_input,),
            daemon=True
        ).start()

    def _run_ai_request(self, ai_input):
        try:
            response = get_ai_response(ai_input)

            if "error" in response:
                self.ai_error_ready.emit(response["error"])
            else:
                self.ai_response_ready.emit(response)

        except Exception as e:
            self.ai_error_ready.emit(str(e))

    def handle_ai_response(self, response: dict):
        self.set_busy(False)

        if response.get("mode") == "chat":
            self.append_ai_message(response.get("response", "No response received."))
            return

        formatted = self.format_analysis_response(response)
        self.append_ai_message(formatted)

    def handle_ai_error(self, error_text: str):
        self.set_busy(False)
        self.append_error_message(error_text)