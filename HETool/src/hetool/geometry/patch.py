from hetool.geometry.point import Point
from hetool.compgeom.tesselation import Tesselation
from hetool.compgeom.compgeom import CompGeom


class Patch:

    def __init__(self, _pts=None, _segments=None, _segmentOrients=None):
        self.pts = _pts if _pts is not None else []
        self.segments = _segments if _segments is not None else []
        self.segmentOrients = _segmentOrients if _segmentOrients is not None else []
        self.mesh = None
        self.selected = False
        self.holes = []  # vector of region holes
        self.holesOrients = []
        self.isDeleted = False
        self.face = None
        self.triangles = [] # Adicionado para armazenar a tesselação


    def __del__(self):
        if hasattr(self, 'mesh') and self.mesh:
            del self.mesh

    def setBoundary(self, segments, orients):
        self.segments = segments
        self.segmentOrients = orients

    def addHole(self, hole_pts):
        self.holes.append(hole_pts)

    def setTriangles(self, triangles):
        self.triangles = triangles

    def getTriangles(self):
        return self.triangles
    
    def getPoints(self):
        return self.pts

    def getSegments(self):
        return self.segments

    def getSegmentOrients(self):
        return self.segmentOrients

    def setSelected(self, _select):
        self.selected = _select

    def isSelected(self):
        return self.selected

    def setMesh(self, _pts, _conn):
        self.mesh = (_pts, _conn)

    def getMesh(self):
        return self.mesh

    def getBoundBox(self):

        if len(self.pts) == 0:
            return

        xmin = self.pts[0].getX()
        ymin = self.pts[0].getY()
        xmax = self.pts[0].getX()
        ymax = self.pts[0].getY()

        if len(self.pts) == 1:
            return

        for j in range(1, len(self.pts)):
            xmin = min(xmin, self.pts[j].getX())
            xmax = max(xmax, self.pts[j].getX())
            ymin = min(ymin, self.pts[j].getY())
            ymax = max(ymax, self.pts[j].getY())

        return xmin, xmax, ymin, ymax

    def setHoles(self, _holessegments, _isOriented):
        self.holes = _holessegments
        self.holesOrients = _isOriented

    def setInternalSegments(self, _internalSegments, _isOriented):
        self.internalSegments = _internalSegments
        self.internalSegmentsOrients = _isOriented

    def isPointInside(self, _pt):
        numIntersec = 0
        for i in range(0, len(self.segments)):
            numIntersec += self.segments[i].ray(_pt)

        if numIntersec % 2 != 0:
            for i in range(0, len(self.holes)):
                numIntersec = 0
                for j in range(0, len(self.holes[i])):
                    numIntersec += self.holes[i][j].ray(_pt)

                if numIntersec % 2 != 0:
                    return False

            return True

        else:
            return False

    def boundaryPolygon(self):
        polygon = []
        for i in range(0, len(self.segments)):
            segmentPol = self.segments[i].getPoints()
            if self.segmentOrients[i]:
                for j in range(0, len(segmentPol)-1):
                    polygon.append(segmentPol[j])
            else:
                for j in range(len(segmentPol)-1, 0, -1):
                    polygon.append(segmentPol[j])

        return polygon

    def boundaryHole(self):
        polygons = []

        for i in range(0, len(self.holes)):
            polygon = []
            for j in range(0, len(self.holes[i])):
                segmentpol = self.holes[i][j].getPoints()
                if self.holesOrients[i][j]:
                    for m in range(0, len(segmentpol)-1):
                        polygon.append(segmentpol[m])
                else:
                    for m in range(len(segmentpol)-1, 0, -1):
                        polygon.append(segmentpol[m])

            polygon.reverse()
            polygons.append(polygon)

        return polygons

    def boundaryInternalSegments(self):
        polygons = []
        for i in range(0, len(self.internalSegments)):
            polygon = []
            for j in range(0, len(self.internalSegments[i])):
                segmentpol = self.internalSegments[i][j].getPoints()
                if self.internalSegmentsOrients[i][j]:
                    for m in range(0, len(segmentpol)-1):
                        polygon.append(segmentpol[m])
                else:
                    for m in range(len(segmentpol)-1, 0, -1):
                        polygon.append(segmentpol[m])

            polygon.reverse()
            polygons.append(polygon)

        return polygons

    def Area(self):
        Area = 0
        pts = self.pts
        triangs = Tesselation.triangleParing(pts)
        for j in range(0, len(triangs)):
            a = Point(pts[triangs[j][0]].getX(),
                      pts[triangs[j][0]].getY())
            b = Point(pts[triangs[j][1]].getX(),
                      pts[triangs[j][1]].getY())
            c = Point(pts[triangs[j][2]].getX(),
                      pts[triangs[j][2]].getY())

            Area += (a.getX()*b.getY() - a.getY()*b.getX()
                     + a.getY()*c.getX() - a.getX()*c.getY()
                     + b.getX()*c.getY() - c.getX()*b.getY()) / 2.0

        internalFaces = self.face.internalFaces()
        if len(internalFaces) > 0:
            for face in internalFaces:
                Area -= face.patch.Area()
                adjacentFaces = face.adjacentFaces()
                for adjface in adjacentFaces:
                    if adjface not in internalFaces and adjface != self.face:
                        pts = adjface.patch.getPoints()
                        if CompGeom.isPointInPolygon(self.pts, pts[0]):
                            Area -= adjface.patch.Area()

        return Area

# ---------------------- MUDANÇAS LUCAS ------------------------------------

    # Retorna a estrutura de loops (número de subdivisões por segmento)
    def getMeshLoops(self):
        loops = []
        for seg in self.segments:
            n = 1
            # Procura atributo de subdivisão
            if hasattr(seg, 'attributes'):
                for att in seg.attributes:
                    if att['name'] == "Nsbdvs":
                        n = att['properties']['Value']
                        break
            loops.append(n)
        return loops

    # Retorna todos os pontos da fronteira discretizados para a geração da malha
    def getMeshBdryPoints(self):
        points = []
        for i in range(len(self.segments)):
            seg = self.segments[i]
            orient = self.segmentOrients[i]
            
            n = 1
            if hasattr(seg, 'attributes'):
                for att in seg.attributes:
                    if att['name'] == "Nsbdvs":
                        n = att['properties']['Value']
                        break
            
            # Define direção baseada na orientação do segmento no patch
            if orient: # True = Sentido original
                start_t, end_t = 0.0, 1.0
            else:      # False = Sentido invertido
                start_t, end_t = 1.0, 0.0
            
            # Gera n pontos (o último ponto do segmento é o primeiro do próximo)
            for k in range(n):
                t = start_t + (end_t - start_t) * (k / float(n))
                # Assume que o segmento tem método getPoint (Polyline/Line)
                pt = seg.getPoint(t) 
                points.append(pt)
                
        return points