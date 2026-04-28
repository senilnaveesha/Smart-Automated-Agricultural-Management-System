import os
os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--disable-gpu --no-sandbox"

import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget
)

from ui.dashboard import DashboardPage
from ui.ai_advisor import AIAdvisorPage
from ui.disease_map import DiseaseMapPage
from ui.drone_control import DroneControlPage
from ui.controls import ControlsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Agriculture System")
        self.setGeometry(100, 100, 1200, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.ai_advisor = AIAdvisorPage()
        self.dashboard = DashboardPage(ai_page=self.ai_advisor)

        self.disease_map = DiseaseMapPage(ai_advisor=self.ai_advisor)
        self.drone_control = DroneControlPage()
        self.controls = ControlsPage()

        self.tabs.addTab(self.dashboard, "🌱 Dashboard")
        self.tabs.addTab(self.ai_advisor, "🤖 AI Advisor")
        self.tabs.addTab(self.disease_map, "🦠 Disease Map")
        self.tabs.addTab(self.drone_control, "🚁 Drone Control")
        self.tabs.addTab(self.controls, "⚙ Controls")

        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2f;
                color: white;
            }
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                background: #2b2b3c;
                padding: 10px;
                margin: 2px;
                border-radius: 6px;
            }
            QTabBar::tab:selected {
                background: #3c3c5c;
            }
        """)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()