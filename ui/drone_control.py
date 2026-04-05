from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DroneControlPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Drone Control Page"))

        self.setLayout(layout)