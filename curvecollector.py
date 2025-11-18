from compgeom.pnt2d import Pnt2D
from geometry.curves.line import Line
from geometry.curves.polyline import Polyline
from geometry.curves.quadbezier import QuadBezier
from geometry.curves.cubicbezier import CubicBezier
from geometry.curves.circle import Circle
from geometry.curves.circlearc import CircleArc
import math


class CurveCollector:
    def __init__(self, _model=[]):
        self.model = _model
        self.curve = None
        self.prevPt = None
        self.tempPt = None
        self.curveType = None  # LINE, POLYLINE...

    # ---------------------------------------------------------------------
    def setModel(self, _model):
        self.model = _model

    # ---------------------------------------------------------------------
    def getModel(self):
        return self.model

    # ---------------------------------------------------------------------
    def setCurveType(self, _type):
        self.curveType = _type

    # ---------------------------------------------------------------------
    def getCurveType(self):
        return self.curveType

    # ---------------------------------------------------------------------
    def startCollection(self):
        # Sempre reinicia estado volátil ao iniciar uma nova coleta
        if self.curve is not None:
            self.curve = None
        self.prevPt = None
        self.tempPt = None

        if self.curveType == 'LINE':
            self.curve = Line()
        elif self.curveType == 'POLYLINE':
            self.curve = Polyline()
        elif self.curveType == 'QUADBEZIER':
            self.curve = QuadBezier()
        elif self.curveType == 'CUBICBEZIER':
            self.curve = CubicBezier()
        elif self.curveType == 'CIRCLE':
            self.curve = Circle()
        elif self.curveType == 'CIRCLEARC':
            self.curve = CircleArc()

    # ---------------------------------------------------------------------
    def _commit_curve(self, _tol):
        # Insere no modelo usando o mesmo “átomo” que o Trab4 já desenha: segmento (Polyline de 2 pontos)
        if self.curve is None or self.model is None:
            return

        # Curvas finitas não-lineares: gerar segmentos
        if isinstance(self.curve, (QuadBezier, CubicBezier, Circle, CircleArc)):
            try:
                pts = self.curve.getEquivPolyline()
            except Exception:
                pts = []

            if not pts or len(pts) < 2:
                return

            # Insere cada aresta consecutiva como uma Polyline de 2 pontos (mesmo caminho de LINE/POLYLINE)
            for i in range(len(pts) - 1):
                p0, p1 = pts[i], pts[i + 1]
                seg = Polyline()
                try:
                    seg.addCtrlPoint(p0.getX(), p0.getY())
                    seg.addCtrlPoint(p1.getX(), p1.getY())
                except Exception:
                    continue

                try:
                    self.model.insertCurve(seg, _tol)
                except Exception:
                    try:
                        self.model.addCurve(seg)
                    except Exception:
                        pass
            return

        # LINE e POLYLINE: mantém comportamento original (o modelo já sabe desenhar)
        try:
            self.model.insertCurve(self.curve, _tol)
            return
        except Exception:
            pass

        try:
            self.model.addCurve(self.curve)
            return
        except Exception:
            pass

    # ---------------------------------------------------------------------
    def endCollection(self, _tol):
        # Insere no modelo e SEMPRE limpa o estado no final
        if self.curve is None:
            self.prevPt = None
            self.tempPt = None
            return
        try:
            self._commit_curve(_tol)
        finally:
            self.curve = None
            self.prevPt = None
            self.tempPt = None

    # ---------------------------------------------------------------------
    def isActive(self):
        return self.curve is not None

    # ---------------------------------------------------------------------
    def isCollecting(self):
        if self.curve is None:
            return False
        try:
            return self.curve.getNumberOfCtrlPoints() > 0
        except Exception:
            try:
                return len(self.curve.getCtrlPoints()) > 0
            except Exception:
                return False

    # ---------------------------------------------------------------------
    def hasFinished(self):
        if self.curve is not None:
            if self.curve.isPossible():
                return True
        return False

    # ---------------------------------------------------------------------
    def isUnlimited(self):
        if self.curve is not None:
            if self.curve.isUnlimited():
                return True
        return False

    # ---------------------------------------------------------------------
    def insertCtrlPoint(self, _x, _y, _tol):
        # evita ponto repetido (snap)
        if self.isCollecting() and self.prevPt is not None:
            if ((abs(_x - self.prevPt.getX()) <= _tol) and
               (abs(_y - self.prevPt.getY()) <= _tol)):
                return 0

        # robusto a curvas cujo addCtrlPoint não retorna bool
        prev_n = 0
        try:
            prev_n = len(self.curve.getCtrlPoints())
        except Exception:
            prev_n = 0

        try:
            self.curve.addCtrlPoint(_x, _y)
        except Exception:
            return 0

        try:
            new_n = len(self.curve.getCtrlPoints())
        except Exception:
            new_n = prev_n

        added = (new_n > prev_n)
        if not added:
            # não adicionou (limite atingido, etc.)
            return 0

        # atualiza estado de preview
        if self.prevPt is None:
            self.prevPt = Pnt2D(_x, _y)
        else:
            self.prevPt.setCoords(_x, _y)
        self.tempPt = None

        # NÃO auto-finaliza aqui; GLCanvas chama endCollection quando hasFinished()
        return 1

    # ---------------------------------------------------------------------
    def addTempCtrlPoint(self, _x, _y):
        if self.tempPt is None:
            self.tempPt = Pnt2D(_x, _y)
        else:
            self.tempPt.setCoords(_x, _y)
        return 1

    # ---------------------------------------------------------------------
    def getCurveCollected(self):
        return self.curve

    # ---------------------------------------------------------------------
    def getDrawPoints(self):
        if self.curve is None:
            return []
        if self.tempPt is None:
            return []
        return self.curve.getEquivPolylineCollecting(self.tempPt)

    # ---------------------------------------------------------------------
    def getCtrlPoints(self):
        if self.curve is None:
            ctrlPts = []
        else:
            ctrlPts = self.curve.getCtrlPoints()
        if ctrlPts == []:
            pts = []
        else:
            pts = ctrlPts.copy()
        if self.tempPt is not None:
            pts.append(self.tempPt)
        return pts

    # ---------------------------------------------------------------------
    def getBoundBox(self):
        if self.curve is None:
            return
        return self.curve.getBoundBox()

    # ---------------------------------------------------------------------
    def reset(self):
        # Cancela a coleta atual e limpa estado
        self.curve = None
        self.prevPt = None
        self.tempPt = None

    # ---------------------------------------------------------------------
    def kill(self):
        if self.curve is not None:
            del self.curve
        del self

    # ---------------------------------------------------------------------
    def snapToCurrentCurve(self, _x, _y, _tol):
        if self.curve is None:
            return False, _x, _y

        if not self.curve.isUnlimited():
            return False, _x, _y

        pts = self.curve.getCtrlPoints()
        if len(pts) < 3:
            return False, _x, _y

        snap = False
        dmin = _tol
        for i in range(0, len(pts)):
            pt_x = pts[i].getX()
            pt_y = pts[i].getY()
            d = math.sqrt((_x - pt_x) * (_x - pt_x) +
                          (_y - pt_y) * (_y - pt_y))

            if d < dmin:
                xmin = pt_x
                ymin = pt_y
                dmin = d
                snap = True

        if snap:
            return True, xmin, ymin
        else:
            return False, _x, _y