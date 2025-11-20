from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtWidgets import (QDialogButtonBox, QRadioButton, QVBoxLayout, QGroupBox)

class Ui_MeshPatchDialog(object):
    def setupUi(self, MeshPatchDialog):
        if not MeshPatchDialog.objectName():
            MeshPatchDialog.setObjectName(u"MeshPatchDialog")
        MeshPatchDialog.resize(300, 200)
        
        self.verticalLayout = QVBoxLayout(MeshPatchDialog)
        
        self.groupBox = QGroupBox(MeshPatchDialog)
        self.groupBox.setTitle("Mesh Type")
        self.layoutGroup = QVBoxLayout(self.groupBox)
        
        self.radioButtonBilinear = QRadioButton(self.groupBox)
        self.radioButtonBilinear.setText("Bilinear")
        self.radioButtonBilinear.setChecked(True)
        self.layoutGroup.addWidget(self.radioButtonBilinear)
        
        self.radioButtonTrilinear = QRadioButton(self.groupBox)
        self.radioButtonTrilinear.setText("Trilinear")
        self.layoutGroup.addWidget(self.radioButtonTrilinear)
        
        self.radioButtonDelaunay = QRadioButton(self.groupBox)
        self.radioButtonDelaunay.setText("Delaunay")
        self.layoutGroup.addWidget(self.radioButtonDelaunay)
        
        self.verticalLayout.addWidget(self.groupBox)

        self.buttonBox = QDialogButtonBox(MeshPatchDialog)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(MeshPatchDialog)
        self.buttonBox.accepted.connect(MeshPatchDialog.accept)
        self.buttonBox.rejected.connect(MeshPatchDialog.reject)
        QMetaObject.connectSlotsByName(MeshPatchDialog)

    def retranslateUi(self, MeshPatchDialog):
        MeshPatchDialog.setWindowTitle(QCoreApplication.translate("MeshPatchDialog", u"Mesh Patch", None))