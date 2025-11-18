import math
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve


class QuadBezier(Curve):
    def __init__(self, _pts=None):
        super().__init__()
        self.type = 'QUADBEZIER'
        self.pts = []
        if _pts:
            for p in _pts:
                try:
                    self.pts.append(Pnt2D(p.getX(), p.getY()))
                except Exception:
                    self.pts.append(Pnt2D(float(p[0]), float(p[1])))
        self.nPts = len(self.pts)

    # ---------------------------------------------------------------------
    def isUnlimited(self):
        return False

    # ---------------------------------------------------------------------
    def addCtrlPoint(self, _x, _y):
        # Limita a 3 pontos (p0, p1, p2) para finalizar no 3º clique
        if self.nPts >= 3:
            return False
        self.pts.append(Pnt2D(_x, _y))
        self.nPts = len(self.pts)
        return True

    # ---------------------------------------------------------------------
    def isPossible(self):
        return self.nPts >= 3

    # ---------------------------------------------------------------------
    def getCtrlPoints(self):
        return [p for p in self.pts]

    # ---------------------------------------------------------------------
    def setCtrlPoint(self, _id, _x, _y, _tol):
        if _id < 0 or _id >= self.nPts:
            return False
        self.pts[_id] = Pnt2D(_x, _y)
        return True

    # ---------------------------------------------------------------------
    def isStraight(self, _tol):
        if self.nPts < 2:
            return False
        if self.nPts == 2:
            return True
        return CompGeom.pickLine(self.pts[0], self.pts[-1], self.pts[1], _tol)

    # ---------------------------------------------------------------------
    def isClosed(self):
        if self.nPts < 2:
            return False
        return Pnt2D.euclidiandistance(self.pts[0], self.pts[-1]) <= Curve.COORD_TOL

    # ---------------------------------------------------------------------
    def _eval_point(self, t):
        # p(t) = (1-t)^2 p0 + 2(1-t)t p1 + t^2 p2
        if self.nPts == 0:
            return Pnt2D(0.0, 0.0)
        if self.nPts == 1:
            return Pnt2D(self.pts[0].getX(), self.pts[0].getY())
        if self.nPts == 2:
            x = (1 - t) * self.pts[0].getX() + t * self.pts[1].getX()
            y = (1 - t) * self.pts[0].getY() + t * self.pts[1].getY()
            return Pnt2D(x, y)
        p0, p1, p2 = self.pts[0], self.pts[1], self.pts[2]
        x = ((1 - t) ** 2) * p0.getX() + 2 * (1 - t) * t * p1.getX() + (t ** 2) * p2.getX()
        y = ((1 - t) ** 2) * p0.getY() + 2 * (1 - t) * t * p1.getY() + (t ** 2) * p2.getY()
        return Pnt2D(x, y)

    # ---------------------------------------------------------------------
    def evalPointSeg(self, _t):
        t = max(0.0, min(1.0, _t))
        pt = self.evalPoint(t)
        # Para Bezier não há índice de segmento significativo
        return pt, 0, t

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        t = max(0.0, min(1.0, _t))
        return self._eval_point(t)

    # ---------------------------------------------------------------------
    def evalPointTangent(self, _t):
        t = max(0.0, min(1.0, _t))
        if self.nPts < 3:
            return self.evalPoint(t), Pnt2D(0.0, 0.0)
        p0, p1, p2 = self.pts[0], self.pts[1], self.pts[2]
        dx = 2 * (1 - t) * (p1.getX() - p0.getX()) + 2 * t * (p2.getX() - p1.getX())
        dy = 2 * (1 - t) * (p1.getY() - p0.getY()) + 2 * t * (p2.getY() - p1.getY())
        norm = math.hypot(dx, dy)
        tang = Pnt2D(0.0, 0.0) if norm == 0.0 else Pnt2D(dx / norm, dy / norm)
        pt = self.evalPoint(t)
        return pt, tang

    # ---------------------------------------------------------------------
    def splitRaw(self, _t):
        if self.nPts < 3:
            return QuadBezier([]), QuadBezier([])
        t = max(0.0, min(1.0, _t))
        p0, p1, p2 = self.pts
        p01 = Pnt2D((1 - t) * p0.getX() + t * p1.getX(), (1 - t) * p0.getY() + t * p1.getY())
        p12 = Pnt2D((1 - t) * p1.getX() + t * p2.getX(), (1 - t) * p1.getY() + t * p2.getY())
        p012 = Pnt2D((1 - t) * p01.getX() + t * p12.getX(), (1 - t) * p01.getY() + t * p12.getY())
        left = QuadBezier([p0, p01, p012])
        right = QuadBezier([p012, p12, p2])
        return left, right

    # ---------------------------------------------------------------------
    def split(self, _t):
        left, right = self.splitRaw(_t)
        return left, right

    # ---------------------------------------------------------------------
    def join(self, _joinCurve, _pt, _tol):
        return False, None, 'Join not supported for quadratic Bezier curves.'

    # ---------------------------------------------------------------------
    def _sample(self, pts, samples=32):
        if len(pts) == 0:
            return []
        if len(pts) == 1:
            return [pts[0]]
        if len(pts) == 2:
            return [Pnt2D((1 - t) * pts[0].getX() + t * pts[1].getX(),
                          (1 - t) * pts[0].getY() + t * pts[1].getY())
                    for t in [i / samples for i in range(samples + 1)]]
        p0, p1, p2 = pts[0], pts[1], pts[2]
        out = []
        for i in range(samples + 1):
            t = i / samples
            out.append(Pnt2D(((1 - t) ** 2) * p0.getX() + 2 * (1 - t) * t * p1.getX() + (t ** 2) * p2.getX(),
                              ((1 - t) ** 2) * p0.getY() + 2 * (1 - t) * t * p1.getY() + (t ** 2) * p2.getY()))
        return out

    # ---------------------------------------------------------------------
    def getEquivPolyline(self):
        return self._sample(self.pts, 32)

    # ---------------------------------------------------------------------
    def getEquivPolylineCollecting(self, _pt):
        # Preview durante a coleta:
        # - n==0: nada
        # - n==1: linha p0->temp
        # - n==2: quadrática usando p0,p1,temp
        # - n>=3: curva final
        if self.nPts == 0:
            return []
        if self.nPts == 1:
            if _pt is None:
                return []
            temp = Pnt2D(_pt.getX(), _pt.getY()) if hasattr(_pt, 'getX') else Pnt2D(float(_pt[0]), float(_pt[1]))
            return [self.pts[0], temp]
        if self.nPts == 2:
            if _pt is None:
                return [self.pts[0], self.pts[1]]
            temp = Pnt2D(_pt.getX(), _pt.getY()) if hasattr(_pt, 'getX') else Pnt2D(float(_pt[0]), float(_pt[1]))
            return self._sample([self.pts[0], self.pts[1], temp], 32)
        return self._sample(self.pts, 32)

    # ---------------------------------------------------------------------
    def _closest_on_polyline(self, poly, x, y):
        if len(poly) < 2:
            pt = poly[0] if poly else Pnt2D(0.0, 0.0)
            return pt, float('inf'), 0, 0.0
        q = Pnt2D(x, y)
        dmin = float('inf')
        cl = Pnt2D(0.0, 0.0)
        seg = 0
        arc = 0.0
        acc = 0.0
        for i in range(len(poly) - 1):
            d, cpt, t = CompGeom.getClosestPointSegment(poly[i], poly[i + 1], q)
            if d < dmin:
                dmin = d
                cl = cpt
                seg = i
                arc = acc + math.hypot(cpt.getX() - poly[i].getX(), cpt.getY() - poly[i].getY())
            acc += math.hypot(poly[i + 1].getX() - poly[i].getX(), poly[i + 1].getY() - poly[i].getY())
        return cl, dmin, seg, arc

    # ---------------------------------------------------------------------
    def closestPointSeg(self, _x, _y):
        poly = self.getEquivPolyline()
        return self._closest_on_polyline(poly, _x, _y)

    # ---------------------------------------------------------------------
    def closestPoint(self, _x, _y):
        cl, dmin, seg, arc = self.closestPointSeg(_x, _y)
        length = self.length()
        t = 0.0 if length == 0.0 else arc / length
        pt, tang = self.evalPointTangent(t)
        return True, cl, dmin, t, tang

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        poly = self.getEquivPolyline()
        if not poly:
            return 0.0, 0.0, 0.0, 0.0
        xs = [p.getX() for p in poly]
        ys = [p.getY() for p in poly]
        return min(xs), max(xs), min(ys), max(ys)

    # ---------------------------------------------------------------------
    def getPntInit(self):
        return self.pts[0] if self.nPts >= 1 else Pnt2D(0.0, 0.0)

    # ---------------------------------------------------------------------
    def getPntEnd(self):
        return self.pts[-1] if self.nPts >= 1 else Pnt2D(0.0, 0.0)

    # ---------------------------------------------------------------------
    def length(self):
        poly = self.getEquivPolyline()
        L = 0.0
        for i in range(len(poly) - 1):
            L += math.hypot(poly[i + 1].getX() - poly[i].getX(), poly[i + 1].getY() - poly[i].getY())
        return L