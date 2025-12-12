from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QMessageBox, QColorDialog)

class AttributeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Attribute Manager")
        self.resize(300, 250)
        
        layout = QVBoxLayout()
        
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

        # --- Seletor de Cor ---
        self.selected_color = "#000000" # Preto por padrão
        
        colorLayout = QHBoxLayout()
        self.btnColor = QPushButton("Attribute Color")
        self.btnColor.clicked.connect(self.pick_color)
        
        self.lblColorPreview = QLabel("■") # Quadrado de preview
        self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")
        
        colorLayout.addWidget(self.btnColor)
        colorLayout.addWidget(self.lblColorPreview)
        layout.addLayout(colorLayout)
        # ---------------------------
        
        # Botões
        btnLayout = QHBoxLayout()
        self.btnApply = QPushButton("Apply")
        self.btnCancel = QPushButton("Cancel")
        
        btnLayout.addWidget(self.btnApply)
        btnLayout.addWidget(self.btnCancel)
        layout.addLayout(btnLayout)
        
        self.setLayout(layout)
        
        # Conexões
        self.btnApply.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")

    def get_data(self):
        name = self.nameEdit.text().strip()
        dtype = self.typeCombo.currentText()
        raw_value = self.valueEdit.text().strip()
        
        if not name:
            return None
            
        try:
            if dtype == "Float":
                value = float(raw_value)
            elif dtype == "Integer":
                value = int(raw_value)
            elif dtype == "Vector":
                parts = raw_value.split(',')
                if len(parts) != 2: raise ValueError
                value = [float(parts[0]), float(parts[1])]
            else:
                value = raw_value
        except ValueError:
            return None
            
        return name, value, dtype, self.selected_color