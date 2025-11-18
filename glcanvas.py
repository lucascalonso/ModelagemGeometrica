from PySide6 import QtOpenGLWidgets, QtCore, QtGui
from OpenGL.GL import *
from numpy import reshape
from compgeom.tesselation import Tesselation


class GLCanvas(QtOpenGLWidgets.QOpenGLWidget):

    def __init__(self, _controller=[], _view=[], _collector=[], _reshape=[]):
        super(GLCanvas, self).__init__()

        # canvas sizes and model clipping window limits
        self.width = 0   # width of canvas (horizontal raster size)
        self.height = 0  # height of canvas (vertical raster size)
        self.left = -10.0    # left limit of clipping window (world)
        self.right = 10.0    # right limit of clipping window (world)
        self.bottom = -10.0  # bottom limit of clipping window (world)
        self.top = 10.0      # top limit of clipping window (world)

        # canvas aggregation objects
        self.controller = _controller  # handle to app controller
        self.view = _view  # handle to app view
        self.grid = None  # grid object associated to canvas
        self.collector = _collector  # collector of curves on canvas
        self.reshape = _reshape  # reshaper of curves on canvas

        # OpenGL display lists and display update flags
        self.viewDsp = 0  # GL list index for model display
        self.updatedDsp = False  # if true, model display is updated
        self.gridDsp = 0  # GL list index for grid display
        self.updatedGridDsp = False  # if true, grid display is updated

        # factors for moving (pan) and zooming (in or out) clipping
        # window (world) with respect to current window sizes
        self.panFac = 0.1
        self.zoomFac = 0.1

        # mouse related properties
        # (Mouse buttons: QCore.Qt.LeftButton, QCore.Qt.RightButton, and
        #  QCore.Qt.MidButton)
        self.mouseButton = QtCore.Qt.NoButton
        self.mousebuttonPressed = False  # if true, mouse button is pressed
        self.mouseDoubleClick = False  # if true, mouse button double click
        self.pt0 = QtCore.QPoint(0, 0)  # mouse position at button press event
        self.pt1 = QtCore.QPoint(0, 0)  # current mouse position
        self.pickTolFac = 0.015  # factor for pick tolerance
        self.pickTol = 0.0  # tolerance for picking in world coordinates
        self.mouseMoveTol = 2  # tolerance for mouse move
        self.curMouseAction = 'SELECTION'  # SELECTION, COLLECTION, RESHAPE

        # Current curve being reshaped and picked control point id
        self.reshapeCurve = None
        self.reshapeCtrlPtId = -1

        # Mouse pan move properties
        self.panMoveOn = False  # flag for mouse pan move
        self.panMovePrevPt = QtCore.QPoint(0, 0)  # previous mouse move position

        # Pressed key properties
        self.shiftKeyPressed = False
        self.controlKeyPressed = False

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # --------------------GENERAL PROPERTY METHODS-------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    def setController(self, _controller):
        self.controller = _controller

    # ---------------------------------------------------------------------
    def getController(self):
        return self.controller

    # ---------------------------------------------------------------------
    def setView(self, _view):
        self.view = _view

    # ---------------------------------------------------------------------
    def getView(self):
        return self.view

    # ---------------------------------------------------------------------
    def setGrid(self, _grid):
        self.grid = _grid

    # ---------------------------------------------------------------------
    def getGrid(self):
        return self.grid

    # ---------------------------------------------------------------------
    def resetViewDisplay(self):
        if self.view is None:
            return
        self.updatedDsp = False
        self.update()

    # ---------------------------------------------------------------------
    def resetGridDisplay(self):
        if self.grid is None:
            return
        self.updatedGridDsp = False
        self.update()

    # ---------------------------------------------------------------------
    def setMouseAction(self, _action):
        if self.curMouseAction == _action:
            return
        if _action == 'SELECTION':
            self.curMouseAction = 'SELECTION'
        elif _action == 'COLLECTION':
            self.curMouseAction = 'COLLECTION'
        elif _action == 'RESHAPE':
            self.curMouseAction = 'RESHAPE'
        self.view.unselectAll()
        self.collector.reset()
        self.reshape.reset()
        self.updatedDsp = False
        self.update()

    # ---------------------------------------------------------------------
    def setCurveType(self, _type):
        if ((self.curMouseAction == 'COLLECTION') and
                (self.collector.getCurveType() == _type)):
            return
        self.collector.setCurveType(_type)

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # --------------------CANVAS PREDEFINED SLOTS--------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    def initializeGL(self):
        # set canvas background color
        color = self.view.getColorBackground()
        glClearColor(color[0], color[1], color[2], 1.0)
        glClear(GL_COLOR_BUFFER_BIT)

        # set some graphics primitives attributes
        glEnable(GL_LINE_SMOOTH)
 
    # ---------------------------------------------------------------------
    def resizeGL(self, _width, _height):

        # Avoid division by zero
        if _width == 0:
            _width = 1

        # store GL canvas sizes in object properties
        self.width = _width
        self.height = _height

        # Setup the viewport to canvas dimesions
        glViewport(0, 0, self.width, self.height)

        # reset the coordinate system
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()

        # Establish the clipping window in world model coordinates
        # based on model bounding box, and set up an orthographic projection
        self.fitWorldToViewport()


    # MÉTODOS PARA VER AS LINHAS ANTES DE CRIAR
    # ---------------------------------------------------------------------
    def setPreviewSegment(self, _startWorld, _xEnd, _yEnd):
        """
        Armazena segmento de pré-visualização em coordenadas de mundo.
        _startWorld: Pnt2D ou QtCore.QPointF (ponto inicial)
        _xEnd, _yEnd: coordenadas finais em mundo (float)
        """
        from compgeom.pnt2d import Pnt2D
        # Normalize _startWorld to Pnt2D
        if _startWorld is None:
            self.previewLine = None
            return
        if isinstance(_startWorld, Pnt2D):
            p0 = Pnt2D(_startWorld.getX(), _startWorld.getY())
        else:
            # assume QPointF-like
            try:
                p0 = Pnt2D(float(_startWorld.x()), float(_startWorld.y()))
            except Exception:
                p0 = Pnt2D(float(_startWorld[0]), float(_startWorld[1]))
        p1 = Pnt2D(float(_xEnd), float(_yEnd))
        self.previewLine = (p0, p1)
        # solicitar redraw
        self.update()

    # ---------------------------------------------------------------------
    def clearPreviewSegment(self):
        """Remove pré-visualização (chame ao finalizar inserção)."""
        self.previewLine = None
        self.update()
    # ---------------------------------------------------------------------
    def paintGL(self):

        # reset the coordinate system
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(self.left, self.right, self.bottom, self.top, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        # clear the buffer with the current color
        glClear(GL_COLOR_BUFFER_BIT)

        # Display view (if there is one), storing it in a display list
        if (self.view is not None) and not(self.view.isEmpty()):
            if not self.updatedDsp:
                if self.viewDsp > 0:
                    glDeleteLists(self.viewDsp, 1)
                self.viewDsp = self.makeDisplayView()

            if self.viewDsp > 0:
                glCallList(self.viewDsp)
                self.updatedDsp = True

        # Display grid (if it is visible)
        gridIsTurnedOn = self.grid.getDisplayInfo()
        if gridIsTurnedOn:
            if not self.updatedGridDsp:
                if self.gridDsp > 0:
                    glDeleteLists(self.gridDsp, 1)
                self.gridDsp = self.makeDisplayGrid()

            if self.gridDsp > 0:
                glCallList(self.gridDsp)
                self.updatedGridDsp = True

        if self.curMouseAction == 'SELECTION' and not self.panMoveOn:
            # Check to see whether there is selection fence and,
            # if that is the case, draw it
            fenceDsp = self.drawSelectionFence()
            if fenceDsp > 0:
                glCallList(fenceDsp)
                glDeleteLists(fenceDsp, 1)
        elif self.curMouseAction == 'COLLECTION':
            # Check to see whether there is a segment being collected and,
            # if that is the case, draw it
            collectDsp = self.drawCollectedCurve()
            if collectDsp > 0:
                glCallList(collectDsp)
                glDeleteLists(collectDsp, 1)
        elif self.curMouseAction == 'RESHAPE':
            # Check to see whether there is a curve being reshaped and,
            # if that is the case, draw the segment owned by this curve
            if self.reshapeCurve is not None:
                reshapeDsp = self.drawReshapeCurve()
                glCallList(reshapeDsp)
                glDeleteLists(reshapeDsp, 1)

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # -----------------------DISPLAY FUNCTIONS-----------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    def drawPatches(self):
        patches = self.view.getPatches()
        for ptch in patches:
            if self.view.isPatchSelected(ptch):
                color = self.view.getColorPatchSelection()
            else:
                color = self.view.getColorPatch()
            glColor3f(color[0], color[1], color[2])
            pts = self.view.getPatchPts(ptch)
            if len(pts) == 3:
                glBegin(GL_TRIANGLES)
                glVertex2f(pts[0].getX(), pts[0].getY())
                glVertex2f(pts[1].getX(), pts[1].getY())
                glVertex2f(pts[2].getX(), pts[2].getY())
                glEnd()
            else:
                # Without tesselation
                # glBegin(GL_POLYGON)
                # for j in range(len(pts)):
                #     glVertex2d(pts[j].getX(),
                #                pts[j].getY())
                # glEnd()
                # With tesselation
                triangs = Tesselation.tessellate(pts)
                for j in range(0, len(triangs)):
                    glBegin(GL_TRIANGLES)
                    glVertex2d(pts[triangs[j][0]].getX(),
                               pts[triangs[j][0]].getY())
                    glVertex2d(pts[triangs[j][1]].getX(),
                               pts[triangs[j][1]].getY())
                    glVertex2d(pts[triangs[j][2]].getX(),
                               pts[triangs[j][2]].getY())
                    glEnd()
                # Draw tesselation triangles
                # glColor3d(0.50, 0.50, 0.50)
                # for j in range(0, len(triangs)):
                #     glBegin(GL_LINE_LOOP)
                #     glVertex2d(pts[triangs[j][0]].getX(),
                #                pts[triangs[j][0]].getY())
                #     glVertex2d(pts[triangs[j][1]].getX(),
                #                pts[triangs[j][1]].getY())
                #     glVertex2d(pts[triangs[j][2]].getX(),
                #                pts[triangs[j][2]].getY())
                #     glEnd()

    # ---------------------------------------------------------------------
    def drawSegments(self):
        segments = self.view.getSegments()
        for seg in segments:
            # Draw segment polyline
            if self.view.isSegmentSelected(seg):
                color = self.view.getColorSegmentSelection()
            else:
                color = self.view.getColorSegment()
            glColor3f(color[0], color[1], color[2])
            pts = self.view.getSegmentPts(seg)
            glLineWidth(0.5)
            glBegin(GL_LINE_STRIP)
            for j in range(len(pts)):
                glVertex2f(pts[j].getX(), pts[j].getY())
            glEnd()

    # ---------------------------------------------------------------------
    def drawPoints(self):
        points = self.view.getPoints()
        glPointSize(6.0)
        glBegin(GL_POINTS)
        for pnt in points:
            if self.view.isPointSelected(pnt):
                color = self.view.getColorPointSelection()
            else:
                color = self.view.getColorPoint()
            glColor3f(color[0], color[1], color[2])
            pt = self.view.getPointLoc(pnt)
            glVertex2f(pt.getX(), pt.getY())
        glEnd()

    # ---------------------------------------------------------------------
    def makeDisplayView(self):
        if (self.view is None) or (self.view.isEmpty()):
            return 0

        list = glGenLists(1)
        glNewList(list, GL_COMPILE)
        self.drawPatches()
        self.drawSegments()
        self.drawPoints()
        glEndList()
        return list

    # ---------------------------------------------------------------------
    def makeDisplayGrid(self):
        oX = 0.0
        oY = 0.0
        x = self.left
        y = self.bottom
        gridX, gridY = self.grid.getGridSpace()

        if (gridX == 0.0) or (gridY == 0.0):
            return 0

        #  treatment for multiple zoom out
        if((((self.right - self.left) / gridX) > 150) or
           (((self.top - self.bottom) / gridY) > 150)):
            return 0

        list = glGenLists(1)
        glNewList(list, GL_COMPILE)
        color = self.view.getColorGrid()
        glColor3f(color[0], color[1], color[2])

        # Display grid points
        glPointSize(5.0)
        glBegin(GL_POINTS)
        x = oX - (int((oX - self.left) / gridX) * gridX) - gridX
        while x <= self.right:
            y = oY - (int((oY - self.bottom) / gridY) * gridY) - gridY
            while y <= self.top:
                glVertex2f(x, y)
                y += gridY
            x += gridX
        glEnd()

        # Display crossed lines at origin
        glLineWidth(0.5)
        glBegin(GL_LINES)
        x = oX - gridX * 0.5
        y = oY
        glVertex2f(x, y)
        x = oX + gridX * 0.5
        y = oY
        glVertex2f(x, y)
        x = oX
        y = oY - gridY * 0.5
        glVertex2f(x, y)
        x = oX
        y = oY + gridY * 0.5
        glVertex2f(x, y)
        glEnd()

        glEndList()
        return list

    # ---------------------------------------------------------------------
    def drawSelectionFence(self):
        # It is assumed that the current mouse action is for segment selection
        # Only draw a fence if mouse button is presse
        if not self.mousebuttonPressed:
            return 0

        # If current mouse point is in the same position of initial mouse point
        # do not display anything
        if (self.pt0.x() == self.pt1.x() and self.pt0.y() == self.pt1.y()):
            return 0

        # Display a fence from initial mouse point to current mouse point
        list = glGenLists(1)
        glNewList(list, GL_COMPILE)
        glLineWidth(0.5)
        color = self.view.getColorSelection()
        glColor3f(color[0], color[1], color[2])
        glBegin(GL_LINE_STRIP)
        pt0W = self.convertRasterPtToWorldCoords(self.pt0)
        pt1W = self.convertRasterPtToWorldCoords(self.pt1)
        glVertex2f(pt0W.x(), pt0W.y())
        glVertex2f(pt1W.x(), pt0W.y())
        glVertex2f(pt1W.x(), pt1W.y())
        glVertex2f(pt0W.x(), pt1W.y())
        glVertex2f(pt0W.x(), pt0W.y())
        glEnd()

        glEndList()
        return list

    # ---------------------------------------------------------------------
    def drawCollectedCurve(self):
        # It is assumed that the current mouse
        # action if for segment collection

        crvPts = self.collector.getDrawPoints()
        ctrlPts = self.collector.getCtrlPoints()

        if (crvPts is None) and (ctrlPts is None):
            return 0

        list = glGenLists(1)
        glNewList(list, GL_COMPILE)

        color = self.view.getColorCollecting()
        glColor3f(color[0], color[1], color[2])

        # Display lines of segment being collected
        if crvPts is not None:
            glLineWidth(0.5)
            glBegin(GL_LINE_STRIP)

            for i in range(0, len(crvPts)):
                glVertex2f(crvPts[i].getX(), crvPts[i].getY())
            glEnd()

        # Display control points of segment being collected
        if ctrlPts is not None:
            glPointSize(6.0)
            glBegin(GL_POINTS)
            for i in range(0, len(ctrlPts)):
                glVertex2f(ctrlPts[i].getX(), ctrlPts[i].getY())
            glEnd()

        glEndList()
        return list

    # ---------------------------------------------------------------------
    def drawReshapeCurve(self):
        # It is assumed that the current mouse
        # action if for curve reshape
        if self.reshapeCurve is None:
            return 0

        list = glGenLists(1)
        glNewList(list, GL_COMPILE)

        color = self.view.getColorSegmentSelection()
        glColor3f(color[0], color[1], color[2])

        # Display the segment that is owned by curve being reshaped
        reshapeSeg = self.view.getCurveSegment(self.reshapeCurve)
        pts = self.view.getSegmentPts(reshapeSeg)
        glLineWidth(0.5)
        glBegin(GL_LINE_STRIP)
        for i in range(0, len(pts)):
            glVertex2f(pts[i].getX(), pts[i].getY())
        glEnd()

        # Display control points of curve being reshaped
        glPointSize(6.0)
        glBegin(GL_POINTS)
        ctrlPts = self.reshapeCurve.getReshapeCtrlPoints()
        for i in range(0, len(ctrlPts)):
            glVertex2f(ctrlPts[i].getX(), ctrlPts[i].getY())
        glEnd()
 
        glEndList()
        return list

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # -----------FUNCTIONS TO MANAGE VISUALIZATION WINDOW LIMITS-----------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    def scaleWorldWindow(self, _scaleFac):
        # Compute canvas viewport aspect ratio
        try:
            vpr = self.height / self.width
        except ZeroDivisionError:
            vpr = 1.0

        # Get clipping window center
        cx = (self.left + self.right) / 2.0
        cy = (self.bottom + self.top) / 2.0

        # Scale clipping window size
        sizex = (self.right - self.left) * _scaleFac
        sizey = (self.top - self.bottom) * _scaleFac

        # Adjust window size to keep aspect ratio
        if sizey > (vpr * sizex):
            sizex = sizey / vpr
        else:
            sizey = sizex * vpr

        # Update clipping window limits
        self.left = cx - (sizex * 0.5)
        self.right = cx + (sizex * 0.5)
        self.bottom = cy - (sizey * 0.5)
        self.top = cy + (sizey * 0.5)

        self.updatedGridDsp = False
        self.update()

    # ---------------------------------------------------------------------
    def panWorldWindow(self, _panX, _panY):
        # Update clipping window limits
        self.left += _panX
        self.right += _panX
        self.bottom += _panY
        self.top += _panY

        self.updatedGridDsp = False
        self.update()


    # ---------------------------------------------------------------------
    def fitWorldToViewport(self):
        # Setup world space window limits based on model bounding box
        if (self.view is None) and (self.view.isEmpty()):
            self.scaleWorldWindow(1.0)
        else:
            self.left, self.right, self.bottom, self.top = self.view.getBoundBox()
            scaleFac = 1.0 + self.zoomFac
            self.scaleWorldWindow(scaleFac)

    # ---------------------------------------------------------------------
    def zoomIn(self):
        if self.view is None:
            return
        # Scale down clipping window
        scaleFac = 1.0 - self.zoomFac
        if scaleFac <= 0.0:
            scaleFac = 0.01
        self.scaleWorldWindow(scaleFac)

    # ---------------------------------------------------------------------
    def zoomOut(self):
        if self.view is None:
            return
        # Scale up clipping window
        scaleFac = 1.0 + self.zoomFac
        self.scaleWorldWindow(scaleFac)

    # ---------------------------------------------------------------------
    def panLeft(self):
        if self.view is None:
            return
        pan = (self.right - self.left) * self.panFac
        self.panWorldWindow(-pan, 0.0)

    # ---------------------------------------------------------------------
    def panRight(self):
        if self.view is None:
            return
        pan = (self.right - self.left) * self.panFac
        self.panWorldWindow(pan, 0.0)

    # ---------------------------------------------------------------------
    def panDown(self):
        if self.view is None:
            return
        pan = (self.top - self.bottom) * self.panFac
        self.panWorldWindow(0.0, -pan)

    # ---------------------------------------------------------------------
    def panUp(self):
        if self.view is None:
            return
        pan = (self.top - self.bottom) * self.panFac
        self.panWorldWindow(0.0, pan)

    # ---------------------------------------------------------------------
    def panMouseMove(self):
        # Convert previous and current mouse raster positions to world coords
        ptPrevW = self.convertRasterPtToWorldCoords(self.panMovePrevPt)
        pt1W = self.convertRasterPtToWorldCoords(self.pt1)

        # Shift clipping window by delta between previous and current world points
        dx = ptPrevW.x() - pt1W.x()
        dy = ptPrevW.y() - pt1W.y()
        self.panWorldWindow(dx, dy)

    # ---------------------------------------------------------------------
    

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # --------FUNCTION TO CONVERT POINT FROM RASTER TO WORLD COORDS--------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    def convertRasterPtToWorldCoords(self, _pt):
        # Prevent division by zero if widget not yet sized
        w = max(1, self.width)
        h = max(1, self.height)

        dX = self.right - self.left
        dY = self.top - self.bottom

        # Convert raster (left-top origin) to world coords (left-bottom origin)
        mX = _pt.x() * dX / w
        my = (h - _pt.y()) * dY / h
        x = self.left + mX
        y = self.bottom + my
        return QtCore.QPointF(x, y)
    # ---------------------------------------------------------------------
    

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------FUNCTION TO SNAP POINT TO GRID, POINT, OR SEGMENT-----------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    def snapPtToGridOrEntity(self, _pt):
        snapped = False
        xW = _pt.x()
        yW = _pt.y()

        # Snap point to grid (if it is visible). Also check for
        # snap-to-grid flag (which will be inverted by control key)
        gridIsTurnedOn = self.grid.getDisplayInfo()
        if gridIsTurnedOn:
            isSnapOn = self.grid.getSnapInfo()
            if ((not self.controlKeyPressed and isSnapOn) or
               (self.controlKeyPressed and not isSnapOn)):
                xW, yW = self.grid.snapTo(xW, yW)
                snapped = True

        # Try to attract point to a segment
        if (self.view is not None) and not(self.view.isEmpty()):
            check, _x, _y = self.view.snapToSegment(xW, yW, self.pickTol)
            if check:
                xW = _x
                yW = _y
            snapped = snapped or check

        # Try to attract point to current curve being collected
        check, _x, _y = self.collector.snapToCurrentCurve(xW, yW, self.pickTol)
        if check:
            xW = _x
            yW = _y
        snapped = snapped or check

        # Try to attract point to a point
        if (self.view is not None) and not(self.view.isEmpty()):
            check, _x, _y = self.view.snapToPoint(xW, yW, self.pickTol)
            if check:
                xW = _x
                yW = _y
            snapped = snapped or check

        return snapped, xW, yW

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ----------------------MOUSE EVENT SLOTS------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    def mousePressEvent(self, event):
        self.mouseButton = event.button()
        self.mousebuttonPressed = True
        self.mouseDoubleClick = False
        self.pt0 = event.pos()

        # Atualiza pick tolerance para este ciclo
        try:
            maxSize = max(abs(self.right - self.left), abs(self.top - self.bottom))
            self.pickTol = maxSize * self.pickTolFac
        except Exception:
            self.pickTol = 0.0

        # PAN (botão do meio)
        if self.mouseButton == QtCore.Qt.MiddleButton:
            self.setCursor(QtGui.QCursor(QtCore.Qt.SizeAllCursor))
            self.panMovePrevPt = self.pt0
            self.panMoveOn = True
            return

        # SELEÇÃO: press apenas inicia fence (o processamento está no release)
        if self.curMouseAction == 'SELECTION':
            return

        # Converte posição do clique para coordenadas de mundo
        try:
            pt0W = self.convertRasterPtToWorldCoords(self.pt0)
        except Exception:
            pt0W = QtCore.QPointF(0.0, 0.0)

        # COLETA
        if self.curMouseAction == 'COLLECTION':
            crvType = ''
            try:
                crvType = self.collector.getCurveType()
            except Exception:
                crvType = ''

            # Tratamento explícito para POLYLINE: cada clique esquerdo comita uma linha
            if crvType == 'POLYLINE':
                # garante atributo âncora
                if not hasattr(self, 'polyAnchor'):
                    self.polyAnchor = None

                if self.mouseButton == QtCore.Qt.LeftButton:
                    snapped, xW, yW = self.snapPtToGridOrEntity(pt0W)

                    # 1º clique: define âncora e inicia preview
                    if self.polyAnchor is None:
                        self.polyAnchor = (xW, yW)
                        try:
                            self.collector.reset()
                            self.collector.setCurveType('POLYLINE')
                            self.collector.startCollection()
                            self.collector.insertCtrlPoint(xW, yW, self.pickTol)
                        except Exception:
                            pass
                        self.update()
                        return

                    # Demais cliques: monta polyline de 2 pontos e comita; âncora avança
                    ax, ay = self.polyAnchor
                    try:
                        # Commit: usa collector para criar e finalizar uma polyline de 2 pts
                        self.collector.reset()
                        self.collector.setCurveType('POLYLINE')
                        self.collector.startCollection()
                        self.collector.insertCtrlPoint(ax, ay, self.pickTol)
                        self.collector.insertCtrlPoint(xW, yW, self.pickTol)
                        self.collector.endCollection(self.pickTol)
                    except Exception:
                        # Não interrompe interação se falhar
                        pass

                    # Reabre preview com nova âncora
                    self.polyAnchor = (xW, yW)
                    try:
                        self.collector.reset()
                        self.collector.setCurveType('POLYLINE')
                        self.collector.startCollection()
                        self.collector.insertCtrlPoint(xW, yW, self.pickTol)
                    except Exception:
                        pass

                    self.updatedDsp = False
                    self.update()
                    return

                if self.mouseButton == QtCore.Qt.RightButton:
                    # Encerrar corrente: limpa preview e âncora; mantém modo POLYLINE
                    try:
                        self.collector.reset()
                    except Exception:
                        pass
                    self.polyAnchor = None
                    self.updatedDsp = False
                    self.update()
                    return

            # Demais curvas (finita): fluxo padrão
            if self.mouseButton == QtCore.Qt.LeftButton:
                if not getattr(self.collector, 'isActive', lambda: False)():
                    try:
                        self.collector.startCollection()
                    except Exception:
                        pass

                snapped, xW, yW = self.snapPtToGridOrEntity(pt0W)
                try:
                    self.collector.insertCtrlPoint(xW, yW, self.pickTol)
                except Exception:
                    pass

                try:
                    if not getattr(self.collector, 'isUnlimited', lambda: False)() and \
                    getattr(self.collector, 'hasFinished', lambda: False)():
                        try:
                            self.collector.endCollection(self.pickTol)
                        except Exception:
                            pass
                        self.updatedDsp = False
                        self.update()
                    else:
                        self.update()
                except Exception:
                    self.update()
                return

            if self.mouseButton == QtCore.Qt.RightButton:
                try:
                    self.collector.reset()
                except Exception:
                    pass
                self.update()
                return

        # RESHAPE: pick do ponto de controle
        if self.curMouseAction == 'RESHAPE' and self.mouseButton == QtCore.Qt.LeftButton:
            pt0W = self.convertRasterPtToWorldCoords(self.pt0)
            if self.reshapeCurve is not None:
                self.reshapeCtrlPtId = self.view.pickReshapeCurveCtrlPoint(
                    self.reshapeCurve, pt0W.x(), pt0W.y(), self.pickTol)
                if self.reshapeCtrlPtId > -1:
                    self.reshape.setCtrlPointId(self.reshapeCtrlPtId)
    # ---------------------------------------------------------------------
    def mouseMoveEvent(self, event):
        # Posição atual do mouse
        self.pt1 = event.pos()

        # PAN em movimento
        if self.panMoveOn:
            self.panMouseMove()
            self.panMovePrevPt = self.pt1
            return

        # SELEÇÃO: redesenha fence enquanto move com botão esquerdo
        if self.curMouseAction == 'SELECTION':
            if self.mouseButton == QtCore.Qt.LeftButton:
                self.update()
            return

        # Converte posição atual para coords de mundo
        pt1W = self.convertRasterPtToWorldCoords(self.pt1)

        # COLETA
        if self.curMouseAction == 'COLLECTION':
            crvType = ''
            try:
                crvType = self.collector.getCurveType()
            except Exception:
                crvType = ''

            # POLYLINE: preview âncora -> cursor (não comita aqui)
            if crvType == 'POLYLINE':
                if not hasattr(self, 'polyAnchor'):
                    self.polyAnchor = None

                # Evita atualizar enquanto um botão está pressionado
                if self.mousebuttonPressed:
                    return

                snapped, xW, yW = self.snapPtToGridOrEntity(pt1W)

                try:
                    self.collector.reset()
                    self.collector.setCurveType('POLYLINE')
                    self.collector.startCollection()
                    if self.polyAnchor is not None:
                        ax, ay = self.polyAnchor
                        self.collector.insertCtrlPoint(ax, ay, self.pickTol)
                        self.collector.addTempCtrlPoint(xW, yW)
                    else:
                        # Sem âncora ainda: mostra possível início
                        self.collector.insertCtrlPoint(xW, yW, self.pickTol)
                except Exception:
                    pass
                self.update()
                return

            # Demais curvas (finita): preview padrão
            else:
                if self.mousebuttonPressed:
                    return
                snapped, xW, yW = self.snapPtToGridOrEntity(pt1W)
                try:
                    self.collector.addTempCtrlPoint(xW, yW)
                except Exception:
                    pass
                self.update()
                return

        # RESHAPE: mover ponto de controle selecionado
        if (self.curMouseAction == 'RESHAPE' and
            self.mousebuttonPressed and
            self.mouseButton == QtCore.Qt.LeftButton):
            if self.reshapeCurve is not None and self.reshapeCtrlPtId > -1:
                snapped, xW, yW = self.snapPtToGridOrEntity(pt1W)
                try:
                    self.reshape.changeCtrlPoint(xW, yW, self.pickTol)
                except Exception:
                    pass
                self.update()
            return
    # ---------------------------------------------------------------------
    def mouseReleaseEvent(self, event):
        self.mousebuttonPressed = False
        if self.mouseDoubleClick:
            return

        btn = event.button()

        # Finaliza pan
        if self.panMoveOn:
            self.panMoveOn = False
            self.setCursor(QtGui.QCursor(QtCore.Qt.ArrowCursor))
            return

        # SELEÇÃO: pick ou fence
        if self.curMouseAction == 'SELECTION':
            if btn == QtCore.Qt.LeftButton:
                self.pt1 = event.pos()

                pt0W = self.convertRasterPtToWorldCoords(self.pt0)
                pt1W = self.convertRasterPtToWorldCoords(self.pt1)

                if ((abs(self.pt0.x() - self.pt1.x()) <= self.mouseMoveTol) and
                    (abs(self.pt0.y() - self.pt1.y()) <= self.mouseMoveTol)):
                    try:
                        self.view.selectPick(pt1W.x(), pt1W.y(), self.pickTol,
                                            self.shiftKeyPressed)
                    except Exception:
                        pass
                else:
                    xmin = min(pt0W.x(), pt1W.x())
                    xmax = max(pt0W.x(), pt1W.x())
                    ymin = min(pt0W.y(), pt1W.y())
                    ymax = max(pt0W.y(), pt1W.y())
                    try:
                        self.view.selectFence(xmin, xmax, ymin, ymax,
                                            self.shiftKeyPressed)
                    except Exception:
                        pass
                self.updatedDsp = False
                self.update()
            return

        # COLLECTION: tudo já tratado no press
        if self.curMouseAction == 'COLLECTION':
            return

        # RESHAPE: confirma/cancela reshape
        if self.curMouseAction == 'RESHAPE':
            if btn == QtCore.Qt.RightButton:
                self.reshapeCurve = None
                self.reshapeCtrlPtId = -1
                try:
                    self.reshape.reset()
                except Exception:
                    pass
                try:
                    self.setMouseAction('SELECTION')
                except Exception:
                    pass
            elif btn == QtCore.Qt.LeftButton:
                self.updatedDsp = False
                self.update()
            return

    # ---------------------------------------------------------------------
    
    # ---------------------------------------------------------------------
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    # ---------------------------------------------------------------------
    def mouseDoubleClickEvent(self, event):
        self.mouseDoubleClick = True
        if self.curMouseAction == 'SELECTION':
            if self.mouseButton == QtCore.Qt.LeftButton:

                # Get current mouse raster position
                ptR = event.pos()

                # Convert mouse position to world coordinates
                ptW = self.convertRasterPtToWorldCoords(ptR)

                # Try to pick a segment for curve reshape
                self.reshapeCurve = self.view.selectReshapeCurve(ptW.x(), ptW.y(),
                                                                 self.pickTol)

                # If picked a segment, set mouse action for curve reshape
                if self.reshapeCurve is not None:
                    self.setMouseAction('RESHAPE')
                    self.reshape.startReshape(self.reshapeCurve)
                    self.view.unselectAll()
                    self.updatedDsp = False
                    self.update()

    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ----------------------KEYBOARD EVENT SLOTS---------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------
    # ---------------------------------------------------------------------

    # ---------------------------------------------------------------------
    def keyPressEvent(self, event):
        self.shiftKeyPressed = (event.key() == QtCore.Qt.Key_Shift)
        self.controlKeyPressed = (event.key() == QtCore.Qt.Key_Control)

    # ---------------------------------------------------------------------
    def keyReleaseEvent(self, event):
        self.shiftKeyPressed = False
        self.controlKeyPressed = False

        # If Escape key was pressed and released, and current collected
        # curve has no limit in the number of points, verify whether
        # previously collected points can finish collection of current curve.
        if event.key() == QtCore.Qt.Key_Escape:
            if self.curMouseAction == 'COLLECTION':
                endCollection = False
                if self.collector.isUnlimited() and self.collector.hasFinished():
                    endCollection = True
                else:
                    # If Escape key was pressed, and previously collected
                    # points cannot finish collection of curve, reset current
                    # curve collection.
                    if not self.collector.isCollecting():
                        # If there is no previously collected point, setup selection
                        # mouse action.
                        self.controller.on_actionSelect()
                    self.collector.reset()
                    self.update()

                if endCollection:
                    self.collector.endCollection(self.pickTol)
                    self.updatedDsp = False
                    self.update()

            elif self.curMouseAction == 'RESHAPE':
                self.reshapeCurve = None
                self.reshapeCtrlPtId = -1
                self.reshape.reset()
                self.setMouseAction('SELECTION')
                self.view.unselectAll()
                self.updatedDsp = False
                self.update()

        # If Delete key was pressed, if in selection mode, delete the 
        # selected entities.
        if event.key() == QtCore.Qt.Key_Delete:
            if self.curMouseAction == 'SELECTION':
                self.view.delSelectEntities()
                self.resetViewDisplay()
                self.update()