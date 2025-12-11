from PySide6 import QtCore
from PySide6.QtWidgets import QMainWindow, QHBoxLayout, QMessageBox
from griddialog import GridDialog
from grid import Grid
from appmodel import AppModel
from appview import AppView
from curvecollector import CurveCollector
from curvereshape import CurveReshape
from glcanvas import GLCanvas
from gui.myapp import Ui_MyApp
from mesh.meshgenerator import MeshGenerator
from mesh.meshpatch import MeshPatch
from mesh.meshsegmentdialog import MeshSegmentDialog
from mesh.meshpatchdialog import MeshPatchDialog
from hetool.compgeom.compgeom import CompGeom
from hetool.geometry.point import Point


class AppController(QMainWindow, Ui_MyApp):
    def __init__(self):
        super().__init__()
        super().setupUi(self)

        # Create model object, view object, and curve collector object
        # CORREÇÃO: Instancia AppModel sem passar 'self'
        self.model = AppModel() 
        
        self.collector = CurveCollector(self.model)
        self.reshape = CurveReshape(self.model)
        self.view = AppView(self.model, self.reshape)

        # Create grid and grid dialog
        self.grid = Grid()
        isTurnedOn = self.grid.getDisplayInfo()
        self.actionGrid.setChecked(isTurnedOn)
        dX, dY = self.grid.getGridSpace()
        isSnapOn = self.grid.getSnapInfo()
        self.gridDialog = GridDialog(self)
        self.gridDialog.lineEditXdir.setText(str(dX))
        self.gridDialog.lineEditYdir.setText(str(dY))
        self.gridDialog.checkBoxSnap.setChecked(isSnapOn)

        # Create Mesh Patch object
        self.meshPatch = MeshPatch()

        # Create Mesh Dialogs
        self.meshSegmentDialog = MeshSegmentDialog(self)
        self.meshPatchDialog = MeshPatchDialog(self)

        # Create an OpenGL canvas and associate to the
        # canvas widget
        self.glcanvas = GLCanvas(self)
        self.glcanvas.setParent(self.canvas)
        horizontalLayout = QHBoxLayout(self.canvas)
        horizontalLayout.setContentsMargins(0, 0, 0, 0)
        horizontalLayout.setSpacing(0)
        horizontalLayout.addWidget(self.glcanvas)

        # Get mouse move events even when no buttons are held down
        self.glcanvas.setMouseTracking(True)

        # Set canvas input focus to activate keyboard events
        self.glcanvas.setFocusPolicy(QtCore.Qt.ClickFocus)

        # Associate grid to canvas
        self.glcanvas.setGrid(self.grid)

        # set default mouse action on canvas
        self.glcanvas.setMouseAction('SELECTION')
        self.actionSelect.setChecked(True)

        # Visualization Control ToolBar Actions
        self.actionFit.triggered.connect(self.glcanvas.fitWorldToViewport)
        self.actionZoomIn.triggered.connect(self.glcanvas.zoomIn)
        self.actionZoomOut.triggered.connect(self.glcanvas.zoomOut)
        self.actionPanLeft.triggered.connect(self.glcanvas.panLeft)
        self.actionPanRight.triggered.connect(self.glcanvas.panRight)
        self.actionPanUp.triggered.connect(self.glcanvas.panUp)
        self.actionPanDown.triggered.connect(self.glcanvas.panDown)

        # Modeling Control ToolBar Actions
        self.actionSelect.triggered.connect(self.on_actionSelect)
        self.actionDelete.triggered.connect(self.on_actionDelete)
        self.actionLine.triggered.connect(self.on_actionLine)
        self.actionPolyLine.triggered.connect(self.on_actionPolyLine)
        self.actionQuadBezier.triggered.connect(self.on_actionQuadBezier)
        self.actionCubicBezier.triggered.connect(self.on_actionCubicBezier)
        self.actionCircle.triggered.connect(self.on_actionCircle)
        self.actionCircleArc.triggered.connect(self.on_actionCircleArc)
        self.actionGrid.triggered.connect(self.on_actionGrid)
        self.actionIntersect.triggered.connect(self.intersectSegments)
        self.actionJoin.triggered.connect(self.joinSegments)
        self.actionSplit.triggered.connect(self.on_actionSplit)
        self.actionCreateRegion.triggered.connect(self.createRegion)
        self.actionMeshSegment.triggered.connect(self.on_actionMeshSegment)
        self.actionDomainMesh.triggered.connect(self.on_actionDomainMesh)

        
    ###########################################################
    #                                                         #
    #             Program close callback method               #
    #                                                         #
    ###########################################################
    def closeEvent(self, _event):
        self.gridDialog.close()
        self.meshSegmentDialog.close()
        self.meshPatchDialog.close()
        _event.accept()

    ###########################################################
    #                                                         #
    #        Selection, Deletion, and Curve Methods           #
    #                                                         #
    ###########################################################
    def on_actionSelect(self):
        self.glcanvas.setMouseAction('SELECTION')
        self.actionSelect.setChecked(True)
        self.actionLine.setChecked(False)
        self.actionPolyLine.setChecked(False)
        self.actionQuadBezier.setChecked(False)
        self.actionCubicBezier.setChecked(False)
        self.actionCircle.setChecked(False)
        self.actionCircleArc.setChecked(False)

    def on_actionDelete(self):
        # Delega para o HeController
        self.model.getHeController().delSelectedEntities()
        print("Delete executed")
        self.glcanvas.update()

    def on_actionLine(self):
        self.glcanvas.setMouseAction('COLLECTION')
        self.glcanvas.setCurveType('LINE')
        self.actionSelect.setChecked(False)
        self.actionLine.setChecked(True)
        self.actionPolyLine.setChecked(False)
        self.actionQuadBezier.setChecked(False)
        self.actionCubicBezier.setChecked(False)
        self.actionCircle.setChecked(False)
        self.actionCircleArc.setChecked(False)

    def on_actionPolyLine(self):
        self.glcanvas.setMouseAction('COLLECTION')
        self.glcanvas.setCurveType('POLYLINE')
        self.actionSelect.setChecked(False)
        self.actionLine.setChecked(False)
        self.actionPolyLine.setChecked(True)
        self.actionQuadBezier.setChecked(False)
        self.actionCubicBezier.setChecked(False)
        self.actionCircle.setChecked(False)
        self.actionCircleArc.setChecked(False)

    def on_actionQuadBezier(self):
        self.glcanvas.setMouseAction('COLLECTION')
        self.glcanvas.setCurveType('QUADBEZIER')
        self.actionSelect.setChecked(False)
        self.actionLine.setChecked(False)
        self.actionPolyLine.setChecked(False)
        self.actionQuadBezier.setChecked(True)
        self.actionCubicBezier.setChecked(False)
        self.actionCircle.setChecked(False)
        self.actionCircleArc.setChecked(False)

    def on_actionCubicBezier(self):
        self.glcanvas.setMouseAction('COLLECTION')
        self.glcanvas.setCurveType('CUBICBEZIER')
        self.actionSelect.setChecked(False)
        self.actionLine.setChecked(False)
        self.actionPolyLine.setChecked(False)
        self.actionQuadBezier.setChecked(False)
        self.actionCubicBezier.setChecked(True)
        self.actionCircle.setChecked(False)
        self.actionCircleArc.setChecked(False)

    def on_actionCircle(self):
        self.glcanvas.setMouseAction('COLLECTION')
        self.glcanvas.setCurveType('CIRCLE')
        self.actionSelect.setChecked(False)
        self.actionLine.setChecked(False)
        self.actionPolyLine.setChecked(False)
        self.actionQuadBezier.setChecked(False)
        self.actionCubicBezier.setChecked(False)
        self.actionCircle.setChecked(True)
        self.actionCircleArc.setChecked(False)

    def on_actionCircleArc(self):
        self.glcanvas.setMouseAction('COLLECTION')
        self.glcanvas.setCurveType('CIRCLEARC')
        self.actionSelect.setChecked(False)
        self.actionLine.setChecked(False)
        self.actionPolyLine.setChecked(False)
        self.actionQuadBezier.setChecked(False)
        self.actionCubicBezier.setChecked(False)
        self.actionCircle.setChecked(False)
        self.actionCircleArc.setChecked(True)

    ###########################################################
    #                                                         #
    #                     Grid Methods                        #
    #                                                         #
    ###########################################################
    def on_actionGrid(self):
        # Toggle grid visibility
        is_visible = self.grid.getDisplayInfo()
        self.grid.setDisplayInfo(not is_visible)
        self.actionGrid.setChecked(not is_visible)

        if not is_visible:
            # If turning on, show the dialog
            self.gridDialog.show()
        else:
            # If turning off, hide the dialog
            self.gridDialog.hide()

        self.glcanvas.resetGridDisplay()

    def gridChangeGrid(self):
        try:
            dX = float(self.gridDialog.lineEditXdir.text())
            dY = float(self.gridDialog.lineEditYdir.text())
            self.grid.setGridSpace(dX, dY)
        except ValueError:
            # Ignores invalid float values during typing
            pass

        isSnapOn = self.gridDialog.checkBoxSnap.isChecked()
        self.grid.setSnapInfo(isSnapOn)
        self.glcanvas.resetGridDisplay()

    def gridClose(self):
        # Just hide the dialog, do not turn off the grid
        self.gridDialog.hide()

    def gridCloseEvent(self):
        # When closing the dialog with 'X', also just hide it
        self.gridDialog.hide()

    ###########################################################
    #                                                         #
    #               Segment intersection/join                 #
    #                                                         #
    ###########################################################
    # Intersection of two selected segments
    def intersectSegments(self):
        # Delega para o HeController
        self.model.getHeController().intersectSelectedSegments()
        self.glcanvas.update()

    # Join two selected segments
    def joinSegments(self):
        # Delega para o HeController (se existir) ou mantém lógica antiga se necessário
        # self.model.getHeController().joinSelectedSegments()
        self.glcanvas.update()

    def on_actionSplit(self):
        # Verifica seleção via HeController
        if self.model.getHeController().getNumSelectedSegments() == 0:
            self.popupMessage("No segments selected.")
            return

        # Import the dialog here to avoid circular dependencies if any
        from splitdialog import SplitDialog
        
        dialog = SplitDialog(self)
        if dialog.exec():
            num_pieces = dialog.get_num_pieces()
            # Delega split para HeController
            self.model.getHeController().splitSelectedSegments(num_pieces)
            self.glcanvas.update()

    ###########################################################
    #                                                         #
    #                      Region creation                    #
    #                                                         #
    ###########################################################
    # Create region (patch) using selected segments
    def createRegion(self):
        # Delega diretamente para o HeController
        self.model.getHeController().createPatch()
        self.glcanvas.update()

    ###########################################################
    #                                                         #
    #                    Pop-up message                       #
    #                                                         #
    ###########################################################
    # Pop-up a message
    def popupMessage(self, _msgText):
        msg = QMessageBox()
        msg.setWindowTitle('Attention')
        msg.setIcon(QMessageBox.Warning)
        msg.setText(_msgText)
        msg.exec()

    ###########################################################
    #                                                         #
    #                    Métodos Mesh                         #
    #                                                         #
    ###########################################################

    def on_actionMeshSegment(self):
        self.meshSegmentDialog.show()
        self.actionMeshSegment.setChecked(True)

    def meshSegmentApply(self):
        try:
            n = int(self.meshSegmentDialog.lineEditNumSubdiv.text())
            r = float(self.meshSegmentDialog.lineEditRatio.text())
        except ValueError:
            return

        # Delega configuração de malha para HeController
        self.model.getHeController().setMeshParams(n, r)
        self.glcanvas.update()

    def meshSegmentClose(self):
        self.actionMeshSegment.setChecked(False)
        self.meshSegmentDialog.hide()

    def meshSegmentCloseEvent(self):
        self.actionMeshSegment.setChecked(False)

    def on_actionDomainMesh(self):
        isTurnedOn = self.meshPatch.getDisplayInfo()
        if not isTurnedOn:
            self.meshPatchDialog.show()
            self.meshPatch.setDisplayInfo(True)
            self.actionDomainMesh.setChecked(True)
        else:
            self.meshPatchDialog.hide()
            self.meshPatch.setDisplayInfo(False)
            self.actionDomainMesh.setChecked(False)

    def meshPatchApply(self):
        # Verifica qual opção foi selecionada no diálogo
        if self.meshPatchDialog.radioButtonBilinear.isChecked():
            type = MeshGenerator.TRANSFIN_BILINEAR
        elif self.meshPatchDialog.radioButtonTrilinear.isChecked():
            type = MeshGenerator.TRANSFIN_TRILINEAR
        elif self.meshPatchDialog.radioButtonDelaunay.isChecked():
            type = MeshGenerator.DELAUNAY_TRIANGULATION
        
        self.meshPatch.setMeshGenerator(type)
        
        # Obtém patches selecionados
        # Importante: Copiamos a lista porque a inserção de segmentos vai modificar 
        # a lista de patches do modelo (dividindo-os)
        selected_patches = list(self.model.getHeView().getSelectedPatches())
        
        he_controller = self.model.getHeController()

        # Lista para armazenar todas as arestas internas a serem criadas
        # Formato: [(x1, y1, x2, y2), ...]
        segments_to_insert = []

        for patch in selected_patches:
            patch.setSelected(False)
            
            # 1. Configura Loops
            loops = patch.getMeshLoops()
            if not self.meshPatch.setLoops(loops):
                self.popupMessage("Invalid patch configuration.")
                continue
            
            # 2. Obtém Pontos da Fronteira
            bdryPts = patch.getMeshBdryPoints()
            
            # 3. Gera Malha (Pontos e Conectividade)
            status, pts, conn = self.meshPatch.generateMesh(bdryPts)
            
            if status:
                # 4. Extrai arestas únicas da malha
                unique_edges = set()
                for tri in conn:
                    # tri = [id0, id1, id2]
                    for i in range(3):
                        u = tri[i]
                        v = tri[(i+1)%3]
                        # Ordena índices para garantir unicidade (u,v) == (v,u)
                        if u > v: u, v = v, u
                        unique_edges.add((u, v))
                
                # 5. Filtra arestas: Queremos apenas as INTERNAS
                # As arestas de contorno já existem no modelo.
                patch_segments = patch.getSegments()
                
                for u, v in unique_edges:
                    p1 = pts[u]
                    p2 = pts[v]
                    
                    # Calcula ponto médio da aresta candidata
                    mid_x = (p1.getX() + p2.getX()) / 2.0
                    mid_y = (p1.getY() + p2.getY()) / 2.0
                    mid_pt = Point(mid_x, mid_y)
                    
                    # Verifica se o ponto médio está muito próximo de algum segmento da borda original
                    is_boundary = False
                    for seg in patch_segments:
                        # Pega pontos do segmento existente
                        # Assumindo que seg tem getPoint(0) e getPoint(1) ou similar
                        # O HETool Segment geralmente tem getPoint(t)
                        s1 = seg.getPoint(0.0)
                        s2 = seg.getPoint(1.0)
                        
                        dist, _, _ = CompGeom.getClosestPointSegment(s1, s2, mid_pt)
                        if dist < 1e-3: # Tolerância pequena
                            is_boundary = True
                            break
                    
                    if not is_boundary:
                        segments_to_insert.append([p1.getX(), p1.getY(), p2.getX(), p2.getY()])
            else:
                self.popupMessage("Error generating mesh.")

        # 6. Insere os segmentos no modelo
        # Isso efetivamente "corta" as regiões, criando novas faces (patches)
        if segments_to_insert:
            # Desabilita atualizações visuais parciais para performance
            # (Se o HETool tiver suporte a batch, seria ideal, mas faremos um loop)
            count = 0
            total = len(segments_to_insert)
            print(f"Inserindo {total} arestas na malha...")
            
            for coords in segments_to_insert:
                he_controller.insertSegment(coords, self.glcanvas.pickTol)
                count += 1
                if count%10 == 0:
                    print(f"Processando...{count}/{total}")
            self.glcanvas.update()

    def meshPatchClose(self):
        self.actionDomainMesh.setChecked(False)
        self.meshPatch.setDisplayInfo(False)
        self.meshPatchDialog.hide()

    def meshPatchCloseEvent(self):
        self.actionDomainMesh.setChecked(False)
        self.meshPatch.setDisplayInfo(False)