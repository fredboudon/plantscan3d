try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print('Py2ExeRelease')
except ImportError:
    py2exe_release = False
    print('StdRelease')

from openalea.plantgl.gui.qt.QtCore import *
from openalea.plantgl.gui.qt.QtGui import *

import os

if not py2exe_release:
    import src.openalea.plantscan3d.compileUi as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'segmenteditor.ui'))

from . import segmenteditor_ui


class SegmentEditor(QMainWindow, segmenteditor_ui.Ui_MainWindow):
    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        segmenteditor_ui.Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.gleditor.set_selectable_trees.connect(self.setTrees)
        self.actionExport_Points.triggered.connect(self.gleditor.exportPoints)

        self.db_instance = None

    def make_thumbnail(self):
        from .thumbnailmaker import make_thumbnail
        from openalea.plantgl.all import Scene

        if self.gleditor.tree_seleted is None:
            return

        points = self.gleditor.points.subset(self.gleditor.segmented_points[self.gleditor.tree_seleted][0])
        return make_thumbnail(Scene([points]), (256, 256))

    def set_database(self, instance):
        self.db_instance = instance
        self.db_instance.make_thumbnail = self.make_thumbnail
        self.db_instance.saveObjectRequested.connect(self.gleditor.save_request)
        self.actionExport_To_Database.setEnabled(True)
        self.actionExport_To_Database.triggered.connect(self.db_instance.insert_item)

    def tree_action_trigger(self):
        obj = self.sender()
        if hasattr(obj, 'index'):
            self.gleditor.setCurrentTrees(obj.index)

    def setTrees(self, trees):
        index = 0
        for t in trees:
            action = QAction(t, self.menuTrees)
            action.index = index
            action.triggered.connect(self.tree_action_trigger)
            self.menuTrees.addAction(action)
            index += 1
