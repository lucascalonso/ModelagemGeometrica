from PySide6.QtWidgets import (QDockWidget, QTreeWidget, QTreeWidgetItem, QWidget, 
                                QVBoxLayout, QMenu, QMessageBox)
from PySide6.QtCore import Qt

class AttributeViewer(QDockWidget):
    def __init__(self, parent=None):
        super().__init__("Attribute Manager", parent)
        self.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        
        self.controller = None # Referência ao controlador
        
        # Widget principal do Dock
        self.main_widget = QWidget()
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Árvore de propriedades
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Entity / Attribute", "Value"])
        self.tree.setColumnWidth(0, 180)
        
        # Habilita Menu de Contexto (Botão Direito)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)

        # Conecta sinal de edição
        self.tree.itemChanged.connect(self.on_item_changed)

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
            QTreeWidget::item {
                padding: 4px;
            }
        """)
        
        self.layout.addWidget(self.tree)
        self.main_widget.setLayout(self.layout)
        self.setWidget(self.main_widget)

    def update_view(self, he_controller):
        """Atualiza a árvore com base na seleção atual do controlador."""
        self.tree.blockSignals(True) # Evita disparar itemChanged enquanto montamos a lista
        self.tree.clear()
        self.controller = he_controller # Guarda referência para usar na edição
        
        model = he_controller.hemodel
        
        # Coleta seleções
        sel_vertices = model.selectedVertices()
        sel_edges = model.selectedEdges()
        sel_faces = model.selectedFaces()
        
        total_sel = len(sel_vertices) + len(sel_edges) + len(sel_faces)
        
        if total_sel == 0:
            self.tree.blockSignals(False)
            return

        # --- Vértices ---
        if sel_vertices:
            root_v = QTreeWidgetItem(self.tree, [f"Vertices ({len(sel_vertices)})", ""])
            root_v.setExpanded(True)
            for i, v in enumerate(sel_vertices):
                pt = v.point
                item = QTreeWidgetItem(root_v, [f"Vertex {v.ID}", ""])
                item.setExpanded(True) 
                self._add_attributes_to_item(item, pt)

        # --- Arestas (Segmentos) ---
        if sel_edges:
            root_e = QTreeWidgetItem(self.tree, [f"Edges ({len(sel_edges)})", ""])
            root_e.setExpanded(True)
            for i, e in enumerate(sel_edges):
                seg = e.segment
                item = QTreeWidgetItem(root_e, [f"Edge {e.ID}", ""])
                item.setExpanded(True)
                self._add_attributes_to_item(item, seg)

        # --- Faces (Regiões) ---
        if sel_faces:
            root_f = QTreeWidgetItem(self.tree, [f"Faces ({len(sel_faces)})", ""])
            root_f.setExpanded(True)
            for i, f in enumerate(sel_faces):
                patch = f.patch
                item = QTreeWidgetItem(root_f, [f"Face {f.ID}", ""])
                item.setExpanded(True) 
                self._add_attributes_to_item(item, patch)
        
        self.tree.blockSignals(False)

    def _add_attributes_to_item(self, parent_item, entity):
        """Helper para listar os atributos de uma entidade."""
        if hasattr(entity, 'attributes') and entity.attributes:
            for attr in entity.attributes:
                name = attr.get('name', 'Sem Nome')
                
                val = ""
                if 'properties' in attr and 'Value' in attr['properties']:
                    val = str(attr['properties']['Value'])
                elif 'value' in attr:
                    val = str(attr['value'])
                
                attr_item = QTreeWidgetItem(parent_item, [name, val])
                
                attr_item.setFlags(attr_item.flags() | Qt.ItemIsEditable)
                
                # Guarda referência da entidade e do nome do atributo no item (invisível)
                attr_item.setData(0, Qt.UserRole, entity)      # Guarda o objeto real
                attr_item.setData(1, Qt.UserRole, name)        # Guarda o nome do atributo
                # -----------------------

    def on_item_changed(self, item, column):
        """Chamado quando o usuário edita um valor e aperta Enter."""
        if column != 1 or not self.controller:
            return
            
        entity = item.data(0, Qt.UserRole)
        attr_name = item.data(1, Qt.UserRole)
        new_value = item.text(1)
        
        if entity and attr_name:
            success = self.controller.updateEntityAttributeValue(entity, attr_name, new_value)
            if not success:
                # Se falhar (ex: digitou texto num campo int), reverte a view chamando update
                self.update_view(self.controller)

    def show_context_menu(self, position):
        """Mostra menu de clique direito para deletar atributo."""
        item = self.tree.itemAt(position)
        if not item: return
        
        # Verifica se é um item de atributo (tem dados guardados)
        entity = item.data(0, Qt.UserRole)
        attr_name = item.data(1, Qt.UserRole)
        
        if entity and attr_name:
            menu = QMenu()
            action_delete = menu.addAction("Delete Attribute")
            action = menu.exec(self.tree.viewport().mapToGlobal(position))
            
            if action == action_delete:
                self.controller.removeAttributeFromEntity(entity, attr_name)
                self.update_view(self.controller) # Atualiza a lista visualmente