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


class AppController(QMainWindow, Ui_MyApp):
    def __init__(self):
        super().__init__()
        super().setupUi(self)

        # Create model object, view object, and curve collector object
        self.model = AppModel(self)
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

        # Create an OpenGL canvas and associate to the
        # canvas widget
        self.glcanvas = GLCanvas(self, self.view, self.collector, self.reshape)
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

        
    ###########################################################
    #                                                         #
    #             Program close callback method               #
    #                                                         #
    ###########################################################
    def closeEvent(self, _event):
        self.gridDialog.close()
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
        self.view.delSelectEntities()
        self.glcanvas.resetViewDisplay()

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
        self.model.intersectSelectedSegments()
        self.glcanvas.resetViewDisplay()

    # Join two selected segments
    #def joinSegments(self):
    #    self.model.joinSelectedSegments()
    #    self.glcanvas.resetViewDisplay()

    ###########################################################
    #                                                         #
    #                      Region creation                    #
    #                                                         #
    ###########################################################
    # Create region (patch) using selected segments
    def createRegion(self):
        self.model.createPatch()
        self.glcanvas.resetViewDisplay()

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

    def joinSegments(self):
        self.view.joinSelectedSegments(self.glcanvas.pickTol)
        self.glcanvas.resetViewDisplay()

    def on_actionSplit(self):
        # Use the new method to check if any segments are selected
        if self.view.getNumSelectedSegments() == 0:
            self.popupMessage("No segments selected.")
            return

        # Import the dialog here to avoid circular dependencies if any
        from splitdialog import SplitDialog
        
        dialog = SplitDialog(self)
        if dialog.exec():
            num_pieces = dialog.get_num_pieces()
            self.view.splitSelectedSegments(num_pieces)
            self.glcanvas.resetViewDisplay()
