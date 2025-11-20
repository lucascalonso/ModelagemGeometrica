from compgeom.pnt2d import Pnt2D
from geometry.segment import Segment


class MeshSegment():

    def __init__(self):
        self.isTurnedOn = False
        self.nsdv = 1
        self.ratio = 1.00

    def reset(self):
        self.nsdv = 1
        self.ratio = 1.00

    def setDisplayInfo(self, _isTurnedOn):
        self.isTurnedOn = _isTurnedOn

    def getDisplayInfo(self):
        return self.isTurnedOn

    def setNumberOfSubdivisions(self, _nsdv):
        self.nsdv = _nsdv

    def getNumberOfSubdivisions(self):
        return self.nsdv

    def setSubdivisionRatio(self, _ratio):
        self.ratio = _ratio

    def getSubdivisionRatio(self):
        return self.ratio

    @staticmethod
    def generateLineSdvPnts(_p1, _p2, _nsdv, _ratio):
        coords = []
        n_pts = _nsdv-1

        for i in range(0, n_pts):
            coords.insert(i, Pnt2D())

        x0 = _p1.x
        y0 = _p1.y
        x1 = _p2.x
        y1 = _p2.y

        _ratio = 1.0 / _ratio
        a = (2.0 * _ratio) / ((_ratio + 1.0) * _nsdv)
        b = (a * (1.0 - _ratio)) / (2.0 * _ratio * (_nsdv - 1.0))

        for i in range(1, _nsdv):
            v = a * i + b * i * (i - 1.0)
            u = 1.0 - v
            coords[i-1].x = u * x0 + v * x1
            coords[i-1].y = u * y0 + v * y1

        return coords

    @staticmethod
    def generateSegmentSdvPnts(_segment, _nsdv, _ratio):
        length = _segment.length()
        coords = []

        if _nsdv <= 1 or _ratio == 0.0:
            return coords

        # Calculate as if it were straight to find interpolation parameters
        r1 = Pnt2D(0.0, 0.0)
        r2 = Pnt2D(length, 0.0)
        coords = MeshSegment.generateLineSdvPnts(r1, r2, _nsdv, _ratio)

        # Calculate the coordinates of the actual points on the segment
        pts = []
        for coord in coords:
            t = coord.x / length
            pts.append(_segment.evalPoint(t))

        return pts
