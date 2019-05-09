from openalea.plantgl.all import *
from PyQt5.Qt import *
from PyQGLViewer import *
import OpenGL.GL as ogl
import OpenGL.GLU as oglu
from math import pi

try:
    GLClassWidget = QOpenGLWidget
except:
    GLClassWidget = QGLWidget


class ThumbnailMaker (GLClassWidget):
    def __init__(self, scene, size, parent):
        GLClassWidget.__init__(self, parent)
        self.msize = size
        self.scene = scene
        self.bbox = BoundingBox(scene)
        self.discretizer = Discretizer()
        self.renderer = GLRenderer(self.discretizer)
        self.renderer.renderingMode = GLRenderer.Dynamic

    def initGL(self):
        pass

    def paintGL(self):
        w,h = self.msize
        center = self.bbox.getCenter()
        size3d = max(self.bbox.getSize())*1.1
        ogl.glClearColor(0,0,0,0)
        ogl.glClear(ogl.GL_COLOR_BUFFER_BIT)
        ogl.glViewport(0,0,w,h)
        ogl.glMatrixMode(ogl.GL_PROJECTION);
        ogl.glLoadIdentity()
        ogl.glOrtho(-1.,1.,-1.,1.,-1000,1000)
        ogl.glMatrixMode(ogl.GL_MODELVIEW);
        ogl.glLoadIdentity()
        oglu.gluLookAt(0,1,0,0,0,0,0,0,1)
        ogl.glScalef(1./size3d,1./size3d,1./size3d)
        #ogl.glRotatef(1,0,0,pi/2.)
        ogl.glTranslatef(-center.x,-center.y,-center.z)
        self.scene.apply(self.renderer)


def make_thumbnail(scene, size = (600,600), parentWidget = None):
    maker = ThumbnailMaker(scene, size, parentWidget)
    maker.resize(*size)
    if hasattr(maker, 'grabFramebuffer'):
        img = maker.grabFramebuffer() # Qt 5 style
    else: 
        maker.show()
        maker.updateGL()
        qApp.processEvents()
        img = maker.grabFrameBuffer() # Qt 4
        maker.hide()
    return img

if __name__ == '__main__':
    qapp =QApplication([])
    img = make_thumbnail(AsymmetricHull())
    widget = QLabel()
    widget.setPixmap(QPixmap.fromImage(img))
    widget.show()
    qapp.exec_()
