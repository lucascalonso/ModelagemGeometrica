from PySide6.QtCore import (QCoreApplication, QMetaObject, Qt)
from PySide6.QtWidgets import (QDialogButtonBox, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout)

class Ui_MeshSegmentDialog(object):
    def setupUi(self, MeshSegmentDialog):
        if not MeshSegmentDialog.objectName():
            MeshSegmentDialog.setObjectName(u"MeshSegmentDialog")
        MeshSegmentDialog.resize(300, 150)
        
        self.verticalLayout = QVBoxLayout(MeshSegmentDialog)
        
        # Inputs
        self.layoutInputs = QVBoxLayout()
        
        # Subdivisions
        self.layoutSubdiv = QHBoxLayout()
        self.labelNumSubdiv = QLabel(MeshSegmentDialog)
        self.labelNumSubdiv.setText("Number of Subdivisions:")
        self.lineEditNumSubdiv = QLineEdit(MeshSegmentDialog)
        self.layoutSubdiv.addWidget(self.labelNumSubdiv)
        self.layoutSubdiv.addWidget(self.lineEditNumSubdiv)
        self.layoutInputs.addLayout(self.layoutSubdiv)

        # Ratio
        self.layoutRatio = QHBoxLayout()
        self.labelRatio = QLabel(MeshSegmentDialog)
        self.labelRatio.setText("Ratio:")
        self.lineEditRatio = QLineEdit(MeshSegmentDialog)
        self.layoutRatio.addWidget(self.labelRatio)
        self.layoutRatio.addWidget(self.lineEditRatio)
        self.layoutInputs.addLayout(self.layoutRatio)
        
        self.verticalLayout.addLayout(self.layoutInputs)

        # Buttons
        self.buttonBox = QDialogButtonBox(MeshSegmentDialog)
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Apply | QDialogButtonBox.Close)
        self.verticalLayout.addWidget(self.buttonBox)

        self.retranslateUi(MeshSegmentDialog)
        self.buttonBox.accepted.connect(MeshSegmentDialog.accept)
        self.buttonBox.rejected.connect(MeshSegmentDialog.reject)
        QMetaObject.connectSlotsByName(MeshSegmentDialog)

    def retranslateUi(self, MeshSegmentDialog):
        MeshSegmentDialog.setWindowTitle(QCoreApplication.translate("MeshSegmentDialog", u"Mesh Segment", None))