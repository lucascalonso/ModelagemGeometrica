from PySide6.QtWidgets import QDialog, QDialogButtonBox
from gui.meshsegmentui import Ui_MeshSegmentDialog

class MeshSegmentDialog(QDialog, Ui_MeshSegmentDialog):
    def __init__(self, controller):
        super().__init__()
        self.setupUi(self)
        self.controller = controller
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.controller.meshSegmentApply)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.controller.meshSegmentClose)
    
    def closeEvent(self, event):
        self.controller.meshSegmentCloseEvent()
        event.accept()
