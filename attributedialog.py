from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                               QComboBox, QPushButton, QHBoxLayout, QMessageBox, 
                               QColorDialog, QCheckBox, QGroupBox)

class AttributeDialog(QDialog):
    def __init__(self, parent=None, existing_attributes=None):
        super().__init__(parent)
        self.setWindowTitle("Attribute Manager")
        self.resize(300, 400)
        
        self.existing_attributes = existing_attributes if existing_attributes else []
        
        layout = QVBoxLayout()
        
        # --- Seleção/Criação de Atributo (NOVO) ---
        layout.addWidget(QLabel("Name (Select existing or type new):"))
        self.nameCombo = QComboBox()
        self.nameCombo.setEditable(True) # Permite digitar um novo nome
        
        # Adiciona item vazio para "Novo"
        self.nameCombo.addItem("") 
        
        # Adiciona os atributos existentes na lista
        for attr in self.existing_attributes:
            self.nameCombo.addItem(attr['name'])
            
        layout.addWidget(self.nameCombo)
        # -----------------------------------
        
        # Tipo de Dado
        layout.addWidget(QLabel("Data Type:"))
        self.typeCombo = QComboBox()
        self.typeCombo.addItems(["String", "Float", "Integer", "Vector (x,y)"])
        layout.addWidget(self.typeCombo)
        
        # Value
        layout.addWidget(QLabel("Value:"))
        self.valueEdit = QLineEdit()
        layout.addWidget(self.valueEdit)

        # --- Área de Seleção de Entidade ---
        self.groupTarget = QGroupBox("Apply to Entities:")
        targetLayout = QVBoxLayout()
        
        self.chkVertex = QCheckBox("Vertex")
        self.chkEdge = QCheckBox("Edge (Segment)")
        self.chkFace = QCheckBox("Face (Patch)")
        
        # Padrão
        self.chkVertex.setChecked(True)
        self.chkEdge.setChecked(True)
        self.chkFace.setChecked(True)
        
        targetLayout.addWidget(self.chkVertex)
        targetLayout.addWidget(self.chkEdge)
        targetLayout.addWidget(self.chkFace)
        self.groupTarget.setLayout(targetLayout)
        
        layout.addWidget(self.groupTarget)
        
        # --- Seletor de Cor ---
        self.selected_color = "#000000" # Preto por padrão
        
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
        
        # Conexões
        self.btnApply.clicked.connect(self.accept)
        self.btnCancel.clicked.connect(self.reject)
        
        # Conecta a mudança no Combo para preencher os dados automaticamente
        self.nameCombo.currentIndexChanged.connect(self.on_attribute_selected)
        self.nameCombo.editTextChanged.connect(self.on_text_edited)

    def on_attribute_selected(self, index):
        """Chamado quando o usuário seleciona um item da lista."""
        name = self.nameCombo.currentText()
        self.fill_data_from_name(name)

    def on_text_edited(self, text):
        """Chamado quando o usuário digita."""
        self.fill_data_from_name(text)

    def fill_data_from_name(self, name):
        """Busca o atributo pelo nome e preenche os campos se existir."""
        attr = next((a for a in self.existing_attributes if a['name'] == name), None)
        
        if attr:
            # 1. Preenche Tipo
            ptypes = attr.get('properties_type', [])
            dtype = "String"
            if "float" in ptypes:
                if len(ptypes) >= 2 and ptypes[0]=="float" and ptypes[1]=="float":
                    dtype = "Vector (x,y)"
                else:
                    dtype = "Float"
            elif "int" in ptypes:
                dtype = "Integer"
            
            idx = self.typeCombo.findText(dtype)
            if idx >= 0: self.typeCombo.setCurrentIndex(idx)
            
            # 2. Preenche Valor (Último usado)
            if 'properties' in attr and 'Value' in attr['properties']:
                val = attr['properties']['Value']
                if isinstance(val, list):
                    self.valueEdit.setText(f"{val[0]}, {val[1]}")
                else:
                    self.valueEdit.setText(str(val))
            
            # 3. Preenche Cor
            if 'textcolor' in attr:
                self.selected_color = attr['textcolor']
                self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")
            
            # 4. Preenche Targets
            self.chkVertex.setChecked(attr.get('applyOnVertex', True))
            self.chkEdge.setChecked(attr.get('applyOnEdge', True))
            self.chkFace.setChecked(attr.get('applyOnFace', True))
        else:
            # Se é um nome novo, não limpa tudo para não irritar o usuário,
            # mas garante que os campos estejam habilitados.
            pass

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.selected_color = color.name()
            self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")

    def get_data(self):
        name = self.nameCombo.currentText().strip()
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
            
        targets = {
            "vertex": self.chkVertex.isChecked(),
            "edge": self.chkEdge.isChecked(),
            "face": self.chkFace.isChecked()
        }
            
        return name, value, dtype, self.selected_color, targets