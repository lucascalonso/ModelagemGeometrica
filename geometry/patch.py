from compgeom.pnt2d import Pnt2D
from geometry.segment import Segment


class Patch():
    def __init__(self, _pts=None, _segments=None, _segOrients=None):
        self.pts = _pts  # patch boundary points
        self.segments = _segments  # list of boundary segments
        self.segOrients = _segOrients  # list of segment orientations
        self.selected = False
        self.meshBdryPts = []
        self.meshPts = []
        self.meshConn = []

    # ---------------------------------------------------------------------
    def setSelected(self, _status):
        self.selected = _status

    # ---------------------------------------------------------------------
    def isSelected(self):
        return self.selected

    # ---------------------------------------------------------------------
    def getPoints(self):
        return self.pts

    # ---------------------------------------------------------------------
    def getSegments(self):
        return self.segments

    # ---------------------------------------------------------------------
    def getSegOrients(self):
        return self.segments

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        x = []
        y = []
        for point in self.pts:
            x.append(point.getX())
            y.append(point.getY())
        xmin = min(x)
        xmax = max(x)
        ymin = min(y)
        ymax = max(y)
        return xmin, xmax, ymin, ymax

    # ---------------------------------------------------------------------
    def getMeshLoops(self):
        loops = []
        segSbdvs = []
        for seg in self.segments:
            segSbdvs.append(seg.getNumberSdv())
        loops.append(segSbdvs)
        return loops

    # ---------------------------------------------------------------------
    def getMeshBdryPoints(self):
        bdryPts = []
        for i in range(len(self.segments)):
            seg = self.segments[i]
            segSdvPnts = seg.getSdvPoints()
            if self.segOrients[i]:
                bdryPts.append(seg.getPntInit())
                for j in range(len(segSdvPnts)):
                    bdryPts.append(segSdvPnts[j])
            else:
                bdryPts.append(seg.getPntEnd())
                for j in range(len(segSdvPnts) - 1, -1, -1):
                    bdryPts.append(segSdvPnts[j])
        return bdryPts

    # ---------------------------------------------------------------------
    def setMesh(self, _pts, _conn):
        self.meshPts = _pts
        self.meshConn = _conn

    # ---------------------------------------------------------------------
    def delMesh(self):
        if self.meshPts is not []:
            del self.meshPts
            self.meshPts = []
        if self.meshConn is not []:
            del self.meshConn
            self.meshConn = []

    # ---------------------------------------------------------------------
    def getMesh(self):
        return self.meshPts, self.meshConn
