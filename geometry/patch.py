from compgeom.pnt2d import Pnt2D

class Patch:

    def __init__(self, _pts, _segments, _segmentOrients):
        self.pts = _pts  # boundary points (vertices of the polygon)
        self.segments = _segments  # vector of boundary segments
        # orientations of segments with respect to counter-clockwise region boundary
        self.segmentOrients = _segmentOrients
        self.mesh = None
        self.selected = False
        self.holes = []  # vector of region holes
        self.holesOrients = []
        self.isDeleted = False
        self.face = None

    def __del__(self):
        if self.mesh:
            del self.mesh

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
    
    def delMesh(self):
        self.mesh = None

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

    # ---------------------------------------------------------------------
    # Retorna a estrutura de loops (número de subdivisões por segmento)
    # Necessário para validar se é Bilinear (4 lados) ou Trilinear (3 lados)
    def getMeshLoops(self):
        segSbdvs = []
        for seg in self.segments:
            segSbdvs.append(seg.getNumberSdv())
        
        # Retorna uma lista contendo a lista de subdivisões do loop externo
        # (Suporte a múltiplos loops/buracos poderia ser adicionado aqui)
        return [segSbdvs]

    # ---------------------------------------------------------------------
    # Retorna todos os pontos da fronteira discretizados para a geração da malha
    def getMeshBdryPoints(self):
        bdryPts = []
        for i, seg in enumerate(self.segments):
            orient = self.segmentOrients[i]
            sdvPts = seg.getSdvPoints()
            if not sdvPts or len(sdvPts) < 2:
                p0 = seg.getPntInit(); p1 = seg.getPntEnd()
                sdvPts = [Pnt2D(p0.getX(), p0.getY()), Pnt2D(p1.getX(), p1.getY())]

            # n subdivisões => n+1 pontos; usamos só os primeiros n
            if orient:
                # ordem direta sem o último
                for k in range(0, len(sdvPts) - 1):
                    bdryPts.append(sdvPts[k])
            else:
                # ordem reversa sem o último (que seria o primeiro no sentido invertido)
                for k in range(len(sdvPts) - 1, 0, -1):
                    bdryPts.append(sdvPts[k])

        # Resultado: para triângulo: 3 * n pontos (sem duplicar vértices)
        return bdryPts