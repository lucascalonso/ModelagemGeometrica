import math
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve


class Circle(Curve):
    def __init__(self, _pts=None):
        super().__init__()
        self.type = 'CIRCLE'
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
        # Limita a 2 pontos (centro, ponto no raio)
        if self.nPts >= 2:
            return False
        self.pts.append(Pnt2D(_x, _y))
        self.nPts = len(self.pts)
        return True

    # ---------------------------------------------------------------------
    def isPossible(self):
        # center + point on circumference
        return self.nPts >= 2

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
        return False

    # ---------------------------------------------------------------------
    def isClosed(self):
        return True

    # ---------------------------------------------------------------------
    def _center_radius(self, temp=None):
        if self.nPts == 0:
            return Pnt2D(0.0, 0.0), 0.0
        c = self.pts[0]
        if self.nPts >= 2:
            r = Pnt2D.euclidiandistance(c, self.pts[1])
        else:
            if temp is None:
                r = 0.0
            else:
                t = temp if isinstance(temp, Pnt2D) else Pnt2D(temp.getX(), temp.getY())
                r = Pnt2D.euclidiandistance(c, t)
        return c, r

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        c, r = self._center_radius()
        t = max(0.0, min(1.0, _t))
        ang = 2.0 * math.pi * t
        return Pnt2D(c.getX() + r * math.cos(ang), c.getY() + r * math.sin(ang))

    # ---------------------------------------------------------------------
    def evalPointTangent(self, _t):
        pt = self.evalPoint(_t)
        c, r = self._center_radius()
        if r == 0.0:
            return pt, Pnt2D(0.0, 0.0)
        # tangente perpendicular ao raio
        vx = pt.getX() - c.getX()
        vy = pt.getY() - c.getY()
        norm = math.hypot(vx, vy)
        if norm == 0.0:
            return pt, Pnt2D(0.0, 0.0)
        tx, ty = -vy / norm, vx / norm
        return pt, Pnt2D(tx, ty)

    # ---------------------------------------------------------------------
    def _sample_circle(self, c, r, samples=64):
        if r <= 0.0:
            return [Pnt2D(c.getX(), c.getY())]
        out = []
        for i in range(samples + 1):
            ang = 2.0 * math.pi * (i / samples)
            out.append(Pnt2D(c.getX() + r * math.cos(ang), c.getY() + r * math.sin(ang)))
        return out

    # ---------------------------------------------------------------------
    def getEquivPolyline(self):
        c, r = self._center_radius()
        return self._sample_circle(c, r, 64)

    # ---------------------------------------------------------------------
    def getEquivPolylineCollecting(self, _pt):
        if self.nPts == 0:
            return []
        if self.nPts == 1:
            if _pt is None:
                return [self.pts[0]]
            temp = Pnt2D(_pt.getX(), _pt.getY()) if hasattr(_pt, 'getX') else Pnt2D(float(_pt[0]), float(_pt[1]))
            c = self.pts[0]
            r = Pnt2D.euclidiandistance(c, temp)
            return self._sample_circle(c, r, 64)
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
        c, r = self._center_radius()
        if r <= 0.0:
            x = c.getX()
            y = c.getY()
            return x, x, y, y
        return c.getX() - r, c.getX() + r, c.getY() - r, c.getY() + r

    # ---------------------------------------------------------------------
    def getPntInit(self):
        return self.pts[0] if self.nPts >= 1 else Pnt2D(0.0, 0.0)

    # ---------------------------------------------------------------------
    def getPntEnd(self):
        return self.pts[-1] if self.nPts >= 1 else Pnt2D(0.0, 0.0)

    # ---------------------------------------------------------------------
    def length(self):
        c, r = self._center_radius()
        return 2.0 * math.pi * r