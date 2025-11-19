
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve
import math

class Line(Curve):
    def __init__(self, _pts=None):
        super().__init__()
        self.type = 'LINE'
        self.pts = []
        if _pts is not None:
            for p in _pts:
                try:
                    self.pts.append(Pnt2D(p.getX(), p.getY()))
                except Exception:
                    self.pts.append(Pnt2D(float(p[0]), float(p[1])))
        self.nPts = len(self.pts)
        

    def isUnlimited(self):
        return False

    def addCtrlPoint(self, _x, _y):
        # Limita a 2 pontos e retorna bool
        if self.nPts >= 2:
            return False
        self.pts.append(Pnt2D(_x, _y))
        self.nPts = len(self.pts)
        return True

    def isPossible(self):
        return self.nPts == 2

    def getCtrlPoints(self):
        return list(self.pts)

    def setCtrlPoint(self, _id, _x, _y, _tol):
        if _id < 0 or _id >= self.nPts:
            return False
        self.pts[_id] = Pnt2D(_x, _y)
        return True

    def isStraight(self, _tol):
        return True if self.nPts >= 2 else False

    def isClosed(self):
        return False

    def evalPointSeg(self, _t):
        if self.nPts == 0:
            return Pnt2D(0.0, 0.0), 0, 0.0
        if self.nPts == 1:
            return Pnt2D(self.pts[0].getX(), self.pts[0].getY()), 0, 0.0
        t = max(0.0, min(1.0, _t))
        x = (1 - t) * self.pts[0].getX() + t * self.pts[1].getX()
        y = (1 - t) * self.pts[0].getY() + t * self.pts[1].getY()
        return Pnt2D(x, y), 0, t

    def evalPoint(self, _t):
        pt, _, _ = self.evalPointSeg(_t)
        return pt

    def evalPointTangent(self, _t):
        if self.nPts < 2:
            return Pnt2D(0.0, 0.0), Pnt2D(0.0, 0.0)
        dx = self.pts[1].getX() - self.pts[0].getX()
        dy = self.pts[1].getY() - self.pts[0].getY()
        norm = math.hypot(dx, dy)
        tang = Pnt2D(0.0, 0.0) if norm == 0.0 else Pnt2D(dx / norm, dy / norm)
        mid = self.evalPoint(0.5)
        return mid, tang

    def splitRaw(self, t):
        """Splits the line at parameter t, returning two new lines."""
        if self.nPts < 2:
            return Line(), Line()
        
        p0 = self.pts[0]
        p1 = self.pts[1]
        # Linear interpolation to find the split point
        mid_pt = Pnt2D((1 - t) * p0.getX() + t * p1.getX(), (1 - t) * p0.getY() + t * p1.getY())
        
        # CORREÇÃO: O construtor da Line espera uma lista de pontos.
        left = Line([p0, mid_pt])
        right = Line([mid_pt, p1])
        return left, right

    def split(self, num_pieces):
        """Splits the line into a specified number of new lines of equal length."""
        if num_pieces < 2:
            return [self]

        new_curves = []
        remaining_curve = self
        
        # Este loop divide a linha no número de pedaços desejado
        for i in range(num_pieces, 1, -1):
            # O parâmetro 't' é sempre 1.0 dividido pelo número de pedaços restantes
            t_split = 1.0 / i
            
            left, right = remaining_curve.splitRaw(t_split)
            
            # Adiciona o novo pedaço da esquerda à nossa lista de novas curvas
            new_curves.append(left)
            
            # A parte da direita se torna a nova curva a ser dividida no próximo passo
            remaining_curve = right
        
        # No final, adiciona o último pedaço restante à lista
        new_curves.append(remaining_curve)
        
        # Retorna a lista completa de novas linhas
        return new_curves

    def join(self, _joinCurve, _pt, _tol):
        from geometry.curves.polyline import Polyline
        # Joining produces a Polyline
        if (_joinCurve.getType() != 'LINE') and (_joinCurve.getType() != 'POLYLINE'):
            return False, None, 'LINE can only be joined with LINE or POLYLINE'
        # reuse polyline join logic: assemble ordered pts
        pts = []
        selfInit = self.getPntInit()
        selfEnd = self.getPntEnd()
        otherInit = _joinCurve.getPntInit()
        otherEnd = _joinCurve.getPntEnd()
        if Pnt2D.euclidiandistance(selfEnd, _pt) < _tol:
            pts = [selfInit, selfEnd]
            otherPts = _joinCurve.getCtrlPoints()
            for p in otherPts[1:]:
                pts.append(p)
        elif Pnt2D.euclidiandistance(selfInit, _pt) < _tol:
            pts = [selfEnd, selfInit]
            otherPts = _joinCurve.getCtrlPoints()
            for p in otherPts[1:]:
                pts.append(p)
        else:
            return False, None, 'Join point not on line'
        return True, Polyline(pts), None

    def getEquivPolyline(self):
        return list(self.pts)

    def getEquivPolylineCollecting(self, _pt):
        return self.getEquivPolyline()

    def closestPointSeg(self, _x, _y):
        if self.nPts < 2:
            return Pnt2D(0.0, 0.0), float('inf'), 0, 0.0
        d, clst, t = CompGeom.getClosestPointSegment(self.pts[0], self.pts[1], Pnt2D(_x, _y))
        arcLen = t * self.length()
        return clst, d, 0, arcLen

    def closestPoint(self, _x, _y):
        clst, dmin, seg, arcLen = self.closestPointSeg(_x, _y)
        tang = self.evalPointTangent(0.5)[1]
        t = 0.0 if self.length() == 0.0 else arcLen / self.length()
        return True, clst, dmin, t, tang

    def closestPointParam(self, _x, _y, _tStart):
        return self.closestPoint(_x, _y)

    def getBoundBox(self):
        if self.nPts == 0:
            return 0.0,0.0,0.0,0.0
        xs = [p.getX() for p in self.pts]
        ys = [p.getY() for p in self.pts]
        return min(xs), max(xs), min(ys), max(ys)

    def getXinit(self):
        return self.pts[0].getX() if self.nPts>=1 else 0.0

    def getYinit(self):
        return self.pts[0].getY() if self.nPts>=1 else 0.0

    def getXend(self):
        return self.pts[-1].getX() if self.nPts>=1 else 0.0

    def getYend(self):
        return self.pts[-1].getY() if self.nPts>=1 else 0.0

    def getPntInit(self):
        return self.pts[0] if self.nPts>=1 else Pnt2D(0.0,0.0)

    def getPntEnd(self):
        return self.pts[-1] if self.nPts>=1 else Pnt2D(0.0,0.0)

    def length(self):
        if self.nPts < 2:
            return 0.0
        return math.hypot(self.pts[1].getX()-self.pts[0].getX(), self.pts[1].getY()-self.pts[0].getY())