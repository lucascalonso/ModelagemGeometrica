from hetool.geometry.point import Point
from geometry.curves.curve import Curve
import math

class CircleArc(Curve):
    def __init__(self):
        super().__init__()
        self.type = 'CIRCLEARC'
        self.center = None
        self.radius = 0.0
        self.startAngle = 0.0
        self.endAngle = 0.0

    def addCtrlPoint(self, x, y):
        self.ctrlPts.append(Point(x, y))
        self.nPts = len(self.ctrlPts)
        
        if self.nPts == 1:
            self.center = self.ctrlPts[0]
        elif self.nPts == 2:
            dx = x - self.center.getX()
            dy = y - self.center.getY()
            self.radius = math.sqrt(dx*dx + dy*dy)
            self.startAngle = math.atan2(dy, dx)
        elif self.nPts == 3:
            dx = x - self.center.getX()
            dy = y - self.center.getY()
            self.endAngle = math.atan2(dy, dx)

    def getEquivPolylineCollecting(self, tempPt):
        if self.nPts == 1:
            # Mostra linha do raio (Centro -> Mouse)
            return [self.center, tempPt]
        elif self.nPts == 2:
            # Mostra o arco do ponto inicial até o mouse
            temp_arc = CircleArc()
            temp_arc.addCtrlPoint(self.center.getX(), self.center.getY())
            temp_arc.addCtrlPoint(self.ctrlPts[1].getX(), self.ctrlPts[1].getY())
            temp_arc.addCtrlPoint(tempPt.getX(), tempPt.getY())
            return temp_arc.getEquivPolyline()
        return []

    def getEquivPolyline(self, tol=0.5):
        if self.radius <= 0: return []

        sa = self.startAngle
        ea = self.endAngle
        if ea < sa: ea += 2 * math.pi
        
        total_angle = ea - sa
        
        if tol >= self.radius: steps = 2
        else:
            angle_step = 2 * math.acos(1 - tol/self.radius)
            steps = int(math.ceil(total_angle / angle_step))
            steps = max(steps, 2)

        pts = []
        for i in range(steps + 1):
            theta = sa + total_angle * i / steps
            px = self.center.getX() + self.radius * math.cos(theta)
            py = self.center.getY() + self.radius * math.sin(theta)
            pts.append(Point(px, py))
        return pts