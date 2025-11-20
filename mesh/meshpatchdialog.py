from PySide6.QtWidgets import QDialog, QDialogButtonBox
from gui.meshpatchui import Ui_MeshPatchDialog

class MeshPatchDialog(QDialog, Ui_MeshPatchDialog):
    def __init__(self, controller):
        super().__init__()
        self.setupUi(self)
        self.controller = controller
        self.buttonBox.button(QDialogButtonBox.Apply).clicked.connect(self.controller.meshPatchApply)
        self.buttonBox.button(QDialogButtonBox.Close).clicked.connect(self.controller.meshPatchClose)

    def closeEvent(self, event):
        self.controller.meshPatchCloseEvent()
        event.accept()