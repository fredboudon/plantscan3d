
import openalea.vpltk.qt
from openalea.vpltk.qt.QtCore import *
from openalea.vpltk.qt.QtGui import *

import os
import compile_ui as cui
ldir    = os.path.dirname(__file__)
cui.check_ui_generation(os.path.join(ldir, 'editor.ui'))

import editor_ui

class MTGEditor(QMainWindow, editor_ui.Ui_MainWindow) :
    def __init__(self, parent=None):
        """
        @param parent : parent window
        """
        QMainWindow.__init__(self, parent)
        editor_ui.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pointSizeSlider.setValue(self.mtgeditor.pointWidth)
        self.nodeSizeSlider.setValue(self.mtgeditor.nodeWidth)
        QObject.connect(self.actionOpenMTG, SIGNAL('triggered(bool)'),self.mtgeditor.openMTG)
        QObject.connect(self.actionSaveMTG, SIGNAL('triggered(bool)'),self.mtgeditor.saveMTG)
        QObject.connect(self.actionSave, SIGNAL('triggered(bool)'),self.mtgeditor.save)
        QObject.connect(self.actionSaveSnapshot, SIGNAL('triggered(bool)'),self.mtgeditor.saveSnapshot)
        QObject.connect(self.actionImportPoints, SIGNAL('triggered(bool)'),self.mtgeditor.importPoints)
        QObject.connect(self.actionImportContractedPoints, SIGNAL('triggered(bool)'),self.mtgeditor.importContractedPoints)
        QObject.connect(self.actionExportContractedPoints, SIGNAL('triggered(bool)'),self.mtgeditor.exportContractedPoints)
        QObject.connect(self.actionExportPoints, SIGNAL('triggered(bool)'),self.mtgeditor.exportPoints)
        self.actionViewPoints.setChecked(self.mtgeditor.isPointDisplayEnabled())
        self.actionViewContractedPoints.setChecked(self.mtgeditor.isContractedPointDisplayEnabled())
        self.actionViewMTG.setChecked(self.mtgeditor.isMTGDisplayEnabled())
        self.actionViewControlPoints.setChecked(self.mtgeditor.isControlPointsDisplayEnabled())
        self.actionView3DModel.setChecked(self.mtgeditor.is3DModelDisplayEnabled())
        QObject.connect(self.actionViewPoints, SIGNAL('triggered(bool)'),self.mtgeditor.enablePointDisplay)
        QObject.connect(self.actionViewContractedPoints, SIGNAL('triggered(bool)'),self.mtgeditor.enableContractedPointDisplay)
        QObject.connect(self.actionViewMTG, SIGNAL('triggered(bool)'),self.mtgeditor.enableMTGDisplay)
        QObject.connect(self.actionViewControlPoints, SIGNAL('triggered(bool)'),self.mtgeditor.enableControlPointsDisplay)
        QObject.connect(self.actionView3DModel, SIGNAL('triggered(bool)'),self.mtgeditor.enable3DModelDisplay)
        QObject.connect(self.actionRefreshView, SIGNAL('triggered(bool)'),self.mtgeditor.refreshView)
        QObject.connect(self.actionAdjustView, SIGNAL('triggered(bool)'),self.mtgeditor.adjustView)
        QObject.connect(self.actionContract, SIGNAL('triggered(bool)'),self.mtgeditor.contractPoints)
        QObject.connect(self.actionCreateSkeleton, SIGNAL('triggered(bool)'),self.mtgeditor.createSkeleton)
        QObject.connect(self.actionComputeRadius, SIGNAL('triggered(bool)'),self.mtgeditor.computeNodesRadius)
        QObject.connect(self.actionAverageRadius, SIGNAL('triggered(bool)'),self.mtgeditor.averageNodesRadius)
        QObject.connect(self.actionFilterRadius, SIGNAL('triggered(bool)'),self.mtgeditor.filterNodesRadius)
        QObject.connect(self.actionCheckMTG, SIGNAL('triggered(bool)'),self.mtgeditor.checkMTG)
        QObject.connect(self.actionExportGeom, SIGNAL('triggered(bool)'),self.mtgeditor.exportAsGeom)
        QObject.connect(self.actionExportNodeList, SIGNAL('triggered(bool)'),self.mtgeditor.exportNodeList)
        QObject.connect(self.visibilityEnabled, SIGNAL('clicked(bool)'),self.mtgeditor.enabledClippingPlane)
        QObject.connect(self.backVisibilitySlider, SIGNAL('valueChanged(int)'),self.mtgeditor.setBackVisibility)
        QObject.connect(self.frontVisibilitySlider, SIGNAL('valueChanged(int)'),self.mtgeditor.setFrontVisibility)
        QObject.connect(self.pointSizeSlider, SIGNAL('valueChanged(int)'),self.mtgeditor.setPointWidth)
        QObject.connect(self.nodeSizeSlider, SIGNAL('valueChanged(int)'),self.mtgeditor.setNodeWidth)
        QObject.connect(self.pointFilterSlider, SIGNAL('valueChanged(int)'),self.mtgeditor.setPointFilter)
        QObject.connect(self.actionUndo, SIGNAL('triggered(bool)'),self.mtgeditor.undo)
        QObject.connect(self.actionRedo, SIGNAL('triggered(bool)'),self.mtgeditor.redo)
        QObject.connect(self.mtgeditor, SIGNAL('undoAvailable(bool)'),self.actionUndo.setEnabled)
        QObject.connect(self.mtgeditor, SIGNAL('redoAvailable(bool)'),self.actionRedo.setEnabled)
        QObject.connect(self.actionPuu1, SIGNAL('triggered(bool)'),self.mtgeditor.puu1)
        QObject.connect(self.actionPuu3, SIGNAL('triggered(bool)'),self.mtgeditor.puu3)
        QObject.connect(self.actionCherry, SIGNAL('triggered(bool)'),self.mtgeditor.cherry)
        QObject.connect(self.actionArabido, SIGNAL('triggered(bool)'),self.mtgeditor.arabido)
        QObject.connect(self.actionRevolveAroundScene, SIGNAL('triggered(bool)'),self.mtgeditor.revolveAroundScene)
        QObject.connect(self.actionShowAll, SIGNAL('triggered(bool)'),self.mtgeditor.showEntireScene)
        QObject.connect(self.actionReorient, SIGNAL('triggered(bool)'),self.mtgeditor.reorient)
        QObject.connect(self.actionRootBottom, SIGNAL('triggered(bool)'),self.mtgeditor.addBottomRoot)
        QObject.connect(self.actionRootTop, SIGNAL('triggered(bool)'),self.mtgeditor.addTopRoot)
        QObject.connect(self.actionXuReconstruction, SIGNAL('triggered(bool)'),self.mtgeditor.xuReconstruction)
        QObject.connect(self.actionSubSampling, SIGNAL('triggered(bool)'),self.mtgeditor.subSampling)
        QObject.connect(self.actionEuclidianContraction, SIGNAL('triggered(bool)'),self.mtgeditor.euclidianContraction)
        QObject.connect(self.actionRiemannianContraction, SIGNAL('triggered(bool)'),self.mtgeditor.riemannianContraction)
        QObject.connect(self.actionAngleEstimation, SIGNAL('triggered(bool)'),self.mtgeditor.angleEstimate)
        QObject.connect(self.actionEditScale, SIGNAL('triggered(bool)'),self.mtgeditor.tagScale)
        QObject.connect(self.actionCommitScale, SIGNAL('triggered(bool)'),self.mtgeditor.commitScale)
        QObject.connect(self.actionTagProperty, SIGNAL('triggered(bool)'),self.mtgeditor.startTagProperty)
        self.mtgeditor.actionEditScale = self.actionEditScale
        self.mtgeditor.actionTagProperty = self.actionTagProperty
        self.actionEditScale.setCheckable(True)
        self.actionTagProperty.setCheckable(True)
        
        self.mtgeditor.mainwindow = self
        
        self.mtgeditor.statusBar = QStatusBar(self)
        self.setStatusBar(self.mtgeditor.statusBar)
        self.setWindowTitle('PlantScan3D')

        
def main():
    #os.chdir(r'D:\Fred\Mes Documents\Develop\vplants\mbranches\pointreconstruction\data\pointset')
    qapp = QApplication([])
    #qapp.processEvents()
    w = MTGEditor()
    w.show()
    qapp.exec_()

if __name__ == '__main__':
    main()
