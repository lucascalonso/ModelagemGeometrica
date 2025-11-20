from mesh.meshgenerator import MeshGenerator
from compgeom.pnt2d import Pnt2D

class TransfinTrilinear(MeshGenerator):

    def __init__(self):
        self.n = 0

    # ---------------------------------------------------------------------
    # Auxiliary method for indexing a triangular matrix with size = n+1
    # stored in a vector.
    # Mapping (i, j) -> k
    # Row 0: (0,0) ... (0,n)
    # Row 1: (1,0) ... (1,n-1)
    # ...
    # Row n: (n,0)
    def mtxIdsToVecId(self, _i, _j):
        # Sum of arithmetic progression for previous rows + column index
        return int(((_i * (2 * self.n - _i + 3)) / 2) + _j)

    # ---------------------------------------------------------------------
    def setLoops(self, _loops):
        self.n = 0

        # Check for just one loop
        if len(_loops) != 1:
            return False

        # Check for exactly three curves on loop
        segSbdvs = _loops[0]
        if len(segSbdvs) != 3:
            return False

        # Check for equal number of subdivisions on all segments of loop
        if segSbdvs[0] != segSbdvs[1]:
            return False
        if segSbdvs[0] != segSbdvs[2]:
            return False

        # Save parameters of valid boundary loop
        self.n = segSbdvs[0]

        return True

    # ---------------------------------------------------------------------
    def generateMesh(self, _bdryPnts):
        if self.n < 1:
            return False, [], []

        # Total points in a triangular grid of side n is (n+1)(n+2)/2
        num_points = int((self.n + 1) * (self.n + 2) / 2)
        pts = [None] * num_points
        conn = []
        
        # Total number of boundary nodes must be consistent with
        # number of boundary segments (3 sides * n subdivisions)
        if len(_bdryPnts) != self.n * 3:
            return False, [], []

        # --- 1. Boundary Points Assignment ---
        idBound = 0

        # Side 1: Left Edge (j varies, i=0)
        # Corresponds to segment from (0,0) to (0,n)
        for j in range(0, self.n):
            k = self.mtxIdsToVecId(0, j)
            pts[k] = _bdryPnts[idBound]
            idBound += 1

        # Side 2: Hypotenuse (i varies, i+j=n)
        # Corresponds to segment from (0,n) to (n,0)
        for i in range(0, self.n):
            j = self.n - i
            k = self.mtxIdsToVecId(i, j)
            pts[k] = _bdryPnts[idBound]
            idBound += 1

        # Side 3: Bottom Edge (i varies backwards, j=0)
        # Corresponds to segment from (n,0) to (0,0)
        for i in range(self.n, 0, -1):
            k = self.mtxIdsToVecId(i, 0)
            pts[k] = _bdryPnts[idBound]
            idBound += 1

        # --- 2. Interior Points Generation ---
        # Uses a blend of 3 linear interpolations (Coons Patch for Triangle)
        for i in range(1, self.n):
            for j in range(1, self.n - i):
                k = self.mtxIdsToVecId(i, j)
                
                # Interpolation 1: Parallel to Side 1 (Left)
                # Interpolates between P(0, j) and P(n-j, j)
                den1 = self.n - j
                u1 = i / den1 if den1 != 0 else 0
                p1_start = pts[self.mtxIdsToVecId(0, j)]
                p1_end   = pts[self.mtxIdsToVecId(self.n - j, j)]
                p1 = p1_start * (1.0 - u1) + p1_end * u1

                # Interpolation 2: Parallel to Side 3 (Bottom)
                # Interpolates between P(i, 0) and P(i, n-i)
                den2 = self.n - i
                u2 = j / den2 if den2 != 0 else 0
                p2_start = pts[self.mtxIdsToVecId(i, 0)]
                p2_end   = pts[self.mtxIdsToVecId(i, self.n - i)]
                p2 = p2_start * (1.0 - u2) + p2_end * u2

                # Interpolation 3: Parallel to Side 2 (Hypotenuse)
                # Interpolates between P(0, i+j) and P(i+j, 0)
                den3 = i + j
                u3 = i / den3 if den3 != 0 else 0
                p3_start = pts[self.mtxIdsToVecId(0, i + j)]
                p3_end   = pts[self.mtxIdsToVecId(i + j, 0)]
                p3 = p3_start * (1.0 - u3) + p3_end * u3

                # Average the 3 interpolations
                pts[k] = (p1 + p2 + p3) * (1.0 / 3.0)
  
        # --- 3. Connectivity Generation ---
        # We generate triangles for both winding orders (CCW and CW) to ensure visibility
        # regardless of camera or normal orientation (Double Sided).
        conn.clear()
        # Família 1: (i,j) -> (i, j+1) -> (i+1, j)  para j = 0..(n-i-1)
        for i in range(0, self.n):
            for j in range(0, self.n - i):
                A = self.mtxIdsToVecId(i, j)
                B = self.mtxIdsToVecId(i, j + 1)
                C = self.mtxIdsToVecId(i + 1, j)
                conn.append([A, B, C])

        # Família 2: (i+1, j) -> (i+1, j+1) -> (i, j+1) para j = 0..(n-i-2)
        for i in range(0, self.n - 1):
            for j in range(0, self.n - i - 1):
                C = self.mtxIdsToVecId(i + 1, j)
                D = self.mtxIdsToVecId(i + 1, j + 1)
                B = self.mtxIdsToVecId(i, j + 1)
                conn.append([C, D, B])

        # --- 4. Força CCW e remove duplicados ---
        def area2(a, b, c):
            return (b.getX() - a.getX()) * (c.getY() - a.getY()) - \
                   (b.getY() - a.getY()) * (c.getX() - a.getX())

        # orientação do triângulo “mestre” (0,0) -> (0,n) -> (n,0)
        k00 = self.mtxIdsToVecId(0, 0)
        k0n = self.mtxIdsToVecId(0, self.n)
        kn0 = self.mtxIdsToVecId(self.n, 0)
        a_dom = area2(pts[k00], pts[k0n], pts[kn0])
        dom_sign = 1 if a_dom >= 0 else -1

        fixed = []
        seen = set()
        EPS = 1e-12
        for tri in conn:
            p0, p1, p2 = pts[tri[0]], pts[tri[1]], pts[tri[2]]
            a = area2(p0, p1, p2)
            # pula triângulos degenerados
            if abs(a) <= EPS:
                continue
            # força orientação compatível com o triângulo mestre
            if dom_sign * a < 0:
                tri[1], tri[2] = tri[2], tri[1]
            key = tuple(tri)
            if key not in seen:
                seen.add(key)
                fixed.append(tri)

        conn = fixed
        return True, pts, conn
 