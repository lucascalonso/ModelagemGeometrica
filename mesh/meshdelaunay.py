from mesh.meshgenerator import MeshGenerator
from hetool.geometry.point import Point
from hetool.compgeom.tesselation import Tesselation
import triangle as tr
import math

class MeshDelaunay(MeshGenerator):

    def __init__(self):
        self.loops = []

    # ---------------------------------------------------------------------
    @staticmethod
    def pickLoop(loopPts, _pt, _tol):
        return False

    # ---------------------------------------------------------------------
    def setLoops(self, _loops):
        if not _loops:
            return False
        self.loops = []
        if isinstance(_loops[0], list):
            for loop_segments in _loops:
                total_pts = sum(loop_segments)
                self.loops.append(total_pts)
        else:
            total_pts = sum(_loops)
            self.loops.append(total_pts)
        return True

    # ---------------------------------------------------------------------
    def generateMesh(self, _bdryPnts):
        if not self.loops:
            return False, [], []

        vertices = []
        for pt in _bdryPnts:
            vertices.append([pt.getX(), pt.getY()])

        segments = []
        holes = []
        current_idx = 0

        for i, loop_size in enumerate(self.loops):
            # Conecta os pontos do loop sequencialmente
            for j in range(loop_size):
                u = current_idx + j
                v = current_idx + (j + 1) % loop_size
                segments.append([u, v])

            # Se for um loop interno (i > 0), calcula ponto interno para marcar como buraco
            if i > 0:
                loop_pts = _bdryPnts[current_idx : current_idx + loop_size]
                hole_pt = self._get_point_inside(loop_pts)
                if hole_pt:
                    holes.append([hole_pt.getX(), hole_pt.getY()])
                else:
                    # Fallback de segurança: centróide simples
                    cx = sum(p.getX() for p in loop_pts) / len(loop_pts)
                    cy = sum(p.getY() for p in loop_pts) / len(loop_pts)
                    holes.append([cx, cy])

            current_idx += loop_size

        data = dict(vertices=vertices, segments=segments)
        if holes:
            data['holes'] = holes

        # Calcula restrição de área
        max_seg_len_sq = 0.0
        current_idx = 0
        for loop_size in self.loops:
            for j in range(loop_size):
                p1 = _bdryPnts[current_idx + j]
                p2 = _bdryPnts[current_idx + (j + 1) % loop_size]
                d2 = (p1.getX() - p2.getX())**2 + (p1.getY() - p2.getY())**2
                if d2 > max_seg_len_sq:
                    max_seg_len_sq = d2
            current_idx += loop_size
        
        max_area = (math.sqrt(3) / 4.0) * max_seg_len_sq
        opts = f'pqa{max_area:.6f}'

        try:
            output = tr.triangulate(data, opts)
        except Exception:
            return False, [], []

        if 'triangles' not in output:
            return False, [], []

        out_pts = []
        for v in output['vertices']:
            out_pts.append(Point(v[0], v[1]))

        out_conn = output['triangles'].tolist()

        return True, out_pts, out_conn

    def _get_point_inside(self, pts):
        """
        Usa Tesselation para encontrar ponto interno.
        Converte explicitamente para lista de coordenadas [x,y,z] para evitar erros no wrapper.
        """
        try:
            # Converte Point objects para lista de coordenadas puras
            # Tesselation espera lista de listas ou tuplas
            coords = [[p.getX(), p.getY(), 0.0] for p in pts]
            
            tess = Tesselation()
            tess.addContour(coords) 
            
            # Retorna lista plana de Points [p1, p2, p3, ...] formando triângulos
            tri_verts = tess.tesselate()
            
            if tri_verts and len(tri_verts) >= 3:
                # Pega o primeiro triângulo gerado pela tesselação
                p1 = tri_verts[0]
                p2 = tri_verts[1]
                p3 = tri_verts[2]
                
                # O centróide de qualquer triângulo da tesselação é garantidamente interno ao polígono
                cx = (p1.getX() + p2.getX() + p3.getX()) / 3.0
                cy = (p1.getY() + p2.getY() + p3.getY()) / 3.0
                return Point(cx, cy)
                
        except Exception as e:
            print(f"Erro Tesselation: {e}")
            
        return None