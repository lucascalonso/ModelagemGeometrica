from hetool.geometry.point import Point

class Curve:
    PARAM_TOL = 1e-7
    COORD_TOL = 1e-5
    MIN_STEP_REDUCT = 0.005
    MAX_NUM_ITERAT = 100
    curveTypes = ['NONE', 'LINE', 'POLYLINE', 'QUADBEZIER', 'CUBICBEZIER', 'CIRCLE', 'CIRCLEARC']

    def __init__(self):
        self.type = 'NONE'
        self.ctrlPts = []
        self.nPts = 0

    def getType(self):
        return self.type

    def isUnlimited(self):
        return False

    def getNumberOfCtrlPoints(self):
        return len(self.ctrlPts)

    def addCtrlPoint(self, _x, _y):
        self.ctrlPts.append(Point(_x, _y))
        self.nPts = len(self.ctrlPts)

    def isPossible(self):
        return self.nPts >= 2

    def getCtrlPoints(self):
        return self.ctrlPts

    def getXinit(self):
        if self.nPts > 0: return self.ctrlPts[0].getX()
        return 0.0

    def getYinit(self):
        if self.nPts > 0: return self.ctrlPts[0].getY()
        return 0.0

    def getXend(self):
        if self.nPts > 0: return self.ctrlPts[-1].getX()
        return 0.0

    def getYend(self):
        if self.nPts > 0: return self.ctrlPts[-1].getY()
        return 0.0

    # Método padrão para preview: tenta criar uma cópia da curva com o ponto temporário
    def getEquivPolylineCollecting(self, tempPt):
        # Implementação padrão retorna vazio. Classes filhas devem sobrescrever.
        return []

    def getEquivPolyline(self, tol=0.5):
        pts = []
        self.genEquivPolyline(pts, tol)
        if self.nPts > 0:
            pts.append(self.ctrlPts[-1])
        return pts

    def genEquivPolyline(self, pts, tol):
        if self.isStraight(tol):
            if self.nPts > 0:
                pts.append(self.ctrlPts[0])
        else:
            c1, c2 = self.splitRaw(0.5)
            c1.genEquivPolyline(pts, tol)
            c2.genEquivPolyline(pts, tol)

    def isStraight(self, tol):
        return True

    def splitRaw(self, t):
        return self, self