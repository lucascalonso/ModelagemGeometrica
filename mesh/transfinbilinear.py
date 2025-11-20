from mesh.meshgenerator import MeshGenerator
from compgeom.pnt2d import Pnt2D


class TransfinBilinear(MeshGenerator):

    def __init__(self):
        self.nu = 0
        self.nv = 0

    # ---------------------------------------------------------------------
    # Auxiliary method for indexing a matrix with size = (nu+1,*)
    # stored in row major order in a vector.
    def mtxIdsToVecId(self, _i, _j):
        return _i * (self.nu + 1) + _j

    # ---------------------------------------------------------------------
    def setLoops(self, _loops):
        self.nu = 0
        self.nv = 0

        # Check for just one loop
        if len(_loops) != 1:
            return False

        # Check for exactly four segments on loop
        segSbdvs = _loops[0]
        if len(segSbdvs) != 4:
            return False

        # Check for equal number of subdivisions on opposite segments of loop
        if segSbdvs[0] != segSbdvs[2]:
            return False
        if segSbdvs[1] != segSbdvs[3]:
            return False

        # Save parameters of valid boundary loop
        self.nu = segSbdvs[0]
        self.nv = segSbdvs[1]

        return True

    # ---------------------------------------------------------------------
    def generateMesh(self, _bdryPnts):
        pts = []
        conn = []
        # Total number of boundary nodes must be consistent with
        # number of boundary segments
        if len(_bdryPnts) != (self.nu + self.nv) * 2:
            return False, pts, conn

        # Allocate point vector in row major order
        pt = Pnt2D(0.0, 0.0)
        for i in range(0, self.nv + 1):
            for j in range(0, self.nu + 1):
                pts.append(pt)

        # Input nodes from first boundary curve
        idBound = 0
        i = 0
        for j in range(0, self.nu):
            k = self.mtxIdsToVecId(i, j)
            pts[k] = _bdryPnts[idBound]
            idBound += 1

        # Input node from second boundary curve
        j = self.nu
        for i in range(0, self.nv):
            # *** COMPLETE HERE - TRANSFINBILINEAR: 01 ***
            k = self.mtxIdsToVecId(i, j)
            pts[k] = _bdryPnts[idBound]
            idBound += 1
        # Input node from third boundary curve
        # *** COMPLETE HERE - TRANSFINBILINEAR: 02 ***
        i = self.nv
        for j in range(self.nu, 0, -1):
            k = self.mtxIdsToVecId(i, j)
            pts[k] = _bdryPnts[idBound]
            idBound += 1
        # Input node from fourth boundary curve
        # *** COMPLETE HERE - TRANSFINBILINEAR: 03 ***
        j = 0
        for i in range(self.nv, 0, -1):
            k = self.mtxIdsToVecId(i, j)
            pts[k] = _bdryPnts[idBound]
            idBound += 1
        # Generate interior nodes
        # *** COMPLETE HERE - TRANSFINBILINEAR: 04 ***
        k_0_0 = self.mtxIdsToVecId(0, 0)
        k_0_nu = self.mtxIdsToVecId(0, self.nu)
        k_nv_0 = self.mtxIdsToVecId(self.nv, 0)
        k_nv_nu = self.mtxIdsToVecId(self.nv, self.nu)

        for i in range(1, self.nv):
            k_i_0 = self.mtxIdsToVecId(i, 0)
            k_i_nu = self.mtxIdsToVecId(i, self.nu)
            
            v = float(i) / self.nv
            
            for j in range(1, self.nu):
                k_0_j = self.mtxIdsToVecId(0, j)
                k_nv_j = self.mtxIdsToVecId(self.nv, j)
                
                u = float(j) / self.nu
                
                k = self.mtxIdsToVecId(i, j)
                
                # Bilinear Transfinite Interpolation Formula
                pts[k] = (pts[k_0_j] * (1.0 - v) + pts[k_nv_j] * v +
                          pts[k_i_0] * (1.0 - u) + pts[k_i_nu] * u -
                          (pts[k_0_0] * (1.0 - u) * (1.0 - v) +
                           pts[k_0_nu] * u * (1.0 - v) +
                           pts[k_nv_0] * (1.0 - u) * v +
                           pts[k_nv_nu] * u * v))
                
        # Generate quadrilateral elements
        # *** COMPLETE HERE - TRANSFINBILINEAR: 05 ***
        for i in range(0, self.nv):
            for j in range(0, self.nu):
                n0 = self.mtxIdsToVecId(i, j)
                n1 = self.mtxIdsToVecId(i, j + 1)
                n2 = self.mtxIdsToVecId(i + 1, j + 1)
                n3 = self.mtxIdsToVecId(i + 1, j)
                conn.append([n0, n1, n2, n3])

        return True, pts, conn
