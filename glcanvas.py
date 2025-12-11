from PySide6 import QtOpenGLWidgets, QtCore, QtGui
from OpenGL.GL import *
from OpenGL.GLU import *
import math

import sys
import os

hetool_path = os.path.join(os.path.dirname(__file__), 'HETool', 'src')
if hetool_path not in sys.path:
    sys.path.append(hetool_path)
from hetool.include.hetool import Hetool
from he_adapter import HetoolAdapter

from geometry.curves.quadbezier import QuadBezier
from geometry.curves.cubicbezier import CubicBezier
from geometry.curves.circle import Circle
from geometry.curves.circlearc import CircleArc
from hetool.geometry.point import Point

class GLCanvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self, _controller):
        super().__init__()
        self.controller = _controller
        
        # Atalhos para o HETool
        self.he_model = self.controller.model.getHeModel()
        self.he_ctrl = self.controller.model.getHeController()
        self.he_view = self.controller.model.getHeView() 

        # Configurações de visualização
        self.width = 0
        self.height = 0
        self.left = -10.0
        self.right = 10.0
        self.bottom = -10.0
        self.top = 10.0
        
        self.grid = None
        self.pt0 = QtCore.QPoint(0, 0)
        self.panFac = 0.01
        self.zoomFac = 0.1
        self.pickTol = 0.1
        self.pickTolFac = 0.015

        self.mouseButton = QtCore.Qt.NoButton
        self.curMouseAction = 'SELECTION'
        self.curveType = 'LINE'
        self.polyAnchor = None
        self.currentCurve = None

        self.panActive = False
        self.lastPanPos = QtCore.QPoint(0, 0)
        self.mousePos = QtCore.QPoint(0, 0)

        self.isSelecting = False
        self.mouseMoveTol = 5

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glDisable(GL_DEPTH_TEST) 
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, width, height):
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        self.update()

    def _get_segments_safe(self):
        if hasattr(self.he_model, 'getSegments'): return self.he_model.getSegments()
        if hasattr(self.he_model, 'segments'): return self.he_model.segments
        if hasattr(self.he_view, 'getSegments'): return self.he_view.getSegments()
        return []

    def _get_patches_safe(self):
        if hasattr(self.he_model, 'getPatches'): return self.he_model.getPatches()
        if hasattr(self.he_model, 'patches'): return self.he_model.patches
        if hasattr(self.he_view, 'getPatches'): return self.he_view.getPatches()
        return []

    def _get_points_safe(self):
        if hasattr(self.he_model, 'getPoints'): return self.he_model.getPoints()
        if hasattr(self.he_model, 'points'): return self.he_model.points
        if hasattr(self.he_view, 'getPoints'): return self.he_view.getPoints()
        return []
    
    def _get_patch_points(self, patch):
        # 1. Tenta extrair da topologia (Face -> Loop -> HalfEdge)
        # Isso garante que desenhamos a geometria atualizada após cortes/splits
        try:
            if hasattr(patch, 'face') and patch.face is not None:
                points = []
                # Assume que patch.face.loop é o loop externo
                start_he = patch.face.loop.he
                if start_he is not None:
                    curr_he = start_he
                    while True:
                        if curr_he.vertex and curr_he.vertex.point:
                            points.append(curr_he.vertex.point)
                        curr_he = curr_he.next
                        if curr_he == start_he or curr_he is None: break
                
                if len(points) >= 3:
                    return points
        except Exception:
            pass

        # 2. Fallback: Se não tiver topologia (ex: patch isolado ou em construção), usa getPoints armazenado
        if hasattr(patch, 'getPoints'):
            points = patch.getPoints()
            if points and len(points) > 0:
                return points
        return []

    def paintGL(self):

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if self.width <= self.height:
            aspect = float(self.height) / float(self.width) if self.width > 0 else 1.0
            glOrtho(self.left, self.right, self.bottom * aspect, self.top * aspect, -1.0, 1.0)
        else:
            aspect = float(self.width) / float(self.height) if self.height > 0 else 1.0
            glOrtho(self.left * aspect, self.right * aspect, self.bottom, self.top, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glClear(GL_COLOR_BUFFER_BIT) 
        
        # 1. Grid (Fundo)
        if self.grid and self.grid.getDisplayInfo():
            self.drawGrid()

        # 2. Patches (Camada do meio - Preenchimento)
        patches = self._get_patches_safe()
        
        if patches:
            valid_patches = [p for p in patches if not p.isDeleted]
            deleted_patches = [p for p in patches if p.isDeleted]

            # PASSO A: Desenha Regiões Válidas
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            # NOTA: Removemos glBegin(GL_TRIANGLES) daqui pois o drawPatchWithTess gerencia isso internamente
            
            for patch in valid_patches:
                
                # Verificação robusta de isUnlimited (funciona se for método ou propriedade)
                is_unlim = False
                if hasattr(patch, 'isUnlimited'):
                    attr = getattr(patch, 'isUnlimited')
                    is_unlim = attr() if callable(attr) else attr
                
                if is_unlim:
                    continue

                if patch.isSelected():
                    glColor4f(1.0, 0.0, 0.0, 0.3) # Vermelho
                else:
                    glColor4f(0.0, 0.8, 0.0, 0.3) # Verde

                # Desenha o fundo colorido do patch
                self.drawPatchWithTess(self._get_patch_points(patch))

                # Se o patch tiver uma malha gerada, desenha ela por cima
                if hasattr(patch, 'mesh') and patch.mesh:
                    self.drawMesh(patch.mesh)
            
            # PASSO B: Desenha Buracos (Branco Opaco)
            glDisable(GL_BLEND)
            glColor3f(1.0, 1.0, 1.0)
            
            for patch in deleted_patches:
                # Verificação robusta de isUnlimited (funciona se for método ou propriedade)
                is_unlim = False
                if hasattr(patch, 'isUnlimited'):
                    attr = getattr(patch, 'isUnlimited')
                    is_unlim = attr() if callable(attr) else attr
                
                if is_unlim:
                    continue
                self.drawPatchWithTess(self._get_patch_points(patch))

        # 3. Segmentos (Camada superior - Linhas)
        segments = self._get_segments_safe()
        if segments:
            glLineWidth(2.0)
            for seg in segments:
                if seg.isSelected():
                    glColor3f(1.0, 0.0, 0.0)
                else:
                    glColor3f(0.0, 0.0, 0.0)

                pts = []
                if hasattr(seg, 'getPointsToDraw'): pts = seg.getPointsToDraw()
                elif hasattr(seg, 'getPoints'): pts = seg.getPoints()
                
                if pts:
                    glBegin(GL_LINE_STRIP)
                    for p in pts:
                        if hasattr(p, 'getX'): glVertex2f(p.getX(), p.getY())
                        elif hasattr(p, 'x'): glVertex2f(p.x, p.y)
                        elif isinstance(p, (list, tuple)): glVertex2f(p[0], p[1])
                    glEnd()

        # 4. Vértices (Topo - Pontos)
        points = self._get_points_safe()
        if points:
            glPointSize(8.0)
            glBegin(GL_POINTS)
            for p in points:
                # Lógica de visualização de seleção para vértices
                is_selected = False
                if hasattr(p, 'isSelected'):
                    is_selected = p.isSelected()
                
                if is_selected:
                    glColor3f(1.0, 0.0, 0.0) # Vermelho se selecionado
                else:
                    glColor3f(0.0, 0.0, 1.0) # Azul padrão

                px = p.getX() if hasattr(p, 'getX') else p.x
                py = p.getY() if hasattr(p, 'getY') else p.y
                glVertex2f(px, py)
            glEnd()

        # 5. Preview
        if self.polyAnchor:
            glColor3f(0.5, 0.5, 0.5)
            glLineWidth(1.0)
            glBegin(GL_LINES)
            glVertex2f(self.polyAnchor[0], self.polyAnchor[1])
            
            curr = self.mousePos
            currW = self.convertRasterPtToWorldCoords(curr)
            cx, cy = currW.x(), currW.y()
            
            cx, cy = self.snapToGridOrPoint(cx, cy)
            
            glVertex2f(cx, cy)
            glEnd()
        
        if self.currentCurve:
            glColor3f(0.5, 0.5, 0.5)
            glLineWidth(1.0)
            
            # Pega posição atual do mouse com Snap
            curr = self.mousePos
            currW = self.convertRasterPtToWorldCoords(curr)
            cx, cy = currW.x(), currW.y()
            cx, cy = self.snapToGridOrPoint(cx, cy)
            mousePt = Point(cx, cy)
            
            # Gera o preview dinâmico
            preview_pts = self.currentCurve.getEquivPolylineCollecting(mousePt)
            
            if preview_pts:
                glBegin(GL_LINE_STRIP)
                for p in preview_pts:
                    glVertex2f(p.getX(), p.getY())
                glEnd()
        
        # 6. Retângulo de Seleção
        if self.isSelecting and self.curMouseAction == 'SELECTION':
            glEnable(GL_BLEND)
            pt0W = self.convertRasterPtToWorldCoords(self.pt0)
            currW = self.convertRasterPtToWorldCoords(self.mousePos)
            
            xmin = min(pt0W.x(), currW.x())
            xmax = max(pt0W.x(), currW.x())
            ymin = min(pt0W.y(), currW.y())
            ymax = max(pt0W.y(), currW.y())

            glColor4f(0.0, 0.0, 1.0, 0.1)
            glBegin(GL_QUADS)
            glVertex2f(xmin, ymin)
            glVertex2f(xmax, ymin)
            glVertex2f(xmax, ymax)
            glVertex2f(xmin, ymax)
            glEnd()

            glColor3f(0.0, 0.0, 1.0)
            glLineWidth(1.0)
            glBegin(GL_LINE_LOOP)
            glVertex2f(xmin, ymin)
            glVertex2f(xmax, ymin)
            glVertex2f(xmax, ymax)
            glVertex2f(xmin, ymax)
            glEnd()

    def drawGrid(self):
        gridX, gridY = self.grid.getGridSpace()
        if gridX <= 0 or gridY <= 0: return

        if self.width <= self.height:
            aspect = float(self.height) / float(self.width) if self.width > 0 else 1.0
            vis_left, vis_right = self.left, self.right
            vis_bottom, vis_top = self.bottom * aspect, self.top * aspect
        else:
            aspect = float(self.width) / float(self.height) if self.height > 0 else 1.0
            vis_left, vis_right = self.left * aspect, self.right * aspect
            vis_bottom, vis_top = self.bottom, self.top

        if (vis_right - vis_left) / gridX > 200 or (vis_top - vis_bottom) / gridY > 200: return

        glColor3f(0.8, 0.8, 0.8)
        glPointSize(5.0)
        glBegin(GL_POINTS)
        
        start_x = math.floor(vis_left / gridX) * gridX
        start_y = math.floor(vis_bottom / gridY) * gridY
        
        x = start_x
        while x < vis_right + gridX:
            y = start_y
            while y < vis_top + gridY:
                glVertex2f(x, y)
                y += gridY
            x += gridX
        glEnd()
        
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(vis_left, 0); glVertex2f(vis_right, 0)
        glVertex2f(0, vis_bottom); glVertex2f(0, vis_top)
        glEnd()

    def snapToPoint(self, x, y, tol):
        points = self._get_points_safe()
        if not points: return False, x, y
        snapped = False
        sx, sy = x, y
        min_dist = tol
        for p in points:
            px = p.getX() if hasattr(p, 'getX') else p.x
            py = p.getY() if hasattr(p, 'getY') else p.y
            dist = math.sqrt((px - x)**2 + (py - y)**2)
            if dist < min_dist:
                min_dist = dist
                sx, sy = px, py
                snapped = True
        return snapped, sx, sy
    
    def snapToGridOrPoint(self, x, y):
        # Atualiza tolerância baseada no zoom atual
        maxSize = max(abs(self.right - self.left), abs(self.top - self.bottom))
        tol = maxSize * self.pickTolFac
        
        # 1. Snap aos pontos existentes (prioridade)
        snapped, sx, sy = self.snapToPoint(x, y, tol)
        if snapped: return sx, sy
        
        # 2. Snap ao Grid (se habilitado)
        if self.grid and self.grid.getSnapInfo():
            sx, sy = self.grid.snapTo(x, y)
            return sx, sy
            
        return x, y

    def keyPressEvent(self, event):
        # Ctrl + Z = Undo
        if event.key() == QtCore.Qt.Key_Z and (event.modifiers() & QtCore.Qt.ControlModifier):
            # Ctrl + Shift + Z = Redo
            if event.modifiers() & QtCore.Qt.ShiftModifier:
                self.he_ctrl.redo()
                print("Redo executed")
            else:
                self.he_ctrl.undo()
                print("Undo executed")
            self.update()
        
        # Ctrl + Y = Redo
        elif event.key() == QtCore.Qt.Key_Y and (event.modifiers() & QtCore.Qt.ControlModifier):
            self.he_ctrl.redo()
            print("Redo executed")
            self.update()

        # Delete ou Backspace = Deletar Seleção
        elif event.key() == QtCore.Qt.Key_Delete or event.key() == QtCore.Qt.Key_Backspace:
            
            if self.he_view:
                selected_points = self.he_view.getSelectedPoints()
                for pt in selected_points:
                    incident_segments = self.he_view.getIncidentSegmentsFromPoint(pt)
                    if incident_segments:
                        for seg in incident_segments:
                            seg.setSelected(True)

            self.he_ctrl.delSelectedEntities()
            print("Delete executed")
            self.update()
            self.repaint()
            
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.mouseButton = event.button()
        self.pt0 = event.pos()
        self.mousePos = event.pos()

        if self.mouseButton == QtCore.Qt.MiddleButton:
            self.panActive = True
            self.lastPanPos = event.pos()
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            return
            
        maxSize = max(abs(self.right - self.left), abs(self.top - self.bottom))
        self.pickTol = maxSize * self.pickTolFac
        ptW = self.convertRasterPtToWorldCoords(self.pt0)
        xw, yw = ptW.x(), ptW.y()

        if self.curMouseAction == 'COLLECTION':
            xw, yw = self.snapToGridOrPoint(xw, yw)
        
        if self.curMouseAction == 'COLLECTION' and self.curveType in ['QUADBEZIER', 'CUBICBEZIER', 'CIRCLE', 'CIRCLEARC']:
            if self.currentCurve is None:
                # Factory: Cria a instância correta
                if self.curveType == 'QUADBEZIER': self.currentCurve = QuadBezier()
                elif self.curveType == 'CUBICBEZIER': self.currentCurve = CubicBezier()
                elif self.curveType == 'CIRCLE': self.currentCurve = Circle()
                elif self.curveType == 'CIRCLEARC': self.currentCurve = CircleArc()
            
            # Adiciona o ponto clicado
            self.currentCurve.addCtrlPoint(xw, yw)
            
            # Verifica se a curva está completa
            is_done = False
            if self.curveType == 'QUADBEZIER' and self.currentCurve.nPts == 3: is_done = True
            elif self.curveType == 'CUBICBEZIER' and self.currentCurve.nPts == 4: is_done = True
            elif self.curveType == 'CIRCLE' and self.currentCurve.nPts == 2: is_done = True
            elif self.curveType == 'CIRCLEARC' and self.currentCurve.nPts == 3: is_done = True
            
            if is_done:
                # Discretiza a curva em segmentos de linha
                poly_pts = self.currentCurve.getEquivPolyline()
                
                # Insere os segmentos no HETool
                if len(poly_pts) >= 2:
                    for i in range(len(poly_pts) - 1):
                        p1 = poly_pts[i]
                        p2 = poly_pts[i+1]
                        
                        dx = p2.getX() - p1.getX()
                        dy = p2.getY() - p1.getY()
                        dist = math.sqrt(dx*dx + dy*dy)
                        if dist > 1e-10:
                            self.he_ctrl.insertSegment([p1.getX(), p1.getY(), p2.getX(), p2.getY()], self.pickTol)
                
                self.currentCurve = None # Reseta para a próxima
            
            self.update()
            return

        if self.curMouseAction == 'SELECTION':
            if self.mouseButton == QtCore.Qt.LeftButton:
                self.isSelecting = True
            return

        if self.curMouseAction == 'COLLECTION':
            if self.curveType == 'LINE':
                if self.polyAnchor is None:
                    self.polyAnchor = (xw, yw)
                else:
                    self.he_ctrl.insertSegment([self.polyAnchor[0], self.polyAnchor[1], xw, yw], self.pickTol)
                    self.polyAnchor = None
                self.update()

            elif self.curveType == 'POLYLINE':
                if self.mouseButton == QtCore.Qt.LeftButton:
                    if self.polyAnchor is None:
                        self.polyAnchor = (xw, yw)
                    else:
                        self.he_ctrl.insertSegment([self.polyAnchor[0], self.polyAnchor[1], xw, yw], self.pickTol)
                        self.polyAnchor = (xw, yw)
                    self.update()
                elif self.mouseButton == QtCore.Qt.RightButton:
                    self.polyAnchor = None
                    self.update()

    def mouseMoveEvent(self, event):
        self.mousePos = event.pos()
        
        if self.isSelecting:
            self.update()
            return

        if self.panActive:
            dx = event.x() - self.lastPanPos.x()
            dy = event.y() - self.lastPanPos.y()
            
            worldWidth = self.right - self.left
            worldHeight = self.top - self.bottom
            
            scaleX = worldWidth / self.width if self.width > 0 else 1.0
            scaleY = worldHeight / self.height if self.height > 0 else 1.0
            
            if self.width <= self.height:
                aspect = float(self.height) / float(self.width) if self.width > 0 else 1.0
                scaleY = (self.top - self.bottom) * aspect / self.height
            else:
                aspect = float(self.width) / float(self.height) if self.height > 0 else 1.0
                scaleX = (self.right - self.left) * aspect / self.width

            self.left -= dx * scaleX
            self.right -= dx * scaleX
            self.bottom += dy * scaleY
            self.top += dy * scaleY

            self.lastPanPos = event.pos()
            self.update()
            return
        
        if self.polyAnchor: self.update()
        if self.currentCurve: self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.MiddleButton:
            self.panActive = False
            self.setCursor(QtCore.Qt.ArrowCursor)
            
        if self.isSelecting and event.button() == QtCore.Qt.LeftButton:
            self.isSelecting = False
            
            diff = event.pos() - self.pt0
            dist = diff.manhattanLength()
            
            shift = (event.modifiers() & QtCore.Qt.ShiftModifier) == QtCore.Qt.ShiftModifier
            
            if dist <= self.mouseMoveTol:
                
                ptW = self.convertRasterPtToWorldCoords(event.pos())
                self.he_ctrl.selectPick(ptW.x(), ptW.y(), self.pickTol, shift)
            else:
                
                pt0W = self.convertRasterPtToWorldCoords(self.pt0)
                pt1W = self.convertRasterPtToWorldCoords(event.pos())
                
                xmin = min(pt0W.x(), pt1W.x())
                xmax = max(pt0W.x(), pt1W.x())
                ymin = min(pt0W.y(), pt1W.y())
                ymax = max(pt0W.y(), pt1W.y())
                
                self.he_ctrl.selectFence(xmin, xmax, ymin, ymax, shift)
            
            self.update()

    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoomIn()
        else:
            self.zoomOut()

    def convertRasterPtToWorldCoords(self, _pt):
        w = self.width
        h = self.height
        if w == 0 or h == 0: return QtCore.QPointF(0,0)
        x_ratio = float(_pt.x()) / w
        y_ratio = float(h - _pt.y()) / h
        if w <= h:
            aspect = float(h) / float(w)
            wx = self.left + x_ratio * (self.right - self.left)
            wy = (self.bottom * aspect) + y_ratio * ((self.top - self.bottom) * aspect)
        else:
            aspect = float(w) / float(h)
            wx = (self.left * aspect) + x_ratio * ((self.right - self.left) * aspect)
            wy = self.bottom + y_ratio * (self.top - self.bottom)
        return QtCore.QPointF(wx, wy)

    def setMouseAction(self, action): 
        self.curMouseAction = action
        self.polyAnchor = None
        self.update()

    def setCurveType(self, curveType):
        self.curveType = curveType
        self.polyAnchor = None
        self.currentCurve = None
        self.update()
        
    def fitWorldToViewport(self):
        points = self._get_points_safe()
        if not points: return
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        for p in points:
            px = p.getX() if hasattr(p, 'getX') else p.x
            py = p.getY() if hasattr(p, 'getY') else p.y
            if px < min_x: min_x = px
            if px > max_x: max_x = px
            if py < min_y: min_y = py
            if py > max_y: max_y = py
        if min_x == float('inf'): return
        margin = 1.1
        cx = (min_x + max_x) / 2; cy = (min_y + max_y) / 2
        dx = (max_x - min_x) * margin; dy = (max_y - min_y) * margin
        if dx < 1.0: dx = 10.0
        if dy < 1.0: dy = 10.0
        self.left = cx - dx/2; self.right = cx + dx/2
        self.bottom = cy - dy/2; self.top = cy + dy/2
        self.update()
        
    def zoomIn(self):
        cx = (self.left + self.right) / 2; cy = (self.bottom + self.top) / 2
        dx = (self.right - self.left) * (1 - self.zoomFac)
        dy = (self.top - self.bottom) * (1 - self.zoomFac)
        self.left = cx - dx/2; self.right = cx + dx/2
        self.bottom = cy - dy/2; self.top = cy + dy/2
        self.update()
        
    def zoomOut(self):
        cx = (self.left + self.right) / 2; cy = (self.bottom + self.top) / 2
        dx = (self.right - self.left) * (1 + self.zoomFac)
        dy = (self.top - self.bottom) * (1 + self.zoomFac)
        self.left = cx - dx/2; self.right = cx + dx/2
        self.bottom = cy - dy/2; self.top = cy + dy/2
        self.update()
        
    def panLeft(self):
        dx = (self.right - self.left) * self.panFac
        self.left -= dx; self.right -= dx
        self.update()
        
    def panRight(self):
        dx = (self.right - self.left) * self.panFac
        self.left += dx; self.right += dx
        self.update()
        
    def panUp(self):
        dy = (self.top - self.bottom) * self.panFac
        self.bottom += dy; self.top += dy
        self.update()
        
    def panDown(self):
        dy = (self.top - self.bottom) * self.panFac
        self.bottom -= dy; self.top -= dy
        self.update()
    
    def setGrid(self, grid):
        self.grid = grid
    
    def resetGridDisplay(self):
        self.update()
    
    def drawPatchWithTess(self, points):
        if not points or len(points) < 3: return

        try:
            # Cria objeto tessellator
            tess = gluNewTess()
            
            # Define callbacks para o OpenGL desenhar os triângulos gerados
            gluTessCallback(tess, GLU_TESS_BEGIN, glBegin)
            gluTessCallback(tess, GLU_TESS_VERTEX, glVertex3dv)
            gluTessCallback(tess, GLU_TESS_END, glEnd)
            
            # Inicia definição do polígono
            gluTessBeginPolygon(tess, None)
            gluTessBeginContour(tess)
            
            for p in points:
                # Garante coordenadas numéricas
                x = p.getX() if hasattr(p, 'getX') else p.x
                y = p.getY() if hasattr(p, 'getY') else p.y
                # Z=0 para 2D. O tessellator precisa de 3 coordenadas.
                v = [float(x), float(y), 0.0]
                gluTessVertex(tess, v, v)
                
            gluTessEndContour(tess)
            gluTessEndPolygon(tess)
            gluDeleteTess(tess)
        except Exception as e:
            print(f"Erro no Tessellator: {e}")

    def drawMesh(self, mesh):
        if not mesh: return
        pts, conn = mesh
        
        # Configura cor para as linhas da malha (Cinza Escuro/Preto)
        glColor3f(0.2, 0.2, 0.2) 
        glLineWidth(1.0)
        
        # Desenha cada triângulo da malha como um loop de linhas (Wireframe)
        for tri in conn:
            # tri é uma lista de índices [i, j, k]
            p0 = pts[tri[0]]
            p1 = pts[tri[1]]
            p2 = pts[tri[2]]
            
            glBegin(GL_LINE_LOOP)
            glVertex2f(p0.getX(), p0.getY())
            glVertex2f(p1.getX(), p1.getY())
            glVertex2f(p2.getX(), p2.getY())
            glEnd()