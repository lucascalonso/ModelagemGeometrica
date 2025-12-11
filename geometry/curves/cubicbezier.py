from hetool.geometry.point import Point
from geometry.curves.curve import Curve
import math

class CubicBezier(Curve):
    def __init__(self):
        super().__init__()
        self.type = 'CUBICBEZIER'

    def getEquivPolylineCollecting(self, tempPt):
        if self.nPts == 1:
            return [self.ctrlPts[0], tempPt]
        elif self.nPts == 2:
            # P0 -> P1 -> Mouse (apenas linhas de controle para visualizar)
            return [self.ctrlPts[0], self.ctrlPts[1], tempPt]
        elif self.nPts == 3:
            # Curva completa P0, P1, P2, Mouse(P3)
            temp_curve = CubicBezier()
            temp_curve.ctrlPts = [self.ctrlPts[0], self.ctrlPts[1], self.ctrlPts[2], tempPt]
            temp_curve.nPts = 4
            return temp_curve.getEquivPolyline()
        return []

    def isStraight(self, tol):
        if self.nPts < 4: return True
        p0, p1, p2, p3 = self.ctrlPts
        
        def dist_pt_line(pt, l1, l2):
            area2 = abs((pt.getX() - l1.getX()) * (l2.getY() - l1.getY()) - 
                        (pt.getY() - l1.getY()) * (l2.getX() - l1.getX()))
            base = math.sqrt((l2.getX() - l1.getX())**2 + (l2.getY() - l1.getY())**2)
            if base < 1e-5: return 0
            return area2 / base

        return dist_pt_line(p1, p0, p3) < tol and dist_pt_line(p2, p0, p3) < tol

    def splitRaw(self, t):
        p0, p1, p2, p3 = self.ctrlPts
        
        def interp(a, b, t):
            return Point((1-t)*a.getX() + t*b.getX(), (1-t)*a.getY() + t*b.getY())

        p01 = interp(p0, p1, t)
        p12 = interp(p1, p2, t)
        p23 = interp(p2, p3, t)
        p012 = interp(p01, p12, t)
        p123 = interp(p12, p23, t)
        p0123 = interp(p012, p123, t)

        c1 = CubicBezier()
        c1.ctrlPts = [p0, p01, p012, p0123]; c1.nPts = 4
        c2 = CubicBezier()
        c2.ctrlPts = [p0123, p123, p23, p3]; c2.nPts = 4
        
        return c1, c2