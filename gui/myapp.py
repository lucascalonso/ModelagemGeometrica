from PySide6.QtWidgets import QMainWindow, QToolBar, QWidget
from PySide6.QtGui import QAction

class Ui_MyApp(object):
    def setupUi(self, MainWindow: QMainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setWindowTitle("Trabalho 4 - Lucas Alonso Correia")
        MainWindow.setGeometry(100, 100, 800, 600)

        # Central widget para o canvas
        self.canvas = QWidget(MainWindow)
        self.canvas.setObjectName("canvas")
        MainWindow.setCentralWidget(self.canvas)

        # --- Criação das Toolbars ---
        # Toolbar de Controle de Visualização
        viewToolbar = QToolBar("Visualização", MainWindow)
        MainWindow.addToolBar(viewToolbar)

        # Toolbar de Controle de Modelagem
        modelToolbar = QToolBar("Modelagem", MainWindow)
        MainWindow.addToolBar(modelToolbar)

        # --- Ações de Visualização ---
        self.actionFit = QAction("Fit", MainWindow)
        viewToolbar.addAction(self.actionFit)

        self.actionZoomIn = QAction("Zoom In", MainWindow)
        viewToolbar.addAction(self.actionZoomIn)

        self.actionZoomOut = QAction("Zoom Out", MainWindow)
        viewToolbar.addAction(self.actionZoomOut)

        self.actionPanLeft = QAction("Pan Left", MainWindow)
        viewToolbar.addAction(self.actionPanLeft)

        self.actionPanRight = QAction("Pan Right", MainWindow)
        viewToolbar.addAction(self.actionPanRight)

        self.actionPanUp = QAction("Pan Up", MainWindow)
        viewToolbar.addAction(self.actionPanUp)

        self.actionPanDown = QAction("Pan Down", MainWindow)
        viewToolbar.addAction(self.actionPanDown)

        # --- Ações de Modelagem ---
        self.actionSelect = QAction("Select", MainWindow)
        self.actionSelect.setCheckable(True)
        modelToolbar.addAction(self.actionSelect)

        self.actionDelete = QAction("Delete", MainWindow)
        modelToolbar.addAction(self.actionDelete)

        modelToolbar.addSeparator()

        self.actionLine = QAction("Line", MainWindow)
        self.actionLine.setCheckable(True)
        modelToolbar.addAction(self.actionLine)

        self.actionPolyLine = QAction("PolyLine", MainWindow)
        self.actionPolyLine.setCheckable(True)
        modelToolbar.addAction(self.actionPolyLine)

        self.actionQuadBezier = QAction("Quad Bezier", MainWindow)
        self.actionQuadBezier.setCheckable(True)
        modelToolbar.addAction(self.actionQuadBezier)

        self.actionCubicBezier = QAction("Cubic Bezier", MainWindow)
        self.actionCubicBezier.setCheckable(True)
        modelToolbar.addAction(self.actionCubicBezier)

        self.actionCircle = QAction("Circle", MainWindow)
        self.actionCircle.setCheckable(True)
        modelToolbar.addAction(self.actionCircle)

        self.actionCircleArc = QAction("Circle Arc", MainWindow)
        self.actionCircleArc.setCheckable(True)
        modelToolbar.addAction(self.actionCircleArc)

        modelToolbar.addSeparator()

        self.actionGrid = QAction("Grid", MainWindow)
        self.actionGrid.setCheckable(True)
        modelToolbar.addAction(self.actionGrid)

        self.actionIntersect = QAction("Intersect", MainWindow)
        modelToolbar.addAction(self.actionIntersect)

        self.actionJoin = QAction("Join", MainWindow)
        modelToolbar.addAction(self.actionJoin)

        self.actionSplit = QAction("Split Segments", MainWindow)
        modelToolbar.addAction(self.actionSplit)

        self.actionCreateRegion = QAction("Create Region", MainWindow)
        modelToolbar.addAction(self.actionCreateRegion)
