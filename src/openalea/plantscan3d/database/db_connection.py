try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    #print('StdRelease')

from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *
from openalea.plantgl.gui.qt.QtWidgets import *

import os

if not py2exe_release:
    import openalea.plantscan3d.ui_compiler as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'db_connection.ui'))

from . import db_connection_ui


class DatabaseConnection(QDialog, db_connection_ui.Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        db_connection_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)
