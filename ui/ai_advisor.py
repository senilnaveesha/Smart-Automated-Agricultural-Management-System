from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTextEdit,
    QLineEdit, QPushButton, QLabel
)

from backend.ai_engine import get_ai_response


class AIAdvisorPage(QWidget):
    def __init__(self):
        super().__init__()

        self.layout = QVBoxLayout()

        # 🧠 Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        # 🌱 Sensor data label
        self.sensor_label = QLabel("Sensor Data: Not Available")

        # ✍ User input
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask something about your crops...")

        # 📤 Send button
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        # Add to layout
        self.layout.addWidget(QLabel("🌱 AI Advisor"))
        self.layout.addWidget(self.chat_display)
        self.layout.addWidget(self.sensor_label)
        self.layout.addWidget(self.input_box)
        self.layout.addWidget(self.send_button)

        self.setLayout(self.layout)

        # Default sensor data (will update later)
        self.sensor_data = {
            "soil": 0,
            "temp": 0,
            "rain": "No",
            "disease": "None",
            "crop": "Tea"
        }

    # 🔄 Update sensor data from dashboard
    def update_sensor_data(self, data):
        self.sensor_data = data

        self.sensor_label.setText(
            f"Soil: {data['soil']}% | Temp: {data['temp']}°C | Rain: {data['rain']}"
        )

    # 💬 Send message to AI
    def send_message(self):
        user_text = self.input_box.text()
        if not user_text:
            return

        # Show user message
        self.chat_display.append(f"👤 You: {user_text}")

        # Combine user + sensor data
        ai_input = self.sensor_data.copy()
        ai_input["user_query"] = user_text

        # Call AI
        response = get_ai_response(ai_input)

        # Show AI response
        if "error" in response:
            self.chat_display.append("⚠ AI Error")
            self.input_box.clear()
            return

        # 🧠 Chat mode (normal conversation)
        if response.get("mode") == "chat":
            self.chat_display.append(f"🤖 AI: {response['response']}")

        # 🌱 Analysis mode (farming advice)
        else:
            actions = "\n- ".join(response["recommended_actions"])

            self.chat_display.append(
            f"🤖 AI:\n"
            f"Problem: {response['problem']}\n"
            f"Explanation: {response.get('explanation', '')}\n"
            f"Actions:\n- {actions}\n"
            f"Urgency: {response['urgency']}\n"
            )

        self.input_box.clear()