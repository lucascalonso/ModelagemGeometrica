from mesh.meshgenerator import MeshGenerator
from compgeom.pnt2d import Pnt2D
from compgeom.compgeom import CompGeom
import triangle as tr
import math


# This class generates meshes by the method of constrained Delaunay triangulation.
# It uses Jonathan Richard Shewchuk’s Triangle - "A Two-Dimensional Quality Mesh
# Generator and Delaunay Triangulator" (http://www.cs.cmu.edu/~quake/triangle.html).
# Copyright: Jonathan Richard Shewchuk (http://people.eecs.berkeley.edu/~jrs/).
# Triangle is implemented in C and this class uses a Python wrapper 
# (https://rufat.be/triangle) around the C implementation developed by The Block
# Research Group (BRG) at the Institute of Technology in Architecture at
# ETH Zürich (https://block.arch.ethz.ch/brg/about).
#
# This use of Triangle is limited to one region with only an external loop
# (no holes).
#
# Triangle generates Delaunay triangulations constrained to the given list of
# loop points. However, to make Triangle's use more robust, the only specified
# parameter is a maximum triangle area constraint, which is calculated as the
# area of an equilateral triangle whose side is equal to the maximum segment
# size of the input loop. Since this is the only parameter specified for
# Triangle, in the case of concave regions, it generates triangles outside the
# given loop and inside its convex hull. Therefore, these external triangles
# and their vertices' points are deleted in the post-processing stage.
#
# In addition, Triangle may generate new triangulation points on the
# external loop. No fix is made for this.
#
# Installation: pip install triangle
#

class MeshDelaunay(MeshGenerator):

    def __init__(self):
        pass

    # ---------------------------------------------------------------------
    @staticmethod
    def pickLoop(loopPts, _pt, _tol):
        nLoopPts = len(loopPts)
        for i in range(0, nLoopPts):
            if CompGeom.pickLine(loopPts[i], loopPts[(i + 1)%nLoopPts], _pt, _tol):
                return True
        return False

    # ---------------------------------------------------------------------
    def setLoops(self, _loops):

        # Check for just one loop
        if len(_loops) != 1:
            return False

        return True

    # ---------------------------------------------------------------------
    def generateMesh(self, _bdryPnts):

        # Fecha loop para testes ponto‑no‑polígono (sem repetir para Triangle)
        polyLoop = _bdryPnts
        if polyLoop[0].getX() != polyLoop[-1].getX() or polyLoop[0].getY() != polyLoop[-1].getY():
            closedLoop = polyLoop + [Pnt2D(polyLoop[0].getX(), polyLoop[0].getY())]
        else:
            closedLoop = polyLoop

        inputPts = [[p.getX(), p.getY()] for p in polyLoop]
        nBdryPts = len(polyLoop)
        if nBdryPts < 3:
            return False, [], []

        segments = [[i, (i + 1) % nBdryPts] for i in range(nBdryPts)]

        maxL = 0.0
        for i in range(nBdryPts):
            a = polyLoop[i]
            b = polyLoop[(i + 1) % nBdryPts]
            sizeL = Pnt2D.euclidiandistance(a, b)
            if sizeL > maxL:
                maxL = sizeL
        maxArea = maxL * maxL * math.sqrt(3.0) / 4.0

        opts = f"pqaz{maxArea}"
        tri_in = {'vertices': inputPts, 'segments': segments}
        t = tr.triangulate(tri_in, opts)

        if 'triangles' not in t or len(t['triangles']) == 0:
            return False, [], []

        ptsRaw = t['vertices'].tolist()
        connRaw = t['triangles'].tolist()

        # Função robusta ponto-no-polígono (ray casting)
        def pointInPoly(pt: Pnt2D, loop):
            x = pt.getX()
            y = pt.getY()
            inside = False
            for i in range(len(loop) - 1):
                x1 = loop[i].getX(); y1 = loop[i].getY()
                x2 = loop[i + 1].getX(); y2 = loop[i + 1].getY()
                # checa interseção com aresta
                cond = ((y1 > y) != (y2 > y))
                if cond:
                    xinters = (x2 - x1) * (y - y1) / (y2 - y1 + 1e-30) + x1
                    if xinters >= x:
                        inside = not inside
            return inside

        # Mantém todos os pontos (Triangle já respeitou segmentos); não filtra agora
        pts = [Pnt2D(x, y) for (x, y) in ptsRaw]
        newPtIds = list(range(len(pts)))

        # Filtra triângulos usando centróide dentro do polígono ou sobre a borda
        tol = maxL * 1e-3
        def onBoundary(pt):
            return MeshDelaunay.pickLoop(polyLoop, pt, tol)

        conn = []
        for tri in connRaw:
            i0, i1, i2 = tri
            p0 = pts[i0]; p1 = pts[i1]; p2 = pts[i2]
            cx = (p0.getX() + p1.getX() + p2.getX()) / 3.0
            cy = (p0.getY() + p1.getY() + p2.getY()) / 3.0
            cpt = Pnt2D(cx, cy)
            if pointInPoly(cpt, closedLoop) or onBoundary(cpt):
                conn.append([newPtIds[i0], newPtIds[i1], newPtIds[i2]])

        if len(conn) == 0:
            # Fallback: aceita todos (já são internos em maioria dos casos)
            conn = [[newPtIds[i0], newPtIds[i1], newPtIds[i2]] for (i0, i1, i2) in connRaw]

        # Força orientação consistente com primeiro triângulo do loop
        def area2(a, b, c):
            return (b.getX() - a.getX()) * (c.getY() - a.getY()) - \
                   (b.getY() - a.getY()) * (c.getX() - a.getX())

        # domínio: usa três pontos do contorno (não colineares)
        domA = polyLoop[0]; domB = polyLoop[1]; domC = polyLoop[2]
        dom_sign = 1 if area2(domA, domB, domC) >= 0 else -1

        fixed = []
        seen = set()
        EPS = 1e-14
        for tri in conn:
            p0, p1, p2 = pts[tri[0]], pts[tri[1]], pts[tri[2]]
            a = area2(p0, p1, p2)
            if abs(a) <= EPS:
                continue  # degenerate
            if dom_sign * a < 0:
                tri[1], tri[2] = tri[2], tri[1]
            key = tuple(tri)
            if key not in seen:
                seen.add(key)
                fixed.append(tri)
        conn = fixed

        return True, pts, conn
