try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print 'Py2ExeRelease'
except ImportError:
    py2exe_release = False
    print 'StdRelease'

if not py2exe_release:
    import openalea.vpltk.qt
    from openalea.vpltk.qt.QtCore import *
    from openalea.vpltk.qt.QtGui import *

else:
    import sip

    sip.setapi('QString', 2)
    sip.setapi('QVariant', 2)

    from PyQt4.QtCore import *
    from PyQt4.QtGui import *

import os

if not py2exe_release:
    import openalea.plantscan3d.compileUi as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'db_connection.ui'))

import db_connection_ui


class DatabaseConnection(QDialog, db_connection_ui.Ui_Dialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        db_connection_ui.Ui_Dialog.__init__(self)
        self.setupUi(self)
