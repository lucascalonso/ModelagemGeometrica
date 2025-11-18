from PySide6.QtWidgets import QMainWindow, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QCheckBox, QPushButton
from PySide6.QtCore import Qt
from PySide6.QtGui import QDoubleValidator
from gui.gridui import Ui_GridDialog


class GridDialog(QMainWindow, Ui_GridDialog):
    def __init__(self, _appctrl):
        super().__init__()
        super().setupUi(self)

        # App controller
        self.appController = _appctrl

        # Use QDoubleValidator for flexible input
        validator = QDoubleValidator(0.01, 1000.0, 2)
        self.lineEditXdir.setValidator(validator)
        self.lineEditYdir.setValidator(validator)

        # Grid Actions
        self.lineEditXdir.editingFinished.connect(self.appController.gridChangeGrid)
        self.lineEditYdir.editingFinished.connect(self.appController.gridChangeGrid)
        self.checkBoxSnap.clicked.connect(self.appController.gridChangeGrid)
        self.closeButton.clicked.connect(self.appController.gridClose)


    def closeEvent(self, _event):
        # Let the controller handle the window hiding
        self.appController.gridCloseEvent()
        _event.accept()
