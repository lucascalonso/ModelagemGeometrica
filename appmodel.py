import os
import sys

_pkg_path = os.path.normpath(os.path.join(os.path.dirname(__file__), 'HETool', 'src'))
if _pkg_path not in sys.path:
    sys.path.insert(0, _pkg_path)

from hetool.he.hemodel import HeModel
from hetool.he.hecontroller import HeController
from hetool.he.heview import HeView

class AppModel:
    def __init__(self):
        self.he_model = HeModel()
        self.he_view = HeView(self.he_model)
        self.he_controller = HeController(self.he_model)
        self.currTol = 0.01

    def getHeController(self):
        return self.he_controller

    def getHeView(self):
        return self.he_view

    def getHeModel(self):
        return self.he_model