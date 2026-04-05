from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class ControlsPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Controls Page"))

        self.setLayout(layout)