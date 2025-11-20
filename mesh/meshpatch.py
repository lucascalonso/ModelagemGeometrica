from mesh.meshgenerator import MeshGenerator
from mesh.transfinbilinear import TransfinBilinear
from mesh.transfintrilinear import TransfinTrilinear
from mesh.meshdelaunay import MeshDelaunay


class MeshPatch():

    def __init__(self):
        self.isTurnedOn = False
        self.meshGenerator = None

    def setDisplayInfo(self, _isTurnedOn):
        self.isTurnedOn = _isTurnedOn

    def getDisplayInfo(self):
        return self.isTurnedOn

    def setMeshGenerator(self, _type):
        if self.meshGenerator is not None:
            del self.meshGenerator
        if _type == MeshGenerator.TRANSFIN_BILINEAR:
            self.generator = TransfinBilinear()
        elif _type == MeshGenerator.TRANSFIN_TRILINEAR:
            self.generator = TransfinTrilinear()
        elif _type == MeshGenerator.DELAUNAY_TRIANGULATION:
            self.generator = MeshDelaunay()
    
    def setLoops(self, _loops):
        if self.generator is None:
            return False
        status = self.generator.setLoops(_loops)
        if status == False:
            return False
        return True

    def generateMesh(self, _bdryPts):
        if self.generator is None:
            return False, [], []
        
        return self.generator.generateMesh(_bdryPts)
    
    """
    def setLoops(self, _loops):
        if self.generator is None:
            return False
        status = self.generator.setLoops(_loops)
        if status == False:
            return False

    def generateMesh(self, _bdryPts):
        if self.generator is None:
            return False
        status, pts, conn = self.generator.generateMesh(_bdryPts)
        if status == False:
            return False, pts, conn
        return True , pts, conn
    """