from hetool.geometry.point import Point
from hetool.compgeom.tesselation import Tesselation
from hetool.compgeom.compgeom import CompGeom
import math


class Patch:

    def __init__(self, _pts=None, _segments=None, _segmentOrients=None):
        self.pts = _pts if _pts is not None else []
        self.segments = _segments if _segments is not None else []
        self.segmentOrients = _segmentOrients if _segmentOrients is not None else []
        self.mesh = None
        self.selected = False
        self.holes = []
        self.holesOrients = []
        self.isDeleted = False
        self.face = None
        self.triangles = []
        self.attributes = []


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
            return 0.0, 0.0, 0.0, 0.0

        xmin = self.pts[0].getX()
        ymin = self.pts[0].getY()
        xmax = self.pts[0].getX()
        ymax = self.pts[0].getY()

        if len(self.pts) == 1:
            return xmin, xmax, ymin, ymax


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
        
        # 1. Loop Externo
        outer_loop = []
        # Ordena segmentos para garantir continuidade
        ordered_segments = self._sort_segments(self.segments)
        
        for seg in ordered_segments:
            n = 1
            if hasattr(seg, 'attributes'):
                for att in seg.attributes:
                    if att['name'] == "Nsbdvs":
                        n = att['properties']['Value']
                        break
            outer_loop.append(n)
            
        if not self.holes:
            return outer_loop
            
        loops.append(outer_loop)
        
        # 2. Loops dos Buracos
        for hole in self.holes:
            hole_loop = []
            ordered_hole = self._sort_segments(hole)
            for seg in ordered_hole:
                n = 1
                if hasattr(seg, 'attributes'):
                    for att in seg.attributes:
                        if att['name'] == "Nsbdvs":
                            n = att['properties']['Value']
                            break
                hole_loop.append(n)
            loops.append(hole_loop)
            
        return loops

    def getMeshBdryPoints(self):
        pts = []
        
        def collect_points(segment_list):
            collected = []
            # Ordena segmentos antes de coletar pontos
            ordered = self._sort_segments(segment_list)
            
            for seg in ordered:
                n = 1
                if hasattr(seg, 'attributes'):
                    for att in seg.attributes:
                        if att['name'] == "Nsbdvs":
                            n = att['properties']['Value']
                            break
                
                for i in range(n):
                    t = i / float(n)
                    collected.append(seg.getPoint(t))
            return collected

        pts.extend(collect_points(self.segments))
        
        if self.holes:
            for hole in self.holes:
                pts.extend(collect_points(hole))
                
        return pts

    # Ordena uma lista de segmentos para formar a cadeia contínua para Delaunay
    def _sort_segments(self, segments):
        if not segments or len(segments) < 2:
            return segments
            
        pool = list(segments)
        ordered = [pool.pop(0)]
        
        while pool:
            last_pt = ordered[-1].getPoint(1.0)
            found_idx = -1
            
            for i, seg in enumerate(pool):
                # Verifica se o inicio do seg conecta com o fim do ultimo
                # Correção: Calculando distância manualmente pois Point não tem .dist()
                p_start = seg.getPoint(0.0)
                dx = p_start.getX() - last_pt.getX()
                dy = p_start.getY() - last_pt.getY()
                dist = math.sqrt(dx*dx + dy*dy)
                
                if dist < 1e-4:
                    found_idx = i
                    break
            
            if found_idx != -1:
                ordered.append(pool.pop(found_idx))
            else:
                # Se não encontrar conexão, tenta conectar o próximo segmento
                ordered.append(pool.pop(0))
        return ordered