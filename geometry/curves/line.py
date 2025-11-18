from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve
from geometry.curves.polyline import Polyline
import math


class Line(Curve):
    def __init__(self, _pt0=None, _pt1=None):
        super(Curve, self).__init__()
        self.type = 'LINE'
        self.pt0 = _pt0
        self.pt1 = _pt1
        self.nPts = 0
        if _pt0 is not None:
            self.nPts += 1
        if _pt1 is not None:
            self.nPts += 1

    # ---------------------------------------------------------------------
    def setPoints(self, _x0, _y0, _x1, _y1):
        self.pt0 = Pnt2D(_x0, _y0)
        self.pt1 = Pnt2D(_x1, _y1)
        self.nPts = 2

    # ---------------------------------------------------------------------
    def addCtrlPoint(self, _x, _y):
        if self.nPts == 0:
            self.pt0 = Pnt2D(_x, _y)
            self.nPts += 1
        elif self.nPts == 1:
            self.pt1 = Pnt2D(_x, _y)
            self.nPts += 1

    # ---------------------------------------------------------------------
    def isPossible(self):
        if self.nPts < 2:
            return False
        return True

    # ---------------------------------------------------------------------
    def getCtrlPoints(self):
        tempPts = []
        if self.nPts == 0:
            return tempPts
        if self.nPts == 1:
            tempPts.append(self.pt0)
            return tempPts
        tempPts.append(self.pt0)
        tempPts.append(self.pt1)
        return tempPts

    # ---------------------------------------------------------------------
    def setCtrlPoint(self, _id, _x, _y, _tol):
        if self.nPts != 2:
            return False
        pt = Pnt2D(_x, _y)
        if _id == 0:
            if Pnt2D.euclidiandistance(pt, self.pt1) <= _tol:
                return False
            self.pt0.setCoords(_x, _y)
            return True
        if _id == 1:
            if Pnt2D.euclidiandistance(pt, self.pt0) <= _tol:
                return False
            self.pt1.setCoords(_x, _y)
            return True
        return False

    # ---------------------------------------------------------------------
    def isStraight(self, _tol):
        if self.nPts != 2:
            return False
        return True

    # ---------------------------------------------------------------------
    def isClosed(self):
        return False

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        vx = self.pt1.getX() - self.pt0.getX()
        vy = self.pt1.getY() - self.pt0.getY()
        if _t < 0.0:
            xOn = self.pt0.getX()
            yOn = self.pt0.getY()
        elif _t > 1.0:
            xOn = self.pt1.getX()
            yOn = self.pt1.getY()
        else:
            xOn = self.pt0.getX() + _t * vx
            yOn = self.pt0.getY() + _t * vy
        return Pnt2D(xOn, yOn)

    # ---------------------------------------------------------------------
    def evalPointTangent(self, _t):
        pt = self.evalPoint(_t)
        tangVec = self.pt1 - self.pt0
        return pt, tangVec

    # ---------------------------------------------------------------------
    def splitRaw(self, _t):
        if _t <= Curve.PARAM_TOL:
            left = None
            right = self
            return left, right
        if (1.0 - _t) <= Curve.PARAM_TOL:
            left = self
            right = None
            return left, right

        pt = self.evalPoint(_t)
        left = Line(self.pt0, pt)
        ptr = Pnt2D(pt.getX(), pt.getY())
        right = Line(ptr, self.pt1)
        return left, right

    # ---------------------------------------------------------------------
    def split(self, _t):
        left, right = self.splitRaw(_t) 
        return left, right

    # ---------------------------------------------------------------------
    def join(self, _joinCurve, _pt, _tol):
        if (_joinCurve.getType() != 'LINE') and (_joinCurve.getType() != 'POLYLINE'):
            return False, None, 'Cannot join segments:\n A LINE curve may be joined only with a LINE or a POLYLINE.'

        # Order the points of the two curves. The first curve is always
        # the self.
        # It is assumed that the given point _pt is the common point of
        # the curves to be joined.
        selfPtInit = self.getPntInit()
        selfPtEnd = self.getPntEnd()
        otherPtInit = _joinCurve.getPntInit()
        otherPtEnd = _joinCurve.getPntEnd()
        if ((Pnt2D.euclidiandistance(selfPtEnd, _pt) < _tol) and
            (Pnt2D.euclidiandistance(otherPtEnd, _pt) < _tol)):
            ptInit = selfPtInit
            ptMid = selfPtEnd
            ptEnd = otherPtInit
            otherReversed = True
        elif ((Pnt2D.euclidiandistance(selfPtInit, _pt) < _tol) and
              (Pnt2D.euclidiandistance(otherPtInit, _pt) < _tol)):
            ptInit = selfPtEnd
            ptMid = selfPtInit
            ptEnd = otherPtEnd
            otherReversed = False
        elif ((Pnt2D.euclidiandistance(selfPtInit, _pt) < _tol) and
              (Pnt2D.euclidiandistance(otherPtEnd, _pt) < _tol)):
            ptInit = selfPtEnd
            ptMid = selfPtInit
            ptEnd = otherPtInit
            otherReversed = True
        else: # default: self is left and other is right
            ptInit = selfPtInit
            ptMid = selfPtEnd
            ptEnd = otherPtEnd
            otherReversed = False

        # If the other curve is straight and the three points form a
        # straight line, create a LINE curve. Otherwise, create a polyline.
        if _joinCurve.isStraight(_tol):
            if CompGeom.pickLine(ptInit, ptEnd, ptMid, _tol):
                crv = Line(ptInit, ptEnd)
            else:
                pts = []
                pts.append(ptInit)
                pts.append(ptMid)
                pts.append(ptEnd)
                crv = Polyline(pts)
        else:
            otherPts = _joinCurve.getCtrlPoints()
            pts = []
            pts.append(ptInit)
            if otherReversed:
                for i in range(len(otherPts) - 1, -1, -1):
                    pts.append(otherPts[i])
            else:
                for i in range(0, len(otherPts)):
                    pts.append(otherPts[i])
            crv = Polyline(pts)

        return True, crv, None

    # ---------------------------------------------------------------------
    def getEquivPolyline(self):
        equivPoly = []
        if self.nPts == 2:
            equivPoly.append(self.pt0)
            equivPoly.append(self.pt1)
        return equivPoly

    # ---------------------------------------------------------------------
    def getEquivPolylineCollecting(self, _pt):
        tempPts = []
        if self.nPts == 2:
            tempPts.append(self.pt0)
            tempPts.append(self.pt1)
        elif self.nPts == 1:
            tempPts.append(self.pt0)
            tempPts.append(_pt)
        return tempPts

    # ---------------------------------------------------------------------
    def closestPoint(self, _x, _y):
        p0 = self.pt0
        p1 = self.pt1
        pt = Pnt2D(_x, _y)
        dist, clstPt, t = CompGeom.getClosestPointSegment(p0, p1, pt)
        tangVec = self.pt1 - self.pt0
        return True, clstPt, dist, t, tangVec

    # ---------------------------------------------------------------------
    def closestPointParam(self, _x, _y, _tStart):
        clstPt, tangVec = self.evalPointTangent(_tStart)
        if ((abs(clstPt.getX() - _x) < Curve.COORD_TOL) and
            (abs(clstPt.getY() - _y) < Curve.COORD_TOL)):
            return True, clstPt, 0.0, _tStart, tangVec

        status, clstPt, dist, t, tangVec = self.closestPoint(_x, _y)
        return status, clstPt, dist, t, tangVec

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        xmax = max(self.pt0.getX(), self.pt1.getX())
        xmin = min(self.pt0.getX(), self.pt1.getX())
        ymax = max(self.pt0.getY(), self.pt1.getY())
        ymin = min(self.pt0.getY(), self.pt1.getY())
        return xmin, xmax, ymin, ymax

    # ---------------------------------------------------------------------
    def getXinit(self):
        return self.pt0.getX()

    # ---------------------------------------------------------------------
    def getYinit(self):
        return self.pt0.getY()

    # ---------------------------------------------------------------------
    def getXend(self):
        return self.pt1.getX()

    # ---------------------------------------------------------------------
    def getYend(self):
        return self.pt1.getY()

    # ---------------------------------------------------------------------
    def getPntInit(self):
        return self.pt0

    # ---------------------------------------------------------------------
    def getPntEnd(self):
        return self.pt1

    # ---------------------------------------------------------------------
    def length(self):
        if self.nPts != 2:
            return 0.0
        L = math.sqrt((self.pt1.getX() - self.pt0.getX()) *
                      (self.pt1.getX() - self.pt0.getX()) +
                      (self.pt1.getY() - self.pt0.getY()) *
                      (self.pt1.getY() - self.pt0.getY()))
        return L
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve
from geometry.curves.polyline import Polyline
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

    def splitRaw(self, _t):
        if self.nPts < 2:
            return Line([]), Line([])
        if _t <= 0.0:
            return Line([]), Line(self.getCtrlPoints())
        if _t >= 1.0:
            return Line(self.getCtrlPoints()), Line([])
        pt = self.evalPoint(_t)
        left = Line([self.pts[0], pt])
        right = Line([pt, self.pts[1]])
        return left, right

    def split(self, _t):
        return self.splitRaw(_t)

    def join(self, _joinCurve, _pt, _tol):
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