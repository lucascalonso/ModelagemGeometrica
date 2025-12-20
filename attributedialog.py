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
        
        # Seleção de Símbolo
        layout.addWidget(QLabel("Visual Symbol:"))
        self.symbolCombo = QComboBox()
        self.symbolCombo.addItems(["None", "Square", "Circle", "Triangle", "Arrow", "Support"])
        layout.addWidget(self.symbolCombo)

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
            # 1. Preenche Valor
            if 'properties' in attr and 'Value' in attr['properties']:
                self.valueEdit.setText(str(attr['properties']['Value']))
            
            # 2. Preenche Tipo de Dado (CORREÇÃO AQUI)
            if 'properties_type' in attr and len(attr['properties_type']) > 0:
                ptype = attr['properties_type'][0] # Pega o primeiro tipo (geralmente o do Value)
                
                # Mapeia os tipos internos para os nomes do ComboBox
                combo_text = "String" # Default
                if ptype == "float":
                    combo_text = "Float"
                elif ptype == "int":
                    combo_text = "Integer"
                elif ptype == "vector": # Se houver suporte a vetor
                    combo_text = "Vector (x,y)"
                
                idx = self.typeCombo.findText(combo_text)
                if idx >= 0:
                    self.typeCombo.setCurrentIndex(idx)

            # 3. Preenche Símbolo (Visual Symbol)
            if 'symbol' in attr:
                idx = self.symbolCombo.findText(attr['symbol'])
                if idx >= 0:
                    self.symbolCombo.setCurrentIndex(idx)
            
            # 4. Preenche Cor
            # A cor é salva como lista [r, g, b] (0.0 a 1.0) dentro de properties['Color']
            if 'properties' in attr and 'Color' in attr['properties']:
                c = attr['properties']['Color']
                if isinstance(c, list) and len(c) >= 3:
                    # Converte RGB (0-1) de volta para Hex (#RRGGBB)
                    r, g, b = int(c[0]*255), int(c[1]*255), int(c[2]*255)
                    hex_color = f"#{r:02x}{g:02x}{b:02x}"
                    
                    self.selected_color = hex_color
                    self.lblColorPreview.setStyleSheet(f"color: {self.selected_color}; font-size: 20px;")
            
            # 5. Preenche Targets (Checkboxes)
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
        symbol = self.symbolCombo.currentText() 

        if not name:
            return None
            
        try:
            if dtype == "Float":
                value = float(raw_value)
            elif dtype == "Integer":
                value = int(raw_value)
            elif dtype == "Vector (x,y)":
                # Remove parênteses se houver e divide por vírgula
                clean_val = raw_value.replace('(', '').replace(')', '')
                parts = clean_val.split(',')
                if len(parts) >= 2:
                    value = [float(parts[0]), float(parts[1])]
                else:
                    # Fallback se o usuário digitar apenas um número
                    value = [float(parts[0]), 0.0]
            else:
                value = raw_value # String
        except ValueError:
            # Se falhar a conversão, retorna None para não criar atributo inválido
            return None
            
        targets = {
            "vertex": self.chkVertex.isChecked(),
            "edge": self.chkEdge.isChecked(),
            "face": self.chkFace.isChecked()
        }
            
        return name, value, dtype, self.selected_color, targets, symbol

    