try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *

class MyComboBox(QComboBox):
    def __init__(self, parent):
        QComboBox.__init__(self, parent)
        self.readonly = False

    def mousePressEvent(self, event):
        if not self.readonly:
            QComboBox.mousePressEvent(self, event)

    def keyPressEvent(self, event):
        if not self.readonly:
            QComboBox.keyPressEvent(self, event)

    def wheelEvent(self, event):
        if not self.readonly:
            QComboBox.wheelEvent(self, event)
