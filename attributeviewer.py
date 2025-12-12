from PySide6.QtWidgets import (QDockWidget, QTreeWidget, QTreeWidgetItem, QWidget, 
                               QVBoxLayout, QPushButton, QColorDialog)
from PySide6.QtCore import Qt

class AttributeViewer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Inspector de Atributos", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Widget principal do Dock
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Árvore de propriedades
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Entidade / Atributo", "Valor"])
        self.tree.setColumnWidth(0, 150)

        # Cor inicial
        self.text_color = "#333333"
        self.update_style()
        
        self.layout.addWidget(self.tree)
        
        # Botão para escolher cor
        self.btn_color = QPushButton("Escolher Cor do Texto")
        self.btn_color.clicked.connect(self.pick_color)
        self.layout.addWidget(self.btn_color)

        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)

    def update_style(self):
        """Aplica o CSS com a cor de texto atual."""
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: #ECECEC; 
                color: {self.text_color};
                border: none;
            }}
            QHeaderView::section {{
                background-color: #DCDCDC;
                color: {self.text_color};
                padding: 4px;
                border: 1px solid #C0C0C0;
            }}
        """)

    def pick_color(self):
        """Abre o diálogo de cor e atualiza a interface."""
        color = QColorDialog.getColor()
        if color.isValid():
            self.text_color = color.name()
            self.update_style()

    def update_view(self, he_controller):
        """Atualiza a árvore com base na seleção atual do controlador."""
        self.tree.clear()
        
        model = he_controller.hemodel
        
        # Coleta seleções
        sel_vertices = model.selectedVertices()
        sel_edges = model.selectedEdges()
        sel_faces = model.selectedFaces()
        
        total_sel = len(sel_vertices) + len(sel_edges) + len(sel_faces)
        
        if total_sel == 0:
            return

        # --- Vértices ---
        if sel_vertices:
            root_v = QTreeWidgetItem(self.tree, [f"Vértices ({len(sel_vertices)})", ""])
            root_v.setExpanded(True)
            for i, v in enumerate(sel_vertices):
                pt = v.point
                coords = f"({pt.getX():.2f}, {pt.getY():.2f})"
                item = QTreeWidgetItem(root_v, [f"Vértice {i+1}", coords])
                self._add_attributes_to_item(item, pt)

        # --- Arestas ---
        if sel_edges:
            root_e = QTreeWidgetItem(self.tree, [f"Arestas ({len(sel_edges)})", ""])
            root_e.setExpanded(True)
            for i, e in enumerate(sel_edges):
                seg = e.segment
                item = QTreeWidgetItem(root_e, [f"Aresta {i+1}", ""])
                self._add_attributes_to_item(item, seg)

        # --- Regiões ---
        if sel_faces:
            root_f = QTreeWidgetItem(self.tree, [f"Regiões ({len(sel_faces)})", ""])
            root_f.setExpanded(True)
            for i, f in enumerate(sel_faces):
                patch = f.patch
                item = QTreeWidgetItem(root_f, [f"Região {i+1}", ""])
                self._add_attributes_to_item(item, patch)

    def _add_attributes_to_item(self, parent_item, entity):
        """Helper para listar os atributos de uma entidade."""
        if hasattr(entity, 'attributes') and entity.attributes:
            for attr in entity.attributes:
                name = attr.get('name', 'Sem Nome')
                
                val = "N/A"
                if 'properties' in attr and 'Value' in attr['properties']:
                    val = str(attr['properties']['Value'])
                elif 'value' in attr:
                    val = str(attr['value'])
                
                attr_item = QTreeWidgetItem(parent_item, [name, val])