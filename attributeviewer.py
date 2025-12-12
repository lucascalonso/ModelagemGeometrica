from PySide6.QtWidgets import (QDockWidget, QTreeWidget, QTreeWidgetItem, QWidget, 
                                QVBoxLayout)
from PySide6.QtCore import Qt

class AttributeViewer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Attribute Manager", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        # Widget principal do Dock
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Árvore de propriedades
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Entity / Attribute", "Value"])
        self.tree.setColumnWidth(0, 150)

        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #ECECEC; 
                color: #333333;
                border: none;
            }
            QHeaderView::section {
                background-color: #DCDCDC;
                color: #333333;
                padding: 4px;
                border: 1px solid #C0C0C0;
            }
        """)
        
        self.layout.addWidget(self.tree)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)


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
            root_v = QTreeWidgetItem(self.tree, [f"Vertices ({len(sel_vertices)})", ""])
            root_v.setExpanded(True)
            for i, v in enumerate(sel_vertices):
                pt = v.point
                item = QTreeWidgetItem(root_v, [f"Vertex {i+1}", ""])
                item.setExpanded(True) 
                self._add_attributes_to_item(item, pt)

        # --- Arestas (Segmentos) ---
        if sel_edges:
            root_e = QTreeWidgetItem(self.tree, [f"Edges ({len(sel_edges)})", ""])
            root_e.setExpanded(True)
            for i, e in enumerate(sel_edges):
                seg = e.segment
                item = QTreeWidgetItem(root_e, [f"Edge {i+1}", ""])
                item.setExpanded(True)
                self._add_attributes_to_item(item, seg)

        # --- Faces (Regiões) ---
        if sel_faces:
            root_f = QTreeWidgetItem(self.tree, [f"Faces ({len(sel_faces)})", ""])
            root_f.setExpanded(True)
            for i, f in enumerate(sel_faces):
                patch = f.patch
                item = QTreeWidgetItem(root_f, [f"Face {i+1}", ""])
                item.setExpanded(True) 
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