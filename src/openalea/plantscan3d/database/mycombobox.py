try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

if not py2exe_release:
    import openalea.plantgl.gui.qt
    from openalea.plantgl.gui.qt.QtCore import *
    from openalea.plantgl.gui.qt.QtGui import *

else:
    import sip

    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)

    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtWidgets import *

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
