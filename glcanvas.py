from PySide6 import QtOpenGLWidgets, QtCore, QtGui
from OpenGL.GL import *
from OpenGL.GLU import *
import math

class GLCanvas(QtOpenGLWidgets.QOpenGLWidget):
    def __init__(self, _controller):
        super().__init__()
        self.controller = _controller
        
        # Atalhos para o HETool
        self.he_model = self.controller.model.getHeModel()
        self.he_ctrl = self.controller.model.getHeController()
        # Tentamos obter a view, mas usamos com cautela
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
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_POINT_SMOOTH)
        glEnable(GL_LINE_SMOOTH)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, width, height):
        self.width = width
        self.height = height
        glViewport(0, 0, width, height)
        
        # Atualiza a projeção
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
        """Helper para obter segmentos de forma segura"""
        if hasattr(self.he_view, 'getSegments'):
            return self.he_view.getSegments()
        if hasattr(self.he_model, 'getSegments'):
            return self.he_model.getSegments()
        if hasattr(self.he_model, 'segments'):
            return self.he_model.segments
        return []

    def _get_patches_safe(self):
        """Helper para obter patches de forma segura"""
        if hasattr(self.he_view, 'getPatches'):
            return self.he_view.getPatches()
        if hasattr(self.he_model, 'getPatches'):
            return self.he_model.getPatches()
        if hasattr(self.he_model, 'patches'):
            return self.he_model.patches
        return []

    def _get_points_safe(self):
        """Helper para obter pontos de forma segura"""
        if hasattr(self.he_model, 'points'): # HeController usa hemodel.points
            return self.he_model.points
        if hasattr(self.he_view, 'getPoints'):
            return self.he_view.getPoints()
        if hasattr(self.he_model, 'getPoints'):
            return self.he_model.getPoints()
        return []

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 1. Desenha o Grid (se existir e estiver ligado)
        if self.grid and self.grid.getDisplayInfo():
            self.drawGrid()

        # 2. Desenha os Patches (Regiões)
        # IMPORTANTE: Desenhamos antes dos segmentos para o preenchimento ficar no fundo
        patches = self._get_patches_safe()

        # --- DEBUG: VERIFICAÇÃO DE PATCHES ---
        # Verifique o terminal após fechar uma região.
        if patches:
            print(f"--- DEBUG PAINT: Total Patches = {len(patches)} ---")
            for i, p in enumerate(patches):
                pts = p.getPoints() if hasattr(p, 'getPoints') else []
                status = "BURACO (isDeleted)" if p.isDeleted else "REGIÃO VÁLIDA"
                print(f"  Patch {i}: {status} | Pontos: {len(pts)}")
        else:
            # print("--- DEBUG PAINT: Nenhum patch encontrado ---")
            pass

        if patches:
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            
            for patch in patches:
                # DEBUG: Desenha TUDO para vermos se está criando.
                # Se isDeleted (Buraco) -> Amarelo fraco
                # Se !isDeleted (Região) -> Verde forte
                
                if patch.isDeleted:
                    # Buraco (região fechada mas não "criada")
                    glColor4f(1.0, 1.0, 0.0, 0.3) 
                else:
                    # Região válida
                    if patch.isSelected():
                        glColor4f(1.0, 0.0, 0.0, 0.6) # Vermelho se selecionado
                    else:
                        glColor4f(0.0, 0.8, 0.0, 0.5) # Verde se normal

                # Obtém os pontos do contorno do patch
                pts = []
                if hasattr(patch, 'getPoints'):
                    pts = patch.getPoints()
                
                if pts and len(pts) >= 3:
                    # Desenha o polígono preenchido
                    glBegin(GL_POLYGON)
                    for p in pts:
                        # Extrai coordenadas X, Y de forma segura
                        px = p.getX() if hasattr(p, 'getX') else p.x
                        py = p.getY() if hasattr(p, 'getY') else p.y
                        glVertex2f(px, py)
                    glEnd()
            
            glDisable(GL_BLEND)

        # 3. Desenha os Segmentos do HETool
        segments = self._get_segments_safe()
        if segments:
            glLineWidth(2.0)
            for seg in segments:
                # Define cor baseada na seleção
                if seg.isSelected():
                    glColor3f(1.0, 0.0, 0.0) # Vermelho se selecionado
                else:
                    glColor3f(0.0, 0.0, 0.0) # Preto normal

                # Desenha a geometria do segmento
                pts = []
                if hasattr(seg, 'getPointsToDraw'):
                    pts = seg.getPointsToDraw()
                elif hasattr(seg, 'getPoints'):
                    pts = seg.getPoints()
                
                if pts:
                    glBegin(GL_LINE_STRIP)
                    for p in pts:
                        # Compatibilidade com diferentes tipos de Ponto
                        if hasattr(p, 'getX'):
                            glVertex2f(p.getX(), p.getY())
                        elif hasattr(p, 'x'):
                            glVertex2f(p.x, p.y)
                        elif isinstance(p, (list, tuple)):
                            glVertex2f(p[0], p[1])
                    glEnd()

        # 4. Desenha Vértices (Pontos) - NOVO
        points = self._get_points_safe()
        if points:
            glColor3f(0.0, 0.0, 1.0) # Azul
            glPointSize(12.0) # Pontos grandes
            glBegin(GL_POINTS)
            for p in points:
                px = p.getX() if hasattr(p, 'getX') else p.x
                py = p.getY() if hasattr(p, 'getY') else p.y
                glVertex2f(px, py)
            glEnd()

        # 5. Desenha Preview (Polilinha em construção)
        if self.polyAnchor:
            glColor3f(0.5, 0.5, 0.5)
            glLineWidth(1.0)
            glBegin(GL_LINES)
            glVertex2f(self.polyAnchor[0], self.polyAnchor[1])
            # Pega posição atual do mouse convertida
            curr = self.mapFromGlobal(QtGui.QCursor.pos())
            currW = self.convertRasterPtToWorldCoords(curr)
            glVertex2f(currW.x(), currW.y())
            glEnd()

    def drawGrid(self):
        gridX, gridY = self.grid.getGridSpace()
        if gridX <= 0 or gridY <= 0:
            return

        # Evita desenhar se muito denso (zoom out excessivo)
        if (self.right - self.left) / gridX > 200 or (self.top - self.bottom) / gridY > 200:
            return

        glColor3f(0.8, 0.8, 0.8) # Cinza claro
        glPointSize(3.0)
        
        glBegin(GL_POINTS)
        
        # Calcula limites visíveis alinhados ao grid
        start_x = math.floor(self.left / gridX) * gridX
        start_y = math.floor(self.bottom / gridY) * gridY
        
        # Desenha pontos
        x = start_x
        while x < self.right + gridX:
            y = start_y
            while y < self.top + gridY:
                glVertex2f(x, y)
                y += gridY
            x += gridX
        glEnd()
        
        # Desenha cruz na origem
        glColor3f(0.0, 0.0, 0.0)
        glLineWidth(1.0)
        glBegin(GL_LINES)
        glVertex2f(-gridX, 0)
        glVertex2f(gridX, 0)
        glVertex2f(0, -gridY)
        glVertex2f(0, gridY)
        glEnd()

    def snapToPoint(self, x, y, tol):
        """Implementação manual de snap para pontos do modelo"""
        points = self._get_points_safe()
        if not points:
            return False, x, y
            
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

    def mousePressEvent(self, event):
        self.mouseButton = event.button()
        self.pt0 = event.pos()
        
        # Calcula tolerância de pick baseada no zoom
        maxSize = max(abs(self.right - self.left), abs(self.top - self.bottom))
        self.pickTol = maxSize * self.pickTolFac

        ptW = self.convertRasterPtToWorldCoords(self.pt0)
        xw, yw = ptW.x(), ptW.y()

        # --- AÇÃO: SELEÇÃO ---
        if self.curMouseAction == 'SELECTION':
            if self.mouseButton == QtCore.Qt.LeftButton:
                # Usa o controller do HETool para selecionar
                shift = (event.modifiers() & QtCore.Qt.ShiftModifier) == QtCore.Qt.ShiftModifier
                self.he_ctrl.selectPick(xw, yw, self.pickTol, shift)
                self.update()
            return

        # --- AÇÃO: CRIAÇÃO DE CURVAS ---
        if self.curMouseAction == 'COLLECTION':
            if self.curveType == 'LINE':
                # Inserção simples de ponto (ou segmento se tiver lógica de 2 cliques)
                if self.polyAnchor is None:
                    self.polyAnchor = (xw, yw)
                else:
                    self.he_ctrl.insertSegment([self.polyAnchor[0], self.polyAnchor[1], xw, yw], self.pickTol)
                    self.polyAnchor = None # Reseta para linhas desconectadas
                self.update()

            elif self.curveType == 'POLYLINE':
                if self.mouseButton == QtCore.Qt.LeftButton:
                    # CORREÇÃO: Usa o método local snapToPoint
                    snapped, sx, sy = self.snapToPoint(xw, yw, self.pickTol)
                    if snapped:
                        xw, yw = sx, sy

                    if self.polyAnchor is None:
                        self.polyAnchor = (xw, yw)
                    else:
                        # Cria segmento do anchor até aqui
                        self.he_ctrl.insertSegment([self.polyAnchor[0], self.polyAnchor[1], xw, yw], self.pickTol)
                        
                        # Se fechou (clicou no início), o HETool detecta topologia automaticamente.
                        if snapped:
                            self.polyAnchor = None
                        else:
                            self.polyAnchor = (xw, yw)
                    
                    self.update()
                
                elif self.mouseButton == QtCore.Qt.RightButton:
                    self.polyAnchor = None
                    self.update()

    def mouseMoveEvent(self, event):
        if self.polyAnchor:
            self.update() # Redesenha para mostrar a linha elástica

    def convertRasterPtToWorldCoords(self, _pt):
        w = self.width
        h = self.height
        if w == 0 or h == 0: return QtCore.QPointF(0,0)
        
        x_ratio = float(_pt.x()) / w
        y_ratio = float(h - _pt.y()) / h # Inverte Y do mouse
        
        if w <= h:
            aspect = float(h) / float(w)
            wx = self.left + x_ratio * (self.right - self.left)
            wy = (self.bottom * aspect) + y_ratio * ((self.top - self.bottom) * aspect)
        else:
            aspect = float(w) / float(h)
            wx = (self.left * aspect) + x_ratio * ((self.right - self.left) * aspect)
            wy = self.bottom + y_ratio * (self.top - self.bottom)
            
        return QtCore.QPointF(wx, wy)

    # Métodos auxiliares chamados pelo Controller
    def setMouseAction(self, action):
        self.curMouseAction = action
        
    def setCurveType(self, curveType):
        self.curveType = curveType
        self.polyAnchor = None
        
    def fitWorldToViewport(self):
        # Implementação manual de fit
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
        cx = (min_x + max_x) / 2
        cy = (min_y + max_y) / 2
        dx = (max_x - min_x) * margin
        dy = (max_y - min_y) * margin
        
        if dx < 1.0: dx = 10.0
        if dy < 1.0: dy = 10.0
        
        self.left = cx - dx/2
        self.right = cx + dx/2
        self.bottom = cy - dy/2
        self.top = cy + dy/2
        
        self.resizeGL(self.width, self.height)
        self.update()
        
    def zoomIn(self):
        cx = (self.left + self.right) / 2
        cy = (self.bottom + self.top) / 2
        dx = (self.right - self.left) * (1 - self.zoomFac)
        dy = (self.top - self.bottom) * (1 - self.zoomFac)
        self.left = cx - dx/2
        self.right = cx + dx/2
        self.bottom = cy - dy/2
        self.top = cy + dy/2
        self.resizeGL(self.width, self.height)
        self.update()
        
    def zoomOut(self):
        cx = (self.left + self.right) / 2
        cy = (self.bottom + self.top) / 2
        dx = (self.right - self.left) * (1 + self.zoomFac)
        dy = (self.top - self.bottom) * (1 + self.zoomFac)
        self.left = cx - dx/2
        self.right = cx + dx/2
        self.bottom = cy - dy/2
        self.top = cy + dy/2
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panLeft(self):
        dx = (self.right - self.left) * self.panFac
        self.left -= dx
        self.right -= dx
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panRight(self):
        dx = (self.right - self.left) * self.panFac
        self.left += dx
        self.right += dx
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panUp(self):
        dy = (self.top - self.bottom) * self.panFac
        self.bottom += dy
        self.top += dy
        self.resizeGL(self.width, self.height)
        self.update()
        
    def panDown(self):
        dy = (self.top - self.bottom) * self.panFac
        self.bottom -= dy
        self.top -= dy
        self.resizeGL(self.width, self.height)
        self.update()
    
    def setGrid(self, grid):
        self.grid = grid
    
    def resetGridDisplay(self):
        self.update()