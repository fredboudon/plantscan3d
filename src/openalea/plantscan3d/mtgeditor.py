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
    import compileUi as cui

    ldir = os.path.dirname(__file__)
    cui.check_ui_generation(os.path.join(ldir, 'editor.ui'))

try:
    import editor_ui
except:
    import openalea.plantscan3d.editor_ui as editor_ui


class MTGEditor(QMainWindow, editor_ui.Ui_MainWindow):
    keyPressed = pyqtSignal(int)
    keyReleased = pyqtSignal(int)

    def __init__(self, parent=None):
        """
        @param parent : parent window
        """
        QMainWindow.__init__(self, parent)
        editor_ui.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pointSizeSlider.setValue(self.mtgeditor.pointinfo.pointWidth)
        self.nodeSizeSlider.setValue(self.mtgeditor.nodeWidth)
        self.keyPressed.connect(self.mtgeditor.keyPressed)
        self.keyReleased.connect(self.mtgeditor.keyReleased)
        QObject.connect(self.actionOpenMTG, SIGNAL('triggered(bool)'), self.mtgeditor.openMTG)
        QObject.connect(self.actionImportMTG, SIGNAL('triggered(bool)'), self.mtgeditor.importMTG)  # TODO
        QObject.connect(self.actionSaveMTG, SIGNAL('triggered(bool)'), self.mtgeditor.saveMTG)
        QObject.connect(self.actionSave, SIGNAL('triggered(bool)'), self.mtgeditor.save)
        QObject.connect(self.actionSaveSnapshot, SIGNAL('triggered(bool)'), self.mtgeditor.saveSnapshot)
        QObject.connect(self.actionImportPoints, SIGNAL('triggered(bool)'), self.mtgeditor.importPoints)
        QObject.connect(self.actionExportPoints, SIGNAL('triggered(bool)'), self.mtgeditor.exportPoints)
        QObject.connect(self.actionExportGeom, SIGNAL('triggered(bool)'), self.mtgeditor.exportAsGeom)
        QObject.connect(self.actionExportNodeList, SIGNAL('triggered(bool)'), self.mtgeditor.exportNodeList)

        if not py2exe_release:
            QObject.connect(self.actionPuu1, SIGNAL('triggered(bool)'), self.mtgeditor.puu1)
            QObject.connect(self.actionPuu3, SIGNAL('triggered(bool)'), self.mtgeditor.puu3)
            QObject.connect(self.actionCherry, SIGNAL('triggered(bool)'), self.mtgeditor.cherry)
            QObject.connect(self.actionArabido, SIGNAL('triggered(bool)'), self.mtgeditor.arabido)
            QObject.connect(self.actionAppleTree, SIGNAL('triggered(bool)'), self.mtgeditor.appletree)
        else:
            self.menuFile.removeAction(self.menuLoad.menuAction())

        QObject.connect(self.actionUndo, SIGNAL('triggered(bool)'), self.mtgeditor.undo)
        QObject.connect(self.actionRedo, SIGNAL('triggered(bool)'), self.mtgeditor.redo)
        QObject.connect(self.mtgeditor, SIGNAL('undoAvailable(bool)'), self.actionUndo.setEnabled)
        QObject.connect(self.mtgeditor, SIGNAL('redoAvailable(bool)'), self.actionRedo.setEnabled)
        QObject.connect(self.actionRevolveAroundScene, SIGNAL('triggered(bool)'), self.mtgeditor.revolveAroundScene)
        QObject.connect(self.actionShowAll, SIGNAL('triggered(bool)'), self.mtgeditor.showEntireScene)

        from openalea.plantscan3d.mtgeditorwidget import WhiteTheme, BlackTheme
        QObject.connect(self.actionWhiteTheme, SIGNAL('triggered(bool)'),
                        lambda: self.mtgeditor.updateTheme(WhiteTheme))
        QObject.connect(self.actionBlackTheme, SIGNAL('triggered(bool)'),
                        lambda: self.mtgeditor.updateTheme(BlackTheme))

        QObject.connect(self.actionReorient, SIGNAL('triggered(bool)'), self.mtgeditor.reorient)
        QObject.connect(self.actionSortZ, SIGNAL('triggered(bool)'), self.mtgeditor.sortZ)
        QObject.connect(self.actionAlignGlobal, SIGNAL('triggered(bool)'), self.mtgeditor.alignGlobally)
        QObject.connect(self.actionAlignOptimizeAll, SIGNAL('triggered(bool)'), self.mtgeditor.alignOptimizeAll)
        QObject.connect(self.actionAlignOptimizeOrientation, SIGNAL('triggered(bool)'),
                        self.mtgeditor.alignOptimizeOrientation)
        QObject.connect(self.actionAlignOptimizePosition, SIGNAL('triggered(bool)'),
                        self.mtgeditor.alignOptimizePosition)
        QObject.connect(self.actionScaleAndCenter, SIGNAL('triggered(bool)'), self.mtgeditor.alignScaleAndCenter)
        QObject.connect(self.actionFilterMinDensity, SIGNAL('triggered(bool)'), self.mtgeditor.filterPointsMin)
        QObject.connect(self.actionFilterMaxDensity, SIGNAL('triggered(bool)'), self.mtgeditor.filterPointsMax)
        QObject.connect(self.actionKDensity, SIGNAL('triggered(bool)'), self.mtgeditor.pointKDensity)
        QObject.connect(self.actionRDensity, SIGNAL('triggered(bool)'), self.mtgeditor.pointRDensity)
        QObject.connect(self.actionRDensity_MT, SIGNAL('triggered(bool)'), self.mtgeditor.pointRDensityMT)
        QObject.connect(self.actionDensityHistogram, SIGNAL('triggered(bool)'), self.mtgeditor.densityHistogram)

        QObject.connect(self.actionSubSampling, SIGNAL('triggered(bool)'), self.mtgeditor.subSampling)

        QObject.connect(self.actionSoil, SIGNAL('triggered(bool)'), self.mtgeditor.selectSoil)

        QObject.connect(self.actionEuclidianContraction, SIGNAL('triggered(bool)'), self.mtgeditor.euclidianContraction)
        QObject.connect(self.actionLaplacianContraction, SIGNAL('triggered(bool)'), self.mtgeditor.laplacianContraction)
        QObject.connect(self.actionRiemannianContraction, SIGNAL('triggered(bool)'),
                        self.mtgeditor.riemannianContraction)
        QObject.connect(self.actionAdaptiveRadialContraction, SIGNAL('triggered(bool)'),
                        self.mtgeditor.adaptiveRadialContraction)
        QObject.connect(self.actionPathBasedContraction, SIGNAL('triggered(bool)'), self.mtgeditor.pathBasedContraction)
        QObject.connect(self.actionROSAContraction, SIGNAL('triggered(bool)'), self.mtgeditor.rosaContraction)

        QObject.connect(self.actionPointDirections, SIGNAL('triggered(bool)'), self.mtgeditor.pointDirections)
        QObject.connect(self.actionPointNormals, SIGNAL('triggered(bool)'), self.mtgeditor.pointNormals)
        QObject.connect(self.actionPointClusters, SIGNAL('triggered(bool)'), self.mtgeditor.pointClusters)

        self.actionViewPoints.setChecked(self.mtgeditor.isPointDisplayEnabled())
        self.actionViewPointAttributes.setChecked(self.mtgeditor.isPointAttributeDisplayEnabled())
        self.actionViewMTG.setChecked(self.mtgeditor.isMTGDisplayEnabled())
        self.actionViewControlPoints.setChecked(self.mtgeditor.isControlPointsDisplayEnabled())
        self.actionViewRadius.setChecked(self.mtgeditor.isRadiusDisplayEnabled())
        self.actionView3DModel.setChecked(self.mtgeditor.is3DModelDisplayEnabled())

        QObject.connect(self.mtgeditor, SIGNAL('PointAttributeDisplay(bool)'),
                        self.actionViewPointAttributes.setChecked)

        QObject.connect(self.actionViewPoints, SIGNAL('triggered(bool)'), self.mtgeditor.enablePointDisplay)
        QObject.connect(self.actionViewPointAttributes, SIGNAL('triggered(bool)'),
                        self.mtgeditor.enablePointAttributeDisplay)
        QObject.connect(self.actionViewMTG, SIGNAL('triggered(bool)'), self.mtgeditor.enableMTGDisplay)
        QObject.connect(self.actionViewControlPoints, SIGNAL('triggered(bool)'),
                        self.mtgeditor.enableControlPointsDisplay)
        QObject.connect(self.actionViewRadius, SIGNAL('triggered(bool)'), self.mtgeditor.enableRadiusDisplay)
        QObject.connect(self.actionView3DModel, SIGNAL('triggered(bool)'), self.mtgeditor.enable3DModelDisplay)
        QObject.connect(self.actionRefreshView, SIGNAL('triggered(bool)'), self.mtgeditor.refreshView)
        QObject.connect(self.actionAdjustView, SIGNAL('triggered(bool)'), self.mtgeditor.adjustView)

        QObject.connect(self.actionComputeMaxRadius, SIGNAL('triggered(bool)'),
                        lambda: self.mtgeditor.estimateAllRadius(maxmethod=True))
        QObject.connect(self.actionComputeMeanRadius, SIGNAL('triggered(bool)'),
                        lambda: self.mtgeditor.estimateAllRadius(maxmethod=False))
        QObject.connect(self.actionComputeMeanRadius, SIGNAL('triggered(bool)'),
                        lambda: self.mtgeditor.estimateAllRadius(maxmethod=False))
        QObject.connect(self.actionSmoothRadius, SIGNAL('triggered(bool)'), self.mtgeditor.smoothRadius)
        QObject.connect(self.actionThresholdRadius, SIGNAL('triggered(bool)'), self.mtgeditor.thresholdRadius)
        QObject.connect(self.actionPipeModel, SIGNAL('triggered(bool)'), self.mtgeditor.pipeModel)
        QObject.connect(self.actionPipeModelAverageDistance, SIGNAL('triggered(bool)'),
                        self.mtgeditor.pipeModelAverageDistance)

        # QObject.connect(self.actionAverageRadius, SIGNAL('triggered(bool)'),self.mtgeditor.averageNodesRadius) # TODO
        # QObject.connect(self.actionFilterRadius, SIGNAL('triggered(bool)'),self.mtgeditor.filterNodesRadius) # TODO

        QObject.connect(self.actionCheckMTG, SIGNAL('triggered(bool)'), self.mtgeditor.checkMTG)
        QObject.connect(self.actionSmoothPosition, SIGNAL('triggered(bool)'), self.mtgeditor.smoothPosition)

        QObject.connect(self.actionRootBottom, SIGNAL('triggered(bool)'), self.mtgeditor.addBottomRoot)
        QObject.connect(self.actionRootTop, SIGNAL('triggered(bool)'), self.mtgeditor.addTopRoot)

        QObject.connect(self.actionXuReconstruction, SIGNAL('triggered(bool)'), self.mtgeditor.xuReconstruction)
        QObject.connect(self.actionLivnyReconstruction, SIGNAL('triggered(bool)'), self.mtgeditor.livnyReconstruction)
        QObject.connect(self.actionAdaptiveScaReconstruction, SIGNAL('triggered(bool)'),
                        self.mtgeditor.adaptivescaReconstruction)
        QObject.connect(self.actionScaReconstruction, SIGNAL('triggered(bool)'), self.mtgeditor.scaReconstruction)
        QObject.connect(self.actionGraphColonization, SIGNAL('triggered(bool)'), self.mtgeditor.graphColonization)

        QObject.connect(self.actionAngleEstimation, SIGNAL('triggered(bool)'), self.mtgeditor.angleEstimate)
        QObject.connect(self.actionEditScale, SIGNAL('triggered(bool)'), self.mtgeditor.tagScale)
        QObject.connect(self.actionCommitScale, SIGNAL('triggered(bool)'), self.mtgeditor.commitScale)
        QObject.connect(self.actionTagProperty, SIGNAL('triggered(bool)'), self.mtgeditor.startTagProperty)
        QObject.connect(self.action3DRepresentation, SIGNAL('triggered(bool)'), self.mtgeditor.show3DModel)

        QObject.connect(self.visibilityEnabled, SIGNAL('clicked(bool)'), self.mtgeditor.enabledClippingPlane)
        QObject.connect(self.backVisibilitySlider, SIGNAL('valueChanged(int)'), self.mtgeditor.setBackVisibility)
        QObject.connect(self.frontVisibilitySlider, SIGNAL('valueChanged(int)'), self.mtgeditor.setFrontVisibility)
        QObject.connect(self.pointSizeSlider, SIGNAL('valueChanged(int)'), self.mtgeditor.setPointWidth)
        QObject.connect(self.nodeSizeSlider, SIGNAL('valueChanged(int)'), self.mtgeditor.setNodeWidth)
        QObject.connect(self.pointFilterSlider, SIGNAL('valueChanged(int)'), self.mtgeditor.setPointFilter)

        self.mtgeditor.actionEditScale = self.actionEditScale
        self.mtgeditor.actionTagProperty = self.actionTagProperty
        self.actionEditScale.setCheckable(True)
        self.actionTagProperty.setCheckable(True)

        self.mtgeditor.mainwindow = self
        self.mtgeditor.filehistory.setMenu(self.menuRecents)

        self.mtgeditor.statusBar = QStatusBar(self)
        self.setStatusBar(self.mtgeditor.statusBar)
        self.setWindowTitle('PlantScan3D')

    def closeEvent(self, event):
        self.mtgeditor.closeEvent(event)

    def keyPressEvent(self, event):
        super(MTGEditor, self).keyPressEvent(event)
        self.keyPressed.emit(event.key())

    def keyReleaseEvent(self, event):
        super(MTGEditor, self).keyReleaseEvent(event)
        self.keyReleased.emit(event.key())

def main():
    # os.chdir(r'D:\Fred\Mes Documents\Develop\vplants\mbranches\pointreconstruction\data\pointset')
    qapp = QApplication([])
    # qapp.processEvents()
    w = MTGEditor()
    w.show()
    qapp.exec_()


if __name__ == '__main__':
    main()
