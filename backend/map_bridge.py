from PyQt6.QtCore import QObject, pyqtSlot


class MapBridge(QObject):

    def __init__(self):
        super().__init__()
        self.coordinates = []

    @pyqtSlot('QVariant')
    def receivePolygon(self, coords):
        print("📍 Received Polygon:", coords)
        self.coordinates = coords