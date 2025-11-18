import math
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve


class CubicBezier(Curve):
    def __init__(self, _pts=None):
        super().__init__()
        self.type = 'CUBICBEZIER'
        self.pts = []
        if _pts:
            for p in _pts:
                try:
                    self.pts.append(Pnt2D(p.getX(), p.getY()))
                except Exception:
                    self.pts.append(Pnt2D(float(p[0]), float(p[1])))
        self.nPts = len(self.pts)

    def getNumberOfCtrlPoints(self):
        return self.nPts

    # ---------------------------------------------------------------------
    def isUnlimited(self):
        return False

    # ---------------------------------------------------------------------
    def addCtrlPoint(self, _x, _y):
        # Limita a 4 pontos de controle (p0..p3)
        if self.nPts >= 4:
            return False
        self.pts.append(Pnt2D(_x, _y))
        self.nPts = len(self.pts)
        return True

    # ---------------------------------------------------------------------
    def isPossible(self):
        return self.nPts >= 4

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
        # todos colineares com p0->p3
        for p in self.pts[1:-1]:
            if not CompGeom.pickLine(self.pts[0], self.pts[-1], p, _tol):
                return False
        return True

    # ---------------------------------------------------------------------
    def isClosed(self):
        if self.nPts < 2:
            return False
        return Pnt2D.euclidiandistance(self.pts[0], self.pts[-1]) <= Curve.COORD_TOL

    # ---------------------------------------------------------------------
    def _de_casteljau_point(self, ctrl, t):
        level = [Pnt2D(p.getX(), p.getY()) for p in ctrl]
        n = len(level)
        for r in range(1, n):
            for i in range(n - r):
                x = (1.0 - t) * level[i].getX() + t * level[i + 1].getX()
                y = (1.0 - t) * level[i].getY() + t * level[i + 1].getY()
                level[i] = Pnt2D(x, y)
        return level[0]

    def _derivative_vec(self, ctrl, t):
        if len(ctrl) < 2:
            return Pnt2D(0.0, 0.0)
        d = []
        for i in range(len(ctrl) - 1):
            d.append(Pnt2D(ctrl[i + 1].getX() - ctrl[i].getX(), ctrl[i + 1].getY() - ctrl[i].getY()))
        if len(d) == 1:
            return d[0]
        if len(d) == 2:
            x = (1.0 - t) * d[0].getX() + t * d[1].getX()
            y = (1.0 - t) * d[0].getY() + t * d[1].getY()
            return Pnt2D(x, y)
        p = self._de_casteljau_point(d, t)
        return Pnt2D(3.0 * p.getX(), 3.0 * p.getY())

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        if self.nPts == 0:
            return Pnt2D(0.0, 0.0)
        t = max(0.0, min(1.0, _t))
        pts = self.pts
        if len(pts) <= 2:
            if len(pts) == 1:
                return Pnt2D(pts[0].getX(), pts[0].getY())
            return Pnt2D((1 - t) * pts[0].getX() + t * pts[1].getX(),
                         (1 - t) * pts[0].getY() + t * pts[1].getY())
        if len(pts) == 3:
            p0, p1, p2 = pts
            x = ((1 - t) ** 2) * p0.getX() + 2 * (1 - t) * t * p1.getX() + (t ** 2) * p2.getX()
            y = ((1 - t) ** 2) * p0.getY() + 2 * (1 - t) * t * p1.getY() + (t ** 2) * p2.getY()
            return Pnt2D(x, y)
        return self._de_casteljau_point(pts, t)

    # ---------------------------------------------------------------------
    def evalPointTangent(self, _t):
        t = max(0.0, min(1.0, _t))
        pt = self.evalPoint(t)
        tang = self._derivative_vec(self.pts, t)
        norm = math.hypot(tang.getX(), tang.getY())
        if norm == 0.0:
            tangVec = Pnt2D(0.0, 0.0)
        else:
            tangVec = Pnt2D(tang.getX() / norm, tang.getY() / norm)
        return pt, tangVec

    # ---------------------------------------------------------------------
    def splitRaw(self, _t):
        if self.nPts == 0:
            return CubicBezier([]), CubicBezier([])
        t = max(0.0, min(1.0, _t))
        triangle = []
        level = [Pnt2D(p.getX(), p.getY()) for p in self.pts]
        triangle.append(level)
        n = len(level)
        for r in range(1, n):
            next_level = []
            for i in range(n - r):
                x = (1.0 - t) * level[i].getX() + t * level[i + 1].getX()
                y = (1.0 - t) * level[i].getY() + t * level[i + 1].getY()
                next_level.append(Pnt2D(x, y))
            triangle.append(next_level)
            level = next_level
        left_pts = [triangle[i][0] for i in range(len(triangle))]
        right_pts = [triangle[i][-1] for i in range(len(triangle))]
        return CubicBezier(left_pts), CubicBezier(right_pts)

    # ---------------------------------------------------------------------
    def split(self, _t):
        left, right = self.splitRaw(_t)
        return left, right

    # ---------------------------------------------------------------------
    def join(self, _joinCurve, _pt, _tol):
        return False, None, 'Join not supported for cubic Bezier curves.'

    # ---------------------------------------------------------------------
    def getEquivPolyline(self):
        samples = 32
        if self.nPts == 0:
            return []
        pts = []
        for i in range(samples + 1):
            t = i / samples
            pts.append(self.evalPoint(t))
        return pts

    # ---------------------------------------------------------------------
    def getEquivPolylineCollecting(self, _pt):
        # Preview:
        # - n==0: []
        # - n==1: [p0,temp] (line)
        # - n==2: quadratic with temp as p2
        # - n==3: cubic with temp as p3
        # - n>=4: final curve
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
            qb = [self.pts[0], self.pts[1], temp]
            out = []
            samples = 32
            p0, p1, p2 = qb
            for i in range(samples + 1):
                t = i / samples
                out.append(Pnt2D(((1 - t) ** 2) * p0.getX() + 2 * (1 - t) * t * p1.getX() + (t ** 2) * p2.getX(),
                                  ((1 - t) ** 2) * p0.getY() + 2 * (1 - t) * t * p1.getY() + (t ** 2) * p2.getY()))
            return out
        if self.nPts == 3:
            if _pt is None:
                qb = self.pts[:3]
                out = []
                samples = 32
                p0, p1, p2 = qb
                for i in range(samples + 1):
                    t = i / samples
                    out.append(Pnt2D(((1 - t) ** 2) * p0.getX() + 2 * (1 - t) * t * p1.getX() + (t ** 2) * p2.getX(),
                                      ((1 - t) ** 2) * p0.getY() + 2 * (1 - t) * t * p1.getY() + (t ** 2) * p2.getY()))
                return out
            temp = Pnt2D(_pt.getX(), _pt.getY()) if hasattr(_pt, 'getX') else Pnt2D(float(_pt[0]), float(_pt[1]))
            cb = [self.pts[0], self.pts[1], self.pts[2], temp]
            samples = 32
            return [self._de_casteljau_point(cb, i / samples) for i in range(samples + 1)]
        return self.getEquivPolyline()

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