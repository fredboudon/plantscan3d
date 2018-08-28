from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQGLViewer import *
from OpenGL.GL import *

import os
import random
from openalea.plantgl.all import *

toVec = lambda v : Vec(v.x,v.y,v.z)

class GLSegmentEditor(QGLViewer):
    set_selectable_trees = pyqtSignal(list)

    def __init__(self, parent=None):
        QGLViewer.__init__(self, parent)

        # plantgl basic object
        self.discretizer = Discretizer()
        self.glrenderer = GLRenderer(self.discretizer)
        self.glrenderer.renderingMode = GLRenderer.Dynamic

        self.pointsRep = None
        self.segmented_points = []
        self.points = None
        self.tree_seleted = None

        try:
            self.glrenderer.setGLFrame(self)
        except:
            print 'no text on GL Display'

    def init(self):
        self.camera().setViewDirection(Vec(0, -1, 0))
        self.camera().setUpVector(Vec(0, 0, 1))
        self.setBackgroundColor(QColor(*(0, 0, 0)))

    def setSegmentPoints(self, points):
        self.points = points
        kclosest = k_closest_points_from_ann(points, 10, True)
        connexsIndex = get_all_connex_components(points, kclosest)

        self.segmented_points = []
        colors = []  # type: List[Color3]
        for c in connexsIndex:
            if len(c) < 10000:
                continue
            color = None
            while color is None:
                r = random.randrange(0, 256)
                g = random.randrange(0, 256)
                b = random.randrange(0, 256)
                if not Color3(r, g, b) in colors:
                    color = Color3(r, g, b)
            self.segmented_points.append((c, color))

        self.set_selectable_trees.emit(['Tree '+str(i) for i in range(len(self.segmented_points))])
        bbx = BoundingBox(PointSet(points))
        self.setSceneBoundingBox(toVec(bbx.lowerLeftCorner), toVec(bbx.upperRightCorner))
        self.createPointsRepresentation()

    def fastDraw(self):
        if self.pointsRep is not None:
            self.pointsRep.apply(self.glrenderer)

    def draw(self):
        #glDisable(GL_CLIP_PLANE0)
        #glDisable(GL_CLIP_PLANE1)

        #glDisable(GL_LIGHTING)

        self.fastDraw()

    def createPointsRepresentation(self):
        shapes = []
        index = 0
        for indexes, color in self.segmented_points:
            width = 2 if self.tree_seleted == index else 1
            shapes.append(Shape(PointSet(self.points.subset(indexes), width=width), Material('mat '+str(color), color)))
            index += 1
        self.pointsRep = Scene(shapes)

    def setCurrentTrees(self, index):
        self.tree_seleted = index
        self.createPointsRepresentation()
        self.updateGL()

    def exportPoints(self):
        if self.tree_seleted is None:
            return

        fname = QFileDialog.getSaveFileName(self, "Save Points file",
                                            "",
                                            "Points Files (*.asc *.xyz *.pwn *.pts *.bgeom *.ply);;All Files (*.*)")
        if not fname: return
        fname = str(fname)

        points = self.points.subset(self.segmented_points[self.tree_seleted][0])
        Scene([PointSet(points)]).save(fname)

    def save_request(self, file_path):
        if self.tree_seleted is None:
            return

        from zipfile import ZipFile, ZIP_DEFLATED

        path, fname = os.path.split(str(file_path))
        try:
            os.makedirs(path)
        except:
            pass

        zip = ZipFile(file_path, mode='w', compression=ZIP_DEFLATED)
        points = self.points.subset(self.segmented_points[self.tree_seleted][0])

        Scene([PointSet(points)]).save(path + '/point_cloud.ply')
        zip.write(path + '/point_cloud.ply', 'point_cloud.ply')
        zip.close()
