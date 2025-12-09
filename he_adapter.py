import os
import sys

_pkg_path = os.path.normpath(os.path.join(os.path.dirname(__file__), 'HETool', 'src'))
if _pkg_path not in sys.path:
    sys.path.insert(0, _pkg_path)

from hetool.include.hetool import Hetool


class HetoolAdapter:

    @staticmethod
    def reset():
        return Hetool.resetDataStructure()

    @staticmethod
    def insert_point(x, y, tol=1e-3):
        return Hetool.insertPoint([x, y], tol)

    @staticmethod
    def insert_segment_coords(coords, tol=1e-3):
        return Hetool.insertSegment(coords, tol)

    @staticmethod
    def insert_segment_from_curve(curve, tol=1e-3):
        # tenta extrair uma lista de pontos da curve (compatível com o modelador atual)
        coords = []
        if hasattr(curve, 'getEquivPolyline'):
            pts = curve.getEquivPolyline()
            for p in pts:
                coords.extend([p.getX(), p.getY()])
        elif hasattr(curve, 'getPoints'):
            for p in curve.getPoints():
                coords.extend([p.getX(), p.getY()])
        else:
            raise ValueError("Curve não possui pontos convertíveis para polilinha")
        return Hetool.insertSegment(coords, tol)

    @staticmethod
    def get_points():
        return Hetool.getPoints()

    @staticmethod
    def get_segments():
        return Hetool.getSegments()

    @staticmethod
    def get_patches():
        return Hetool.getPatches()

    @staticmethod
    def select_pick(x, y, tol=1e-3, shift=False):
        return Hetool.selectPick(x, y, tol, shift)

    @staticmethod
    def select_fence(xmin, xmax, ymin, ymax, shift=False):
        return Hetool.selectFence(xmin, xmax, ymin, ymax, shift)

    @staticmethod
    def create_patch(segments=None):
        # ESTRATÉGIA ROBUSTA:
        # O HETool.createPatch() opera sobre patches (faces) SELECIONADOS.
        # Em vez de depender da seleção de segmentos (que pode falhar),
        # vamos iterar sobre TODOS os patches do modelo.
        # Se encontrarmos um patch que é um "buraco" (isDeleted=True) e não é a face infinita,
        # nós o selecionamos para preenchimento.
        
        patches_to_select = []
        all_patches = Hetool.getPatches()
        
        if all_patches:
            # O índice 0 geralmente é a Face Infinita (Universo), que não deve ser preenchida.
            # Verificamos todos os outros.
            for i in range(1, len(all_patches)):
                patch = all_patches[i]
                # Se isDeleted for True, significa que é um ciclo fechado vazio (um buraco).
                # É exatamente isso que queremos transformar em Patch.
                if patch.isDeleted:
                    patches_to_select.append(patch)

        # Se não encontrou buracos candidatos, não há nada para fechar.
        if not patches_to_select:
            return False

        # Seleciona os buracos encontrados
        for p in patches_to_select:
            p.setSelected(True)

        # Chama o comando da biblioteca (agora com alvo certo)
        result = Hetool.createPatch()
        
        # Limpa a seleção para não deixar artefatos visuais
        for p in patches_to_select:
            p.setSelected(False)
            
        return result

    @staticmethod
    def delete_selected():
        return Hetool.delSelectedEntities()

    @staticmethod
    def set_number_of_subdivisions(n, r=1):
        return Hetool.setNumberOfSubdivisions(n, r)

    @staticmethod
    def save_file(path):
        return Hetool.saveFile(path)

    @staticmethod
    def open_file(path):
        return Hetool.openFile(path)

    @staticmethod
    def snap_to_point(x, y, tol):
        return Hetool.snapToPoint(x, y, tol)

    @staticmethod
    def snap_to_segment(x, y, tol):
        return Hetool.snapToSegment(x, y, tol)
    
    @staticmethod
    def insert_segment(x1, y1, x2, y2, tol=1e-3):
        return Hetool.insertSegment([x1, y1, x2, y2], tol)
    
    @staticmethod
    def tessellate(patch):
        return Hetool.tessellate(patch)