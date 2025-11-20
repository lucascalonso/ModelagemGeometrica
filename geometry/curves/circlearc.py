import math
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve


class CircleArc(Curve):
    def __init__(self, _pts=None):
        super().__init__()
        self.type = 'CIRCLEARC'
        self.pts = []
        if _pts:
            for p in _pts:
                try:
                    self.pts.append(Pnt2D(p.getX(), p.getY()))
                except Exception:
                    self.pts.append(Pnt2D(float(p[0]), float(p[1])))
        self.nPts = len(self.pts)
        self._center = None
        self._radius = 0.0
        self._a0 = 0.0
        self._a1 = 0.0
        self._poly = []

        if self.nPts >= 3:
            self._recompute()

    def getNumberOfCtrlPoints(self):
        return self.nPts

    def isUnlimited(self):
        return False

    def addCtrlPoint(self, _x, _y):
        if self.nPts >= 3:
            return False
        self.pts.append(Pnt2D(_x, _y))
        self.nPts = len(self.pts)
        if self.nPts == 3:
            self._recompute()
        else:
            self._poly.clear()
        return True

    def isPossible(self):
        return self.nPts == 3 and self._radius > 0.0

    def getCtrlPoints(self):
        return [p for p in self.pts]

    def setCtrlPoint(self, _id, _x, _y, _tol):
        if _id < 0 or _id >= self.nPts:
            return False
        self.pts[_id] = Pnt2D(_x, _y)
        if self.nPts == 3:
            self._recompute()
        return True

    def isStraight(self, _tol):
        return False

    def isClosed(self):
        return False

    def _recompute(self):
        self._poly.clear()
        c, r = self._compute_center_radius()
        if r <= 0.0:
            self._radius = 0.0
            return
        self._center = c
        self._radius = r
        self._a0, self._a1 = self._compute_angles(c, self.pts[1], self.pts[2])

    def _compute_center_radius(self):
        if self.nPts < 3:
            return Pnt2D(0.0, 0.0), 0.0
        p0, p1, p2 = self.pts
        # Circumcenter of triangle p0,p1,p2
        x0, y0 = p0.getX(), p0.getY()
        x1, y1 = p1.getX(), p1.getY()
        x2, y2 = p2.getX(), p2.getY()
        d = 2.0 * (x0*(y1 - y2) + x1*(y2 - y0) + x2*(y0 - y1))
        if abs(d) < 1e-14:
            return Pnt2D(0.0, 0.0), 0.0
        ux = ((x0**2 + y0**2)*(y1 - y2) + (x1**2 + y1**2)*(y2 - y0) + (x2**2 + y2**2)*(y0 - y1)) / d
        uy = ((x0**2 + y0**2)*(x2 - x1) + (x1**2 + y1**2)*(x0 - x2) + (x2**2 + y2**2)*(x1 - x0)) / d
        c = Pnt2D(ux, uy)
        r = Pnt2D.euclidiandistance(c, p0)
        return c, r

    def _compute_angles(self, c, start_pt, end_pt):
        def ang(pt):
            a = math.atan2(pt.getY() - c.getY(), pt.getX() - c.getX())
            return a if a >= 0.0 else a + 2.0 * math.pi
        a0 = ang(start_pt)
        a1 = ang(end_pt)
        # Preserve shortest positive sweep (counter-clockwise)
        if a1 < a0:
            a1 += 2.0 * math.pi
        return a0, a1

    def _sample_arc(self, samples=24):
        self._poly.clear()
        if not self.isPossible():
            return
        step = (self._a1 - self._a0) / samples
        for i in range(samples + 1):
            a = self._a0 + i * step
            x = self._center.getX() + self._radius * math.cos(a)
            y = self._center.getY() + self._radius * math.sin(a)
            self._poly.append(Pnt2D(x, y))

    def evalPoint(self, _t):
        if not self.isPossible():
            return Pnt2D(0.0, 0.0)
        t = max(0.0, min(1.0, _t))
        a = self._a0 + t * (self._a1 - self._a0)
        x = self._center.getX() + self._radius * math.cos(a)
        y = self._center.getY() + self._radius * math.sin(a)
        return Pnt2D(x, y)

    def evalPointTangent(self, _t):
        pt = self.evalPoint(_t)
        if not self.isPossible():
            return pt, Pnt2D(0.0, 0.0)
        t = max(0.0, min(1.0, _t))
        a = self._a0 + t * (self._a1 - self._a0)
        dx = -self._radius * math.sin(a)
        dy = self._radius * math.cos(a)
        nrm = math.hypot(dx, dy)
        tang = Pnt2D(dx / nrm, dy / nrm) if nrm > 0.0 else Pnt2D(0.0, 0.0)
        return pt, tang

    def splitRaw(self, _t):
        if not self.isPossible():
            return CircleArc([]), CircleArc([])
        t = max(0.0, min(1.0, _t))
        a_mid = self._a0 + t * (self._a1 - self._a0)
        mid_pt = Pnt2D(self._center.getX() + self._radius * math.cos(a_mid),
                       self._center.getY() + self._radius * math.sin(a_mid))
        left = CircleArc([self.pts[0], self.pts[1], mid_pt])
        right = CircleArc([self.pts[0], mid_pt, self.pts[2]])
        return left, right

    def split(self, _t):
        l, r = self.splitRaw(_t)
        l._sample_arc()
        r._sample_arc()
        return l, r

    def join(self, _joinCurve, _pt, _tol):
        return False, None, 'Join not supported for CircleArc.'

    def getEquivPolyline(self):
        if not self.isPossible():
            return []
        if not self._poly:
            self._sample_arc()
        return [p for p in self._poly]

    def getEquivPolylineCollecting(self, _pt):
        if self.nPts == 0:
            return []
        if self.nPts == 1:
            return [self.pts[0]]
        if self.nPts == 2 and _pt is not None:
            temp = Pnt2D(_pt.getX(), _pt.getY()) if hasattr(_pt, 'getX') else _pt
            trial = CircleArc([self.pts[0], self.pts[1], temp])
            if trial.isPossible():
                trial._sample_arc(samples=16)
                return trial.getEquivPolyline()
            return [self.pts[0], self.pts[1], temp]
        if not self.isPossible():
            return self.getCtrlPoints()
        return self.getEquivPolyline()

    def closestPoint(self, _x, _y):
        if not self.isPossible():
            return True, Pnt2D(0.0, 0.0), 0.0, 0.0, Pnt2D(0.0, 0.0)
        q = Pnt2D(_x, _y)
        # Project onto circle
        dx = q.getX() - self._center.getX()
        dy = q.getY() - self._center.getY()
        d = math.hypot(dx, dy)
        if d == 0.0:
            cand = Pnt2D(self._center.getX() + self._radius * math.cos(self._a0),
                         self._center.getY() + self._radius * math.sin(self._a0))
        else:
            cand = Pnt2D(self._center.getX() + self._radius * dx / d,
                         self._center.getY() + self._radius * dy / d)
        # Clamp angle to arc
        ang = math.atan2(cand.getY() - self._center.getY(), cand.getX() - self._center.getX())
        if ang < 0.0:
            ang += 2.0 * math.pi
        # Normalize into [a0,a1] (allow a1 > 2π)
        a = ang
        if a < self._a0:
            a = self._a0
        if a > self._a1:
            a = self._a1
        clamped = Pnt2D(self._center.getX() + self._radius * math.cos(a),
                        self._center.getY() + self._radius * math.sin(a))
        t = (a - self._a0) / (self._a1 - self._a0) if self._a1 != self._a0 else 0.0
        dist = abs(d - self._radius)
        _, tang = self.evalPointTangent(t)
        return True, clamped, dist, t, tang

    def closestPointParam(self, _x, _y, _tStart):
        return self.closestPoint(_x, _y)

    def getBoundBox(self):
        if not self.isPossible():
            return 0.0, 0.0, 0.0, 0.0
        # Sample endpoints + mid for bbox
        pts = [self.evalPoint(0.0), self.evalPoint(1.0), self.evalPoint(0.5)]
        xs = [p.getX() for p in pts]
        ys = [p.getY() for p in pts]
        return min(xs), max(xs), min(ys), max(ys)

    def length(self):
        if not self.isPossible():
            return 0.0
        return self._radius * (self._a1 - self._a0)