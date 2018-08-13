try:
    import openalea.plantscan3d.py2exe_release

    py2exe_release = True
    print 'Py2ExeRelease'
except ImportError:
    py2exe_release = False
    print 'StdRelease'

if not py2exe_release:
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
    cui.check_rc_generation(os.path.join(ldir, 'plantscan3d.qrc'))

import editor_ui
from database import dbeditor, db_connection


class MTGEditor(QMainWindow, editor_ui.Ui_MainWindow):

    def __init__(self, parent=None):
        """
        @param parent : parent window
        """
        QMainWindow.__init__(self, parent)
        editor_ui.Ui_MainWindow.__init__(self)
        self.setupUi(self)
        self.pointSizeSlider.setValue(self.mtgeditor.pointWidth)
        self.nodeSizeSlider.setValue(self.mtgeditor.nodeWidth)
        QObject.connect(self.actionOpenMTG, SIGNAL('triggered(bool)'), self.mtgeditor.openMTG)
        QObject.connect(self.actionImportMTG, SIGNAL('triggered(bool)'), self.mtgeditor.importMTG)  # TODO
        QObject.connect(self.actionSaveMTG, SIGNAL('triggered(bool)'), self.mtgeditor.saveMTG)
        QObject.connect(self.actionSave, SIGNAL('triggered(bool)'), self.mtgeditor.save)
        QObject.connect(self.actionSaveSnapshot, SIGNAL('triggered(bool)'), self.mtgeditor.saveSnapshot)
        QObject.connect(self.actionImportPoints, SIGNAL('triggered(bool)'), self.mtgeditor.importPoints)
        QObject.connect(self.actionExportPoints, SIGNAL('triggered(bool)'), self.mtgeditor.exportPoints)
        QObject.connect(self.actionExportGeom, SIGNAL('triggered(bool)'), self.mtgeditor.exportAsGeom)
        QObject.connect(self.actionExportNodeList, SIGNAL('triggered(bool)'), self.mtgeditor.exportNodeList)

        self.db_connection = db_connection.DatabaseConnection(self)
        QObject.connect(self.actionConnect_to_Database, SIGNAL('triggered(bool)'), self.db_connection.show)
        QObject.connect(self.db_connection, SIGNAL('accepted()'), self.db_connection_validated)

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
        QObject.connect(self.actionRecalculate_Colors, SIGNAL('triggered(bool)'), self.mtgeditor.RecalculateColors)

        from mtgeditorwidget import WhiteTheme, BlackTheme
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

        QObject.connect(self.actionDelete_Selection, SIGNAL('triggered(bool)'), self.mtgeditor.deleteSelection)
        QObject.connect(self.actionKeep_Selection, SIGNAL('triggered(bool)'), self.mtgeditor.keepSelection)
        QObject.connect(self.actionSoil, SIGNAL('triggered(bool)'), self.mtgeditor.selectSoil)
        QObject.connect(self.actionWire, SIGNAL('triggered(bool)'), self.mtgeditor.selectWire)
        QObject.connect(self.mtgeditor, SIGNAL('wireAvailable(bool)'), self.actionWire.setEnabled)
        QObject.connect(self.actionWire_KeepPoint, SIGNAL('triggered(bool)'), self.mtgeditor.wireKeepPoint)
        QObject.connect(self.actionPole, SIGNAL('triggered(bool)'), self.mtgeditor.selectPole)
        QObject.connect(self.actionSegment, SIGNAL('triggered(bool)'), self.mtgeditor.segment)
        QObject.connect(self.mtgeditor, SIGNAL('nextSegmentedTreeAvailable(bool)'), self.actionNext_Segmented_Tree.setEnabled)
        QObject.connect(self.actionNext_Segmented_Tree, SIGNAL('triggered(bool)'), self.mtgeditor.nextSegmentedTree)

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

        self.openDBObject = None

    def closeEvent(self, event):
        from database.server_manip import server_info
        server_info.save_register_ids()
        self.mtgeditor.closeEvent(event)

    def test_connection_callback(self, status):
        if status:
            def get_file_path(fname):
                file_path = './'
                if '/' in fname:
                    end_path = fname.rfind('/')
                    if fname.startswith('/'):
                        file_path = fname[:end_path] + '/'
                    else:
                        file_path = fname[:end_path] + '/'
                return file_path

            def delete_request(id):
                if self.openDBObject == id:
                    self.openDBObject = None

                    msgBox = QMessageBox()
                    msgBox.setText('The current opened scan has been deleted from the database, do you want to clean the viewer ?')
                    msgBox.setStandardButtons(QMessageBox.Apply | QMessageBox.Cancel)
                    msgBox.setDefaultButton(QMessageBox.Cancel)

                    if msgBox.exec_() == QMessageBox.Apply:
                        from openalea.plantgl.all import PointSet, Point3Array, Color4Array
                        self.mtgeditor.setPoints(PointSet(Point3Array(), Color4Array()))

            def open_request(id, fname):
                from zipfile import ZipFile, ZIP_DEFLATED

                file_path = get_file_path(str(fname))

                zip = ZipFile(fname, mode='r', compression=ZIP_DEFLATED)
                zip.extractall(file_path)

                if 'point_cloud.ply' in zip.namelist():
                    self.mtgeditor.readPoints(str(file_path + 'point_cloud.ply'))
                if 'skeleton.bmtg' in zip.namelist():
                    self.mtgeditor.readMTG(str(file_path + 'skeleton.bmtg'))

                self.openDBObject = id
                zip.close()

            def save_request(fname):
                from zipfile import ZipFile, ZIP_DEFLATED

                file_path = get_file_path(str(fname))

                zip = ZipFile(fname, mode='w', compression=ZIP_DEFLATED)

                if self.mtgeditor.points is not None and len(self.mtgeditor.points.pointList) > 0:
                    self.mtgeditor.savePoints(file_path + 'point_cloud.ply', self.mtgeditor.points)
                    zip.write(file_path + 'point_cloud.ply', 'point_cloud.ply')
                if self.mtgeditor.mtg is not None:
                    self.mtgeditor.writeMTG(file_path + 'skeleton.bmtg')
                    zip.write(file_path + 'skeleton.bmtg', 'skeleton.bmtg')
                zip.close()

            def set_object_request(id):
                self.openDBObject = id

            def size_callback():
                return len(self.mtgeditor.points.pointList)

            def make_thumbnail():
                from thumbnailmaker import make_thumbnail
                from openalea.plantgl.all import Scene
                return make_thumbnail(Scene([self.mtgeditor.points]),  )

            def reset_open_object():
                self.openDBObject = None
                self.database_editor.current_opened_item = None

            self.actionDatabase.setEnabled(True)
            self.actionExport_To_Database.setEnabled(True)
            self.actionUpdate_Current_Item.setEnabled(True)
            self.database_editor = dbeditor.DatabaseEditor(size_callback, make_thumbnail, parent=self)
            QObject.connect(self.actionDatabase, SIGNAL('triggered(bool)'), self.database_editor.show)
            QObject.connect(self.actionExport_To_Database, SIGNAL('triggered(bool)'), self.database_editor.insert_item)
            QObject.connect(self.actionUpdate_Current_Item, SIGNAL('triggered(bool)'), self.database_editor.update_current_item)
            self.database_editor.openObjectRequested.connect(open_request)
            self.database_editor.saveObjectRequested.connect(save_request)
            self.database_editor.setCurrentObjectRequested.connect(set_object_request)
            self.database_editor.objectDeleted.connect(delete_request)

            self.mtgeditor.open_file.connect(reset_open_object)
            QMessageBox.information(self, 'Connection success', 'The connection to the MongoDB server has succeeded')
            self.database_editor.show()
        else:
            QMessageBox.warning(self, 'Connection fail', 'The connection to the MongoDB server has failed')
            self.db_connection.show()

    def db_connection_validated(self):
        try:
            # Python 3.x
            from urllib.parse import quote_plus
        except ImportError:
            # Python 2.x
            from urllib import quote_plus

        mongodb_address = self.db_connection.addressComboBox.currentText()
        mongodb_username = self.db_connection.usernameLineEdit.text()
        mongodb_password = self.db_connection.passwordLineEdit.text()
        uri = 'mongodb://'
        if self.db_connection.IDGroupBox.isChecked():
            uri += quote_plus(mongodb_username) + ':' + quote_plus(mongodb_password) + '@' + mongodb_address
        else:
            uri += mongodb_address
        from database.server_manip import server_info, WorkerTestConnection

        server_info.mongodb_uri = uri

        self.workerThread = QThread()
        self.workerObject = WorkerTestConnection()
        self.workerObject.moveToThread(self.workerThread)
        self.workerThread.started.connect(self.workerObject.run)
        self.workerObject.finished.connect(self.workerThread.quit)
        self.workerObject.result.connect(self.test_connection_callback)
        self.workerThread.start()


def main():
    qapp = QApplication([])
    # qapp.processEvents()
    w = MTGEditor()
    w.show()
    qapp.exec_()


if __name__ == '__main__':
    main()
