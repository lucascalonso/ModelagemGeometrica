from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QColorDialog, QCheckBox, QGroupBox)

class AttributeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attribute Manager")
        self.resize(300, 350) # Aumentei um pouco a altura
        
        layout = QVBoxLayout()
        
        # ... (código existente: Nome, Tipo, Valor) ...
        # Nome do Atributo
        layout.addWidget(QLabel("Name:"))
        self.nameEdit = QLineEdit()
        layout.addWidget(self.nameEdit)
        
        # Tipo de Dado
        layout.addWidget(QLabel("Data Type:"))
        self.typeCombo = QComboBox()
        self.typeCombo.addItems(["String", "Float", "Integer", "Vector (x,y)"])
        layout.addWidget(self.typeCombo)
        
        # Value
        layout.addWidget(QLabel("Value:"))
        self.valueEdit = QLineEdit()
        layout.addWidget(self.valueEdit)

        # --- NOVO: Área de Seleção de Entidade ---
        self.groupTarget = QGroupBox("Apply to Entities:")
        targetLayout = QVBoxLayout()
        
        self.chkVertex = QCheckBox("Vertex")
        self.chkEdge = QCheckBox("Edge (Segment)")
        self.chkFace = QCheckBox("Face (Patch)")
        
        # Por padrão, vamos deixar tudo marcado ou forçar o usuário a escolher
        self.chkVertex.setChecked(True)
        self.chkEdge.setChecked(True)
        self.chkFace.setChecked(True)
        
        targetLayout.addWidget(self.chkVertex)
        targetLayout.addWidget(self.chkEdge)
        targetLayout.addWidget(self.chkFace)
        self.groupTarget.setLayout(targetLayout)
        
        layout.addWidget(self.groupTarget)
        # -----------------------------------------

        # ... (código existente: Seletor de Cor e Botões) ...
        # --- Seletor de Cor ---
        self.selected_color = "#000000"
        colorLayout = QHBoxLayout()
        self.btnColor = QPushButton("Attribute Color")
        self.btnColor.clicked.connect(self.pick_color)
        self.lblColorPreview = QLabel("■")
        self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")
        colorLayout.addWidget(self.btnColor)
        colorLayout.addWidget(self.lblColorPreview)
        layout.addLayout(colorLayout)
        
        # Botões
        btnLayout = QHBoxLayout()
        self.btnApply = QPushButton("Apply")
        self.btnCancel = QPushButton("Cancel")
        btnLayout.addWidget(self.btnApply)
        btnLayout.addWidget(self.btnCancel)
        layout.addLayout(btnLayout)
        
        self.setLayout(layout)
        
        self.btnApply.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)

    # ... (método pick_color existente) ...
    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")

    def get_data(self):
        name = self.nameEdit.text().strip()
        dtype = self.typeCombo.currentText()
        raw_value = self.valueEdit.text().strip()
        
        if not name: return None
            
        try:
            if dtype == "Float": value = float(raw_value)
            elif dtype == "Integer": value = int(raw_value)
            elif dtype == "Vector":
                parts = raw_value.split(',')
                if len(parts) != 2: raise ValueError
                value = [float(parts[0]), float(parts[1])]
            else: value = raw_value
        except ValueError: return None
        
        # --- NOVO: Retorna também quais entidades foram selecionadas ---
        targets = {
            "vertex": self.chkVertex.isChecked(),
            "edge": self.chkEdge.isChecked(),
            "face": self.chkFace.isChecked()
        }
        
        # Retorna uma tupla com 5 elementos agora
        return name, value, dtype, self.selected_color, targets