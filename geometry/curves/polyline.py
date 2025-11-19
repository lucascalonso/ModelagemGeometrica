from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
from geometry.curves.curve import Curve
import math
from geometry.curves.line import Line


class Polyline(Curve):
    def __init__(self, _pts=None):
        super().__init__()
        self.type = 'POLYLINE'
        self.pts = []
        if _pts is not None:
            for i in range(len(_pts)):
                # accept both Pnt2D and objects with getX/getY or tuples
                try:
                    self.pts.append(Pnt2D(_pts[i].getX(), _pts[i].getY()))
                except Exception:
                    self.pts.append(Pnt2D(float(_pts[i][0]), float(_pts[i][1])))
        self.nPts = len(self.pts)

    # ---------------------------------------------------------------------
    def isUnlimited(self):
        return True

    # ---------------------------------------------------------------------
    def addCtrlPoint(self, _x, _y):
        self.pts.append(Pnt2D(_x, _y))
        self.nPts = len(self.pts)
        return True

    # ---------------------------------------------------------------------
    def isPossible(self):
        # A polyline is possible if it has at least two control points
        return (self.nPts >= 2)

    # ---------------------------------------------------------------------
    def getCtrlPoints(self):
        tempPts = []
        for i in range(0, self.nPts):
            tempPts.append(self.pts[i])
        return tempPts

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
        for i in range(1, len(self.pts) - 1):
            if not CompGeom.pickLine(self.pts[0], self.pts[-1], self.pts[i], _tol):
                return False
        return True

    # ---------------------------------------------------------------------
    def isClosed(self):
        if self.nPts < 2:
            return False
        return (Pnt2D.euclidiandistance(self.pts[0], self.pts[-1]) <= Curve.COORD_TOL)

    # ---------------------------------------------------------------------
    def evalPointByLength(self, target_len):
        """Evaluates a point at a specific distance along the polyline's length."""
        if target_len <= 0.0:
            return self.pts[0]

        running_length = 0.0
        for i in range(self.nPts - 1):
            p1 = self.pts[i]
            p2 = self.pts[i+1]
            segment_length = math.hypot(p2.getX() - p1.getX(), p2.getY() - p1.getY())
            
            if running_length + segment_length >= target_len:
                # The point is on this segment
                remaining_len = target_len - running_length
                t = remaining_len / segment_length
                x = (1 - t) * p1.getX() + t * p2.getX()
                y = (1 - t) * p1.getY() + t * p2.getY()
                return Pnt2D(x, y)
            
            running_length += segment_length
        
        # If target_len is greater than or equal to total length, return the last point
        return self.pts[-1]
    # ---------------------------------------------------------------------
    # Evaluate a point for a given parametric value.
    # Also return the segment of the evaluated point and
    # the local parametric value in segment
    def evalPointSeg(self, _t):
        # Guards for invalid/degenerate lists
        if self.nPts == 0:
            return Pnt2D(0.0, 0.0), 0, 0.0
        if self.nPts == 1:
            return Pnt2D(self.pts[0].getX(), self.pts[0].getY()), 0, 0.0

        if _t <= 0.0:
            return Pnt2D(self.pts[0].getX(), self.pts[0].getY()), 0, 0.0

        if _t >= 1.0:
            # seg index may be clamped by callers
            return Pnt2D(self.pts[-1].getX(), self.pts[-1].getY()), self.nPts - 1, 1.0

        length = self.length()
        if length == 0.0:
            return Pnt2D(self.pts[0].getX(), self.pts[0].getY()), 0, 0.0

        s = _t * length
        loc_t = 1.0
        prev_id = 0
        next_id = 0
        lenToSeg = 0.0

        for i in range(1, len(self.pts)):
            prev_id = i - 1
            next_id = i
            dist = math.hypot(self.pts[i].getX() - self.pts[i - 1].getX(),
                              self.pts[i].getY() - self.pts[i - 1].getY())

            if (lenToSeg + dist) >= s:
                loc_t = 0.0 if dist == 0.0 else (s - lenToSeg) / dist
                break

            lenToSeg += dist

        x = self.pts[prev_id].getX() + loc_t * (self.pts[next_id].getX() - self.pts[prev_id].getX())
        y = self.pts[prev_id].getY() + loc_t * (self.pts[next_id].getY() - self.pts[prev_id].getY())

        return Pnt2D(x, y), prev_id, loc_t

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        pt, _, _ = self.evalPointSeg(_t)
        return pt

    # ---------------------------------------------------------------------
    def evalPointTangent(self, _t):
        pt, seg, loc_t = self.evalPointSeg(_t)
        if self.nPts < 2:
            return pt, Pnt2D(0.0, 0.0)
        if seg >= self.nPts - 1:
            seg = self.nPts - 2
        p0 = self.pts[seg]
        p1 = self.pts[seg + 1]
        dx = p1.getX() - p0.getX()
        dy = p1.getY() - p0.getY()
        norm = math.hypot(dx, dy)
        tangVec = Pnt2D(0.0, 0.0) if norm == 0.0 else Pnt2D(dx / norm, dy / norm)
        return pt, tangVec

    # ---------------------------------------------------------------------
    def splitRaw(self, _t):
        # split polyline at param _t into two polylines
        if self.nPts == 0:
            return Polyline([]), Polyline([])
        if _t <= 0.0:
            return Polyline([]), Polyline(self.getCtrlPoints())
        if _t >= 1.0:
            return Polyline(self.getCtrlPoints()), Polyline([])

        ptOn, seg, loc_t = self.evalPointSeg(_t)
        left_pts = []
        for i in range(0, seg + 1):
            left_pts.append(self.pts[i])
        left_pts.append(ptOn)

        right_pts = [ptOn]
        for i in range(seg + 1, self.nPts):
            right_pts.append(self.pts[i])

        left = Polyline(left_pts)
        right = Polyline(right_pts)
        return left, right

    # ---------------------------------------------------------------------
    def split(self, num_pieces):
        """Splits the polyline into a specified number of new Line objects of equal length."""
        if num_pieces < 2 or self.nPts < 2:
            return [self]

        total_length = self.length()
        if total_length == 0.0:
            return [self]

        new_lines = []
        length_per_piece = total_length / num_pieces
        current_point = self.pts[0]

        for i in range(num_pieces):
            target_length = (i + 1) * length_per_piece
            next_point = self.evalPointByLength(target_length)
            new_line = Line([current_point, next_point])
            new_lines.append(new_line)
            current_point = next_point
            
        return new_lines

    # ---------------------------------------------------------------------
    def join(self, _joinCurve, _pt, _tol):
        if (_joinCurve.getType() != 'LINE') and (_joinCurve.getType() != 'POLYLINE'):
            return False, None, 'Cannot join segments:\n A POLYLINE curve may be joined only with a LINE or a POLYLINE.'

        # Get the relative orientation of the two curves.
        # The first curve is always the self.
        # It is assumed that the given point _pt is the common point of
        # the curves to be joined.
        selfPtInit = self.getPntInit()
        selfPtEnd = self.getPntEnd()
        otherPtInit = _joinCurve.getPntInit()
        otherPtEnd = _joinCurve.getPntEnd()
        if ((Pnt2D.euclidiandistance(selfPtEnd, _pt) < _tol) and
            (Pnt2D.euclidiandistance(otherPtEnd, _pt) < _tol)):
            selfReversed = False
            otherReversed = True
        elif ((Pnt2D.euclidiandistance(selfPtInit, _pt) < _tol) and
              (Pnt2D.euclidiandistance(otherPtInit, _pt) < _tol)):
            selfReversed = True
            otherReversed = False
        elif ((Pnt2D.euclidiandistance(selfPtInit, _pt) < _tol) and
              (Pnt2D.euclidiandistance(otherPtEnd, _pt) < _tol)):
            selfReversed = True
            otherReversed = True
        else:  # default: self is left and other is right
            selfReversed = False
            otherReversed = False

        # Create a polyline with an ordered list of points.
        pts = []
        if selfReversed:
            for i in range(len(self.pts) - 1, -1, -1):
                pts.append(self.pts[i])
        else:
            for i in range(0, len(self.pts)):
                pts.append(self.pts[i])

        otherPts = _joinCurve.getCtrlPoints()
        if otherReversed:
            for i in range(len(otherPts) - 2, -1, -1):
                pts.append(otherPts[i])
        else:
            for i in range(1, len(otherPts)):
                pts.append(otherPts[i])
        crv = Polyline(pts)

        return True, crv, None

    # ---------------------------------------------------------------------
    def getEquivPolyline(self):
        equivPoly = []
        if self.nPts < 2:
            return equivPoly
        for i in range(0, self.nPts):
            equivPoly.append(self.pts[i])
        return equivPoly

    # ---------------------------------------------------------------------
    def getEquivPolylineCollecting(self, _pt):
        # Preview during collection:
        # - if >=1 ctrl point, append the temp point to draw the next segment
        # - if 0 ctrl points, return [] or just [_pt] (no segment anyway)
        if self.nPts == 0:
            if _pt is None:
                return []
            try:
                return [Pnt2D(_pt.getX(), _pt.getY())]
            except Exception:
                return [Pnt2D(float(_pt[0]), float(_pt[1]))]

        pts = [p for p in self.pts]
        if _pt is not None:
            try:
                pts.append(Pnt2D(_pt.getX(), _pt.getY()))
            except Exception:
                pts.append(Pnt2D(float(_pt[0]), float(_pt[1])))
        return pts

    # ---------------------------------------------------------------------
    # Returns the closest point on polyline for a given point.
    # Also returns the segment of the closest point and the arc
    # length from the curve init to the closest point.
    def closestPointSeg(self, _x, _y):
        if self.nPts < 2:
            return Pnt2D(0.0, 0.0), float('inf'), 0, 0.0

        pt = Pnt2D(_x, _y)
        d, clstPtSeg, t = CompGeom.getClosestPointSegment(self.pts[0], self.pts[1], pt)
        xOn = clstPtSeg.getX()
        yOn = clstPtSeg.getY()
        dmin = d
        seg = 0

        for i in range(1, self.nPts - 1):
            d, clstPtSeg, t = CompGeom.getClosestPointSegment(self.pts[i], self.pts[i + 1], pt)
            if d < dmin:
                xOn = clstPtSeg.getX()
                yOn = clstPtSeg.getY()
                dmin = d
                seg = i

        arcLen = 0.0
        for i in range(0, seg):
            arcLen += math.hypot(self.pts[i + 1].getX() - self.pts[i].getX(),
                                 self.pts[i + 1].getY() - self.pts[i].getY())
        arcLen += math.hypot(xOn - self.pts[seg].getX(), yOn - self.pts[seg].getY())

        clstPt = Pnt2D(xOn, yOn)
        return clstPt, dmin, seg, arcLen

    # ---------------------------------------------------------------------
    def closestPoint(self, _x, _y):
        if self.nPts < 2:
            # invalid polyline: report infinite distance and zero tangent
            pt = Pnt2D(0.0, 0.0) if self.nPts == 0 else self.pts[0]
            return True, pt, float('inf'), 0.0, Pnt2D(0.0, 0.0)

        clstPt, dmin, seg, arcLen = self.closestPointSeg(_x, _y)
        length = self.length()
        t = 0.0 if length == 0.0 else (arcLen / length)
        if seg >= self.nPts - 1:
            seg = self.nPts - 2
        p0 = self.pts[seg]
        p1 = self.pts[seg + 1]
        dx = p1.getX() - p0.getX()
        dy = p1.getY() - p0.getY()
        norm = math.hypot(dx, dy)
        tangVec = Pnt2D(0.0, 0.0) if norm == 0.0 else Pnt2D(dx / norm, dy / norm)
        return True, clstPt, dmin, t, tangVec

    # ---------------------------------------------------------------------
    def closestPointParam(self, _x, _y, _tStart):
        pt, tangVec = self.evalPointTangent(_tStart)
        if ((abs(pt.getX() - _x) < Curve.COORD_TOL) and
            (abs(pt.getY() - _y) < Curve.COORD_TOL)):
            return True, pt, 0.0, _tStart, tangVec

        status, clstPt, dist, t, tangVec = self.closestPoint(_x, _y)
        return status, clstPt, dist, t, tangVec

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        if self.nPts == 0:
            return 0.0, 0.0, 0.0, 0.0
        xs = [p.getX() for p in self.pts]
        ys = [p.getY() for p in self.pts]
        xmin = min(xs)
        xmax = max(xs)
        ymin = min(ys)
        ymax = max(ys)
        return xmin, xmax, ymin, ymax

    # ---------------------------------------------------------------------
    def getXinit(self):
        return self.pts[0].getX() if self.nPts >= 1 else 0.0

    # ---------------------------------------------------------------------
    def getYinit(self):
        return self.pts[0].getY() if self.nPts >= 1 else 0.0

    # ---------------------------------------------------------------------
    def getXend(self):
        return self.pts[-1].getX() if self.nPts >= 1 else 0.0

    # ---------------------------------------------------------------------
    def getYend(self):
        return self.pts[-1].getY() if self.nPts >= 1 else 0.0

    # ---------------------------------------------------------------------
    def getPntInit(self):
        return self.pts[0] if self.nPts >= 1 else Pnt2D(0.0, 0.0)

    # ---------------------------------------------------------------------
    def getPntEnd(self):
        return self.pts[-1] if self.nPts >= 1 else Pnt2D(0.0, 0.0)

    # ---------------------------------------------------------------------
    def length(self):
        if self.nPts < 2:
            return 0.0
        L = 0.0
        for i in range(0, self.nPts - 1):
            L += math.hypot(self.pts[i + 1].getX() - self.pts[i].getX(),
                            self.pts[i + 1].getY() - self.pts[i].getY())
        return L