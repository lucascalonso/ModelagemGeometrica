from hetool.geometry.point import Point
from geometry.curves.curve import Curve
import math

class Circle(Curve):
    def __init__(self):
        super().__init__()
        self.type = 'CIRCLE'
        self.center = None
        self.radius = 0.0

    def addCtrlPoint(self, x, y):
        self.ctrlPts.append(Point(x, y))
        self.nPts = len(self.ctrlPts)
        if self.nPts == 1:
            self.center = self.ctrlPts[0]
        elif self.nPts == 2:
            dx = self.ctrlPts[1].getX() - self.center.getX()
            dy = self.ctrlPts[1].getY() - self.center.getY()
            self.radius = math.sqrt(dx*dx + dy*dy)

    def getEquivPolylineCollecting(self, tempPt):
        if self.nPts == 1:
            # Simula o círculo com o raio definido pela distância até o mouse
            temp_c = Circle()
            temp_c.addCtrlPoint(self.center.getX(), self.center.getY())
            temp_c.addCtrlPoint(tempPt.getX(), tempPt.getY())
            return temp_c.getEquivPolyline()
        return []

    def getEquivPolyline(self, tol=0.5):
        if self.radius <= 0: return []
        
        if tol >= self.radius: steps = 4
        else:
            angle_step = 2 * math.acos(1 - tol/self.radius)
            steps = int(math.ceil(2 * math.pi / angle_step))
            steps = max(steps, 12)

        pts = []
        for i in range(steps + 1):
            theta = 2 * math.pi * i / steps
            px = self.center.getX() + self.radius * math.cos(theta)
            py = self.center.getY() + self.radius * math.sin(theta)
            pts.append(Point(px, py))
        return pts