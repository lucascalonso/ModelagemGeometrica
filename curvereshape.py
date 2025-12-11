class CurveReshape:
    def __init__(self, _model=[]):
        self.model = _model
        self.curve = None
        self.ctrlPtId = -1

    # ---------------------------------------------------------------------
    def setModel(self, _model):
        self.model = _model

    # ---------------------------------------------------------------------
    def getModel(self):
        return self.model

    # ---------------------------------------------------------------------
    def startReshape(self, _curve):
        self.curve = _curve

    # ---------------------------------------------------------------------
    def isReshaping(self):
        if self.curve is not None:
            return True
        return False

    # ---------------------------------------------------------------------
    def setCtrlPointId(self, _id):
        if self.curve is None:
            return False
        nCtrlPts = self.curve.getNumberOfReshapeCtrlPoints()
        if nCtrlPts < 2:
            return False
        if _id < 0:
            return False
        if _id >= nCtrlPts:
            return False
        self.ctrlPtId = _id
        return True
    # ---------------------------------------------------------------------
    def changeCtrlPoint(self, _x, _y, _tol):
        if self.ctrlPtId == -1:
            return False
        if self.curve.setCtrlPoint(self.ctrlPtId, _x, _y, _tol):
            self.model.reshapeCurve(self.curve, _tol)
            return True
        return False

    # ---------------------------------------------------------------------
    def reset(self):
        self.curve = None
        self.ctrlPtId = -1
