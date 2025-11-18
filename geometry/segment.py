from compgeom.pnt2d import Pnt2D
from geometry.point import Point
from geometry.curves.curve import Curve
from compgeom.compgeom import CompGeom


class Segment():
    def __init__(self, _curve=None):
        self.curve = _curve  # owning curve (can be empty [])
        self.polyline = None  # segment equiv. polyline
        self.selected = False
        self.nSdv = None
        self.sdvPoints = None
        if self.curve != None:
            self.polyline = self.curve.getEquivPolyline()

    # ---------------------------------------------------------------------
    def setCurve(self, _curve):
        self.curve = _curve  # owning curve
        if self.curve != None:
            self.polyline = self.curve.getEquivPolyline()

    # ---------------------------------------------------------------------
    def resetEquivPolyline(self):
        if self.curve != None:
            self.polyline = self.curve.getEquivPolyline()

    # ---------------------------------------------------------------------
    def getCurve(self):
        return self.curve

    # ---------------------------------------------------------------------
    def setSelected(self, _status):
        self.selected = _status

    # ---------------------------------------------------------------------
    def isSelected(self):
        return self.selected

    # ---------------------------------------------------------------------
    def getPolylinePts(self):
        return self.polyline

    # ---------------------------------------------------------------------
    def getInitTangent(self):
        pt, tan = self.curve.evalPointTangent(0.0)
        tan = Pnt2D.normalize(tan)
        return tan

    # ---------------------------------------------------------------------
    def getEndTangent(self):
        pt, tan = self.curve.evalPointTangent(1.0)
        tan = Pnt2D.normalize(tan)
        return tan

    # ---------------------------------------------------------------------
    def intersectPoint(self, _pt, _tol):
        status, clstPt, dmin, t, tang = self.curve.closestPoint(_pt.getX(), _pt.getY())
        if dmin <= _tol:
            return True, t, clstPt
        else:
            return False, t, clstPt

    # ---------------------------------------------------------------------
    def split(self, _params, _pts):
        curv2 = self.curve
        segments = []

        # It is assumed the lists _params and _pts are ordered in crescent order
        # of parametric values of intesection points.

        # Recursively split curve based on parametric values
        for i in range(0, len(_pts)):
            status, clstPt, dmin, t, tangVec = curv2.closestPointParam(
                                    _pts[i].getX(), _pts[i].getY(), _params[i])
            curv1, curv2 = curv2.split(t)

            if curv1 is not None:
                seg1 = Segment(curv1)
                segments.append(seg1)
            else:
                segments.append([])

            # update the remaining parameters
            for j in range(i+1, len(_params)):
                _params[j] = (_params[j] - _params[i])/(1.0 - _params[i])

        if curv2 is not None:
            seg2 = Segment(curv2)
            segments.append(seg2)
        else:
            segments.append([])

        # Force initial and end polyline points of each created segment to
        # be equal to do given split points.
        for i in range(0, len(_pts)):
                seg1 = segments[i]
                seg2 = segments[i + 1]
                if seg1 != []:
                    seg1.polyline[-1].setX(_pts[i].getX())
                    seg1.polyline[-1].setY(_pts[i].getY())
                if seg2 != []:
                    seg2.polyline[0].setX(_pts[i].getX())
                    seg2.polyline[0].setY(_pts[i].getY())

        return segments

    # ---------------------------------------------------------------------
    def length(self):
        lenSeg = self.curve.length()
        return lenSeg

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        return self.curve.evalPoint(_t)

    # ---------------------------------------------------------------------
    def getXinit(self):
        return self.curve.getXinit()

    # ---------------------------------------------------------------------
    def getYinit(self):
        return self.curve.getYinit()

    # ---------------------------------------------------------------------
    def getXend(self):
        return self.curve.getXend()

    # ---------------------------------------------------------------------
    def getYend(self):
        return self.curve.getYend()

    # ---------------------------------------------------------------------
    def getPntInit(self):
        return self.curve.getPntInit()
    
    # ---------------------------------------------------------------------
    def getPntEnd(self):
        return self.curve.getPntEnd()

    # ---------------------------------------------------------------------
    def getType(self):
        return self.curve.getType()

    # ---------------------------------------------------------------------
    def closestPoint(self, _x, _y):
        status, clstPt, dmin, t, tang = self.curve.closestPoint(_x, _y)
        xOn = clstPt.getX()
        yOn = clstPt.getY()
        if status:
            if (t < 0.0) or (t > 1.0):
                return False, xOn, xOn, dmin
        return status, xOn, yOn, dmin

    # ---------------------------------------------------------------------
    def canReshape(self):
        return True

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        # Compute segment bounding box based on segment polypoints
        x = []
        y = []
        for point in self.polyline:
            x.append(point.getX())
            y.append(point.getY())
        xmin = min(x)
        xmax = max(x)
        ymin = min(y)
        ymax = max(y)
        return xmin, xmax, ymin, ymax
