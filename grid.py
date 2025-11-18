
class Grid:

    def __init__(self):
        self.isTurnedOn = False
        self.gridX = 1.00
        self.gridY = 1.00
        self.isSnapOn = False

    def reset(self):
        self.isTurnedOn = False
        self.gridX = 1.00
        self.gridY = 1.00
        self.isSnapOn = False

    def setDisplayInfo(self, _isTurnedOn):
        self.isTurnedOn = _isTurnedOn

    def getDisplayInfo(self):
        return self.isTurnedOn

    def setGridSpace(self, _dX, _dY):
        self.gridX = _dX
        self.gridY = _dY

    def getGridSpace(self):
        return self.gridX, self.gridY

    def setSnapInfo(self, _isSnapOn):
        self.isSnapOn = _isSnapOn

    def getSnapInfo(self):
        return self.isSnapOn

    def snapTo(self, _x, _y):
        fp = _x / self.gridX
        ip = int(fp)
        fp = fp - ip
        if fp > 0.5:
            _x = (ip + 1.0) * self.gridX
        elif fp < -0.5:
            _x = (ip - 1.0) * self.gridX
        else:
            _x = ip * self.gridX

        fp = _y / self.gridY
        ip = int(fp)
        fp = fp - ip

        if fp > 0.5:
            _y = (ip + 1.0) * self.gridY
        elif fp < -0.5:
            _y = (ip - 1.0) * self.gridY
        else:
            _y = ip * self.gridY
        return _x, _y
