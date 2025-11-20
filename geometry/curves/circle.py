from compgeom.pnt2d import Pnt2D
from geometry.curves.curve import Curve
from geometry.curves.circlearc import CircleArc
import math


class Circle(Curve):

    deltaAng = math.pi / 32.0

    def __init__(self, _center=None, _circ1=None):
        super(Curve, self).__init__()
        self.type = 'CIRCLE'
        self.center = _center
        self.circ1 = _circ1
        self.nPts = 0
        self.eqPoly = []
        if _center is not None:
            self.nPts += 1
        if _circ1 is not None:
            self.nPts += 1
        self.radius = 0.0
        self.ang1 = 0.0  # Angle of circle point (0 <= angle < +2PI)

        if self.nPts == 2:
            drX1 = self.circ1.getX() - self.center.getX()
            drY1 = self.circ1.getY() - self.center.getY()
            self.radius = math.sqrt(drX1 * drX1 + drY1 * drY1)
            if self.radius > 0.0:
                # Compute angle
                ang = math.atan2(drY1, drX1)
                # Convert angle to a positive angle less than 2PI
                if ang < 0.0:
                    ang += 2.0 * math.pi
                self.ang1 = ang

    # ---------------------------------------------------------------------
    def computeEquivPolyline(self):
        self.eqPoly.clear()
        if self.nPts != 2 or self.radius <= 0.0:
            return
        # Amostragem completa da circunferência
        ang = 0.0
        while ang < 2.0 * math.pi - 1e-12:
            x = self.center.getX() + self.radius * math.cos(ang)
            y = self.center.getY() + self.radius * math.sin(ang)
            self.eqPoly.append(Pnt2D(x, y))
            ang += Circle.deltaAng
        # Garante fechamento visual (último ponto)
        self.eqPoly.append(Pnt2D(self.center.getX() + self.radius,
                                 self.center.getY()))

    # ---------------------------------------------------------------------
    def setPoints(self, _x0, _y0, _x1, _y1):
        self.center = Pnt2D(_x0, _y0)
        self.circ1 = Pnt2D(_x1, _y1)
        self.nPts = 2
        drX1 = self.circ1.getX() - self.center.getX()
        drY1 = self.circ1.getY() - self.center.getY()
        self.radius = math.sqrt(drX1 * drX1 + drY1 * drY1)
        if self.radius > 0.0:
            ang = math.atan2(drY1, drX1)
            if ang < 0.0:
                ang += 2.0 * math.pi
            self.ang1 = ang
        self.eqPoly.clear()

    # ---------------------------------------------------------------------
    def addCtrlPoint(self, _x, _y):
        # **** COMPLETE HERE: CIRCLE_01 ****
        if self.nPts == 0:
            self.center = Pnt2D(_x, _y)
            self.nPts = 1
            return True
        if self.nPts == 1:
            self.circ1 = Pnt2D(_x, _y)
            self.nPts = 2
            drX1 = self.circ1.getX() - self.center.getX()
            drY1 = self.circ1.getY() - self.center.getY()
            self.radius = math.hypot(drX1, drY1)
            ang = math.atan2(drY1, drX1)
            if ang < 0.0:
                ang += 2.0 * math.pi
            self.ang1 = ang
            self.eqPoly.clear()
            return True
        return False

    # ---------------------------------------------------------------------
    def isPossible(self):
        return self.nPts == 2 and self.radius > 0.0

    # ---------------------------------------------------------------------
    def getCtrlPoints(self):
        if self.nPts == 0:
            return []
        if self.nPts == 1:
            return [self.center]
        return [self.center, self.circ1]

    # ---------------------------------------------------------------------
    def getNumberOfReshapeCtrlPoints(self):
        return 2 if self.nPts == 2 else 0

    # ---------------------------------------------------------------------
    def getReshapeCtrlPoints(self):
        return self.getCtrlPoints()

    # ---------------------------------------------------------------------
    def setCtrlPoint(self, _id, _x, _y, _tol):
        if _id < 0 or _id >= self.nPts:
            return False
        if _id == 0:
            self.center.setX(_x)
            self.center.setY(_y)
        else:
            self.circ1.setX(_x)
            self.circ1.setY(_y)
        if self.nPts == 2:
            drX1 = self.circ1.getX() - self.center.getX()
            drY1 = self.circ1.getY() - self.center.getY()
            self.radius = math.hypot(drX1, drY1)
            ang = math.atan2(drY1, drX1)
            if ang < 0.0:
                ang += 2.0 * math.pi
            self.ang1 = ang
        self.eqPoly.clear()
        return True

    # ---------------------------------------------------------------------
    def isStraight(self, _tol):
        return False  # círculo nunca é segmento

    # ---------------------------------------------------------------------
    def isClosed(self):
        # **** COMPLETE HERE: CIRCLE_04 ****
        return self.isPossible()

    # ---------------------------------------------------------------------
    def evalPoint(self, _t):
        # **** COMPLETE HERE: CIRCLE_05 ****
        if not self.isPossible():
            return Pnt2D(0.0, 0.0)
        t = max(0.0, min(1.0, _t))
        ang = 2.0 * math.pi * t
        x = self.center.getX() + self.radius * math.cos(ang)
        y = self.center.getY() + self.radius * math.sin(ang)
        return Pnt2D(x, y)

    # ---------------------------------------------------------------------
    def evalPointTangent(self, _t):
        # **** COMPLETE HERE: CIRCLE_06 ****
        pt = self.evalPoint(_t)
        if not self.isPossible():
            return pt, Pnt2D(0.0, 0.0)
        t = max(0.0, min(1.0, _t))
        ang = 2.0 * math.pi * t
        # Derivada paramétrica não normalizada: (-r sin ang, r cos ang)
        dx = -self.radius * math.sin(ang)
        dy = self.radius * math.cos(ang)
        norm = math.hypot(dx, dy)
        tang = Pnt2D(dx / norm, dy / norm) if norm > 0.0 else Pnt2D(0.0, 0.0)
        return pt, tang

    # ---------------------------------------------------------------------
    def splitRaw(self, _t):
        # **** COMPLETE HERE: CIRCLE_07 ****
        if not self.isPossible():
            return None, None
        t = max(0.0, min(1.0, _t))
        angSplit = 2.0 * math.pi * t
        # Cria dois CircleArc cobrindo a circunferência
        left = CircleArc(self.center, self.radius, 0.0, angSplit)
        right = CircleArc(self.center, self.radius, angSplit, 2.0 * math.pi)
        return left, right

    # ---------------------------------------------------------------------
    def split(self, _t):
        left, right = self.splitRaw(_t)
        if left is not None:
            left.computeEquivPolyline()
        if right is not None:
            right.computeEquivPolyline()
        return left, right

    # ---------------------------------------------------------------------
    def join(self, _joinCurve, _pt, _tol):
        return False, None, 'Cannot join segments:\n A closed curve may not be joined with another curve.'

    # ---------------------------------------------------------------------
    def getEquivPolyline(self):
        equivPoly = []
        if self.nPts != 2:
            return equivPoly

        # Compute equivalent polygonal of current circle if
        # it is not already created
        if self.eqPoly == []:
            self.computeEquivPolyline()

        for i in range(0, len(self.eqPoly)):
            equivPoly.append(self.eqPoly[i])
        return equivPoly

    # ---------------------------------------------------------------------
    def getEquivPolylineCollecting(self, _pt):
        # **** COMPLETE HERE: CIRCLE_08 ****
        # Estados:
        # nPts==0: nada
        # nPts==1 (+ preview): mostrar círculo provisório usando _pt como circ1
        # nPts==2: polilinha definitiva
        if self.nPts == 0:
            return []
        if self.nPts == 1 and _pt is not None:
            temp = Pnt2D(_pt.getX(), _pt.getY()) if hasattr(_pt, 'getX') else _pt
            r = math.hypot(temp.getX() - self.center.getX(),
                           temp.getY() - self.center.getY())
            if r <= 0.0:
                return [self.center]
            pts = []
            ang = 0.0
            while ang < 2.0 * math.pi - 1e-12:
                x = self.center.getX() + r * math.cos(ang)
                y = self.center.getY() + r * math.sin(ang)
                pts.append(Pnt2D(x, y))
                ang += Circle.deltaAng
            pts.append(Pnt2D(self.center.getX() + r, self.center.getY()))
            return pts
        if not self.isPossible():
            return self.getCtrlPoints()
        return self.getEquivPolyline()

    # ---------------------------------------------------------------------
    def closestPoint(self, _x, _y):
        # **** COMPLETE HERE: CIRCLE_09 ****
        if not self.isPossible():
            return True, Pnt2D(0.0, 0.0), 0.0, 0.0, Pnt2D(0.0, 0.0)
        dx = _x - self.center.getX()
        dy = _y - self.center.getY()
        distCenter = math.hypot(dx, dy)
        if distCenter == 0.0:
            # ponto no centro: devolve circ1
            clstPt = Pnt2D(self.circ1.getX(), self.circ1.getY())
            t = self.ang1 / (2.0 * math.pi)
            _, tangVec = self.evalPointTangent(t)
            return True, clstPt, self.radius, t, tangVec
        # Projeção na circunferência
        nx = dx / distCenter
        ny = dy / distCenter
        clstPt = Pnt2D(self.center.getX() + self.radius * nx,
                       self.center.getY() + self.radius * ny)
        ang = math.atan2(clstPt.getY() - self.center.getY(),
                         clstPt.getX() - self.center.getX())
        if ang < 0.0:
            ang += 2.0 * math.pi
        t = ang / (2.0 * math.pi)
        dist = abs(distCenter - self.radius)
        _, tangVec = self.evalPointTangent(t)
        return True, clstPt, dist, t, tangVec

    # ---------------------------------------------------------------------
    def closestPointParam(self, _x, _y, _tStart):
        # Refinamento trivial: usa projeção direta ignorando _tStart
        return self.closestPoint(_x, _y)

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        if not self.isPossible():
            return 0.0, 0.0, 0.0, 0.0
        xmin = self.center.getX() - self.radius
        xmax = self.center.getX() + self.radius
        ymin = self.center.getY() - self.radius
        ymax = self.center.getY() + self.radius
        return xmin, xmax, ymin, ymax