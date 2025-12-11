from hetool.geometry.point import Point
from geometry.curves.curve import Curve
import math

class QuadBezier(Curve):
    def __init__(self):
        super().__init__()
        self.type = 'QUADBEZIER'

    def getEquivPolylineCollecting(self, tempPt):
        # Se temos 1 ponto (P0), desenha linha até o mouse (P1)
        if self.nPts == 1:
            return [self.ctrlPts[0], tempPt]
        # Se temos 2 pontos (P0, P1), desenha a curva completa usando mouse como P2
        elif self.nPts == 2:
            temp_curve = QuadBezier()
            temp_curve.ctrlPts = [self.ctrlPts[0], self.ctrlPts[1], tempPt]
            temp_curve.nPts = 3
            return temp_curve.getEquivPolyline()
        return []

    def isStraight(self, tol):
        if self.nPts < 3: return True
        p0, p1, p2 = self.ctrlPts
        
        # Área do triângulo * 2
        area2 = abs((p1.getX() - p0.getX()) * (p2.getY() - p0.getY()) - 
                    (p1.getY() - p0.getY()) * (p2.getX() - p0.getX()))
        dist = math.sqrt((p2.getX() - p0.getX())**2 + (p2.getY() - p0.getY())**2)
        
        if dist < 1e-5: return True
        return (area2 / dist) < tol

    def splitRaw(self, t):
        p0, p1, p2 = self.ctrlPts

        def interp(a, b, t):
            return Point((1-t)*a.getX() + t*b.getX(), (1-t)*a.getY() + t*b.getY())

        p01 = interp(p0, p1, t)
        p12 = interp(p1, p2, t)
        p012 = interp(p01, p12, t)

        c1 = QuadBezier()
        c1.ctrlPts = [p0, p01, p012]; c1.nPts = 3
        c2 = QuadBezier()
        c2.ctrlPts = [p012, p12, p2]; c2.nPts = 3

        return c1, c2