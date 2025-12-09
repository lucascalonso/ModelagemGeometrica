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

    def initializeGL(self):
        glClearColor(1.0, 1.0, 1.0, 1.0)
        # CORREÇÃO: Desativamos o teste de profundidade para desenho 2D.
        # Isso garante que a ordem de desenho (Faces -> Linhas -> Pontos) seja respeitada.
        glDisable(GL_DEPTH_TEST) 
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, width, height):
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        if width <= height:
            aspect = float(height) / float(width)
            glOrtho(self.left, self.right, self.bottom * aspect, self.top * aspect, -1.0, 1.0)
        else:
            aspect = float(width) / float(height)
            glOrtho(self.left * aspect, self.right * aspect, self.bottom, self.top, -1.0, 1.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def _get_segments_safe(self):
        if hasattr(self.he_view, 'getSegments'): return self.he_view.getSegments()
        if hasattr(self.he_model, 'getSegments'): return self.he_model.getSegments()
        if hasattr(self.he_model, 'segments'): return self.he_model.segments
        return []

    def _get_patches_safe(self):
        if hasattr(self.he_view, 'getPatches'): return self.he_view.getPatches()
        if hasattr(self.he_model, 'getPatches'): return self.he_model.getPatches()
        if hasattr(self.he_model, 'patches'): return self.he_model.patches
        return []

    def _get_points_safe(self):
        if hasattr(self.he_model, 'points'): return self.he_model.points
        if hasattr(self.he_view, 'getPoints'): return self.he_view.getPoints()
        if hasattr(self.he_model, 'getPoints'): return self.he_model.getPoints()
        return []
    
    def _get_patch_points(self, patch):
        points = []
        if hasattr(patch, 'getPoints'):
            points = patch.getPoints()
            if points and len(points) > 0:
                return points

        try:
            if not hasattr(patch, 'face') or patch.face is None: return []
            start_he = patch.face.loop.he
            if start_he is None: return []
            curr_he = start_he
            while True:
                if curr_he.vertex and curr_he.vertex.point:
                    points.append(curr_he.vertex.point)
                curr_he = curr_he.next
                if curr_he == start_he or curr_he is None: break
        except Exception:
            return []
        return points

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT) 
        
        # 1. Grid (Fundo)
        if self.grid and self.grid.getDisplayInfo():
            self.drawGrid()

        # 2. Patches (Camada do meio - Preenchimento)
        patches = self._get_patches_safe()

        # --- DEBUG DIAGNÓSTICO BURACOS---
        if patches:
            print(f"\n--- DEBUG PAINT (Total: {len(patches)}) ---")
            for i, p in enumerate(patches):
                # Tenta pegar ID se existir
                pid = p.ID if hasattr(p, 'ID') else i
                status = "BURACO (isDeleted)" if p.isDeleted else "REGIÃO VÁLIDA"
                pts = self._get_patch_points(p)
                print(f"  Patch[{i}] ID={pid}: {status} | Pontos: {len(pts)}")
        # -------------------------
        
        if patches:
            # Separa patches em duas listas
            valid_patches = [p for p in patches if not p.isDeleted]
            deleted_patches = [p for p in patches if p.isDeleted]

            # PASSO A: Desenha Regiões Válidas (Verde/Vermelho)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            for patch in valid_patches:
                if patch.isSelected():
                    glColor4f(1.0, 0.0, 0.0, 0.3) # Vermelho
                else:
                    glColor4f(0.0, 0.8, 0.0, 0.3) # Verde

                pts = self._get_patch_points(patch)
                if pts and len(pts) >= 3:
                    glBegin(GL_POLYGON)
                    for p in pts:
                        px = p.getX() if hasattr(p, 'getX') else p.x
                        py = p.getY() if hasattr(p, 'getY') else p.y
                        glVertex2f(px, py)
                    glEnd()
            
            # PASSO B: Desenha Buracos (Branco Opaco) POR CIMA
            # Isso "apaga" visualmente a área do buraco
            glDisable(GL_BLEND)
            glColor3f(1.0, 1.0, 1.0) # Branco (Cor do Fundo)
            
            for patch in deleted_patches:
                pts = self._get_patch_points(patch)
                if pts and len(pts) >= 3:
                    glBegin(GL_POLYGON)
                    for p in pts:
                        px = p.getX() if hasattr(p, 'getX') else p.x
                        py = p.getY() if hasattr(p, 'getY') else p.y
                        glVertex2f(px, py)
                    glEnd()

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
            glColor3f(0.0, 0.0, 1.0)
            glPointSize(8.0)
            glBegin(GL_POINTS)
            for p in points:
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
            curr = self.mapFromGlobal(QtGui.QCursor.pos())
            currW = self.convertRasterPtToWorldCoords(curr)
            glVertex2f(currW.x(), currW.y())
            glEnd()

    def drawGrid(self):
        gridX, gridY = self.grid.getGridSpace()
        if gridX <= 0 or gridY <= 0: return
        if (self.right - self.left) / gridX > 200 or (self.top - self.bottom) / gridY > 200: return

        glColor3f(0.8, 0.8, 0.8)
        glPointSize(3.0)
        glBegin(GL_POINTS)
        start_x = math.floor(self.left / gridX) * gridX
        start_y = math.floor(self.bottom / gridY) * gridY
        x = start_x
        while x < self.right + gridX:
            y = start_y
            while y < self.top + gridY:
                glVertex2f(x, y)
                y += gridY
            x += gridX
        glEnd()
        
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(-gridX, 0); glVertex2f(gridX, 0)
        glVertex2f(0, -gridY); glVertex2f(0, gridY)
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

    # --- IMPLEMENTAÇÃO DE UNDO / REDO ---
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
            self.he_ctrl.delSelectedEntities()
            print("Delete executed")
            self.update()
            
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        self.mouseButton = event.button()
        self.pt0 = event.pos()
        maxSize = max(abs(self.right - self.left), abs(self.top - self.bottom))
        self.pickTol = maxSize * self.pickTolFac
        ptW = self.convertRasterPtToWorldCoords(self.pt0)
        xw, yw = ptW.x(), ptW.y()

        if self.curMouseAction == 'SELECTION':
            if self.mouseButton == QtCore.Qt.LeftButton:
                shift = (event.modifiers() & QtCore.Qt.ShiftModifier) == QtCore.Qt.ShiftModifier
                self.he_ctrl.selectPick(xw, yw, self.pickTol, shift)
                self.update()
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
                    snapped, sx, sy = self.snapToPoint(xw, yw, self.pickTol)
                    if snapped: xw, yw = sx, sy

                    if self.polyAnchor is None:
                        self.polyAnchor = (xw, yw)
                    else:
                        self.he_ctrl.insertSegment([self.polyAnchor[0], self.polyAnchor[1], xw, yw], self.pickTol)
                        if snapped: self.polyAnchor = None
                        else: self.polyAnchor = (xw, yw)
                    self.update()
                elif self.mouseButton == QtCore.Qt.RightButton:
                    self.polyAnchor = None
                    self.update()

    def mouseMoveEvent(self, event):
        if self.polyAnchor: self.update()

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

    def setMouseAction(self, action): self.curMouseAction = action
    def setCurveType(self, curveType):
        self.curveType = curveType
        self.polyAnchor = None
        
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
        self.resizeGL(self.width, self.height)
        self.update()
        
    def zoomIn(self):
        cx = (self.left + self.right) / 2; cy = (self.bottom + self.top) / 2
        dx = (self.right - self.left) * (1 - self.zoomFac)
        dy = (self.top - self.bottom) * (1 - self.zoomFac)
        self.left = cx - dx/2; self.right = cx + dx/2
        self.bottom = cy - dy/2; self.top = cy + dy/2
        self.resizeGL(self.width, self.height)
        self.update()
        
    def zoomOut(self):
        cx = (self.left + self.right) / 2; cy = (self.bottom + self.top) / 2
        dx = (self.right - self.left) * (1 + self.zoomFac)
        dy = (self.top - self.bottom) * (1 + self.zoomFac)
        self.left = cx - dx/2; self.right = cx + dx/2
        self.bottom = cy - dy/2; self.top = cy + dy/2
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panLeft(self):
        dx = (self.right - self.left) * self.panFac
        self.left -= dx; self.right -= dx
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panRight(self):
        dx = (self.right - self.left) * self.panFac
        self.left += dx; self.right += dx
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panUp(self):
        dy = (self.top - self.bottom) * self.panFac
        self.bottom += dy; self.top += dy
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panDown(self):
        dy = (self.top - self.bottom) * self.panFac
        self.bottom -= dy; self.top -= dy
        self.resizeGL(self.width, self.height)
        self.update()
    
    def setGrid(self, grid):
        self.grid = grid
    
    def resetGridDisplay(self):
        self.update()