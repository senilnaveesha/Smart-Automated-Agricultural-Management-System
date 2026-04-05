from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout

class DiseaseMapPage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Disease Map Page"))

        self.setLayout(layout)