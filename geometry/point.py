from compgeom.pnt2d import Pnt2D


class Point(Pnt2D):

    def __init__(self, _x=None, _y=None):
        super(Pnt2D, self).__init__(_x, _y)
        self.selected = False
        self.vertex = None
        self.attributes = []

    def setSelected(self, _select):
        self.selected = _select

    def isSelected(self):
        return self.selected
