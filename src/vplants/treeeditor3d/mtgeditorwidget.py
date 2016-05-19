from PyQt4.QtGui import *
from PyQt4.Qt import *
from PyQGLViewer import *
from OpenGL.GL import *
from openalea.plantgl.all import *
from openalea.plantgl.gui.editablectrlpoint import *
import openalea.mtg.algo as mtgalgo
from pglnqgl import *
import os
from math import pi
from serial import *
from shareddata import *

import os
import compile_ui as cui
ldir    = os.path.dirname(__file__)
cui.check_ui_generation(os.path.join(ldir, 'contraction.ui'))
cui.check_ui_generation(os.path.join(ldir, 'reconstruction.ui'))
cui.check_ui_generation(os.path.join(ldir, 'radius.ui'))
cui.check_ui_generation(os.path.join(ldir, 'propwidget.ui'))

class Pos3Setter:
    def __init__(self,ctrlpointset,index):
        self.ctrlpointset = ctrlpointset
        self.index = index
    def __call__(self,pos):
        self.ctrlpointset[self.index] = toV3(pos)

def createMTGRepresentation(mtg,segment_inf_material,segment_plus_material,translation = None, positionproperty= 'position'):
    scene = Scene()
    shindex = {}
    positions = mtg.property(positionproperty)
    r = set(mtg.component_roots_at_scale(mtg.root,scale=mtg.max_scale()))
    def choose_mat(mtg,nid,segment_inf_material,segment_plus_material):
        if mtg.edge_type(nid) == '<': return segment_inf_material
        else : return segment_plus_material
    l = [createEdgeRepresentation(mtg.parent(nodeID),nodeID,positions,choose_mat(mtg,nodeID,segment_inf_material,segment_plus_material),translation) for nodeID in mtg.vertices(scale=mtg.max_scale()) if not nodeID in r]
    scene = Scene(l)
    shindex = dict((sh.id,i) for i,sh in enumerate(l))
    # for nodeID in mtg.vertices(scale=2):
        # for son in mtg.children(nodeID):
            # shindex[son] = i
            # scene += createEdgeRepresentation(nodeID,son,positions,segment_material,translation)
            # i+=1
            
    return scene, shindex

def createEdgeRepresentation(begnode,endnode,positions,material, translation = None):
    if begnode is None or endnode is None: 
        print 'Pb with node ', begnode, endnode
        return None
    res = Polyline([positions[begnode], positions[endnode]],width=1)
    #res = Group([res,Translated((positions[begnode]+positions[endnode])/2,Text(str(endnode)))])
    if translation:
        res = Translated(translation, res)
    return Shape(res,material,endnode)

def createRadiiRepresentation(mtg, material, translation = None, positionproperty= 'position', radiusproperty = 'radius'):
    scene = Scene()
    shindex = {}
    positions = mtg.property(positionproperty)
    radii = mtg.property(radiusproperty)
    l = [createRadiusRepresentation(mtg, nodeID, positions, radii, material, translation) for nodeID in radii.keys()]
    scene = Scene(l)
    shindex = dict((sh.id,i) for i,sh in enumerate(l))
            
    return scene, shindex
    
def createRadiusRepresentation(mtg, node, positions, radii, material, translation = None):
    res = Polyline2D.Circle(radii[node],16)
    if mtg.parent(node):
        d = direction(positions[node] - positions[mtg.parent(node)])
        i = d.anOrthogonalVector()
        j = d ^ i
        res = Oriented(i,j,res)
    res = Translated(positions[node]+ (translation if translation else Vector3(0,0,0)), res)
    return Shape(res,material,node)
 
def createCtrlPoints(mtg,color,positionproperty = 'position',callback = None):
    ctrlPoints = dict( (nodeID , createCtrlPoint(mtg,nodeID,color,positionproperty,callback)) for nodeID in mtg.vertices(scale=mtg.max_scale()) )
    return ctrlPoints

def createCtrlPoint(mtg,nodeID,color,positionproperty = 'position',callback = None):
    ccp = CtrlPoint(mtg.property(positionproperty)[nodeID], Pos3Setter(mtg.property(positionproperty),nodeID),color=color,id=nodeID)
    if callback: ccp.setCallBack(callback)
    return ccp

def createAttractorsRepresentation(attractors, width, material):
    pointset = PointSet(attractors)
    pointset.width = width
    return Scene([Shape(pointset, material)])


def getConeDirections(u, angle):
    return ConePerception().getConeAxis(u, angle)

def createCone(p1, p2, angle, resolution=20):
    from math import tan
    o = Vector3(p2)
    nz = Vector3(p1) - Vector3(p2)
    h = nz.normalize()
    ny = cross(nz,Vector3.OX)
    if  norm(ny) < 1e-3:
        ny = cross(nz,Vector3.OY)
    ny.normalize()
    nx = cross(ny,nz)
    nx.normalize()
    radius = tan(angle/2)*h
    return Translated(o,Oriented(nx,ny,Cone(radius,h,slices=resolution)))

def createConeRepresentation(p1, axises, height, angle, material):
    p2list = [ p1 + (height*u) for u in axises]
    
    res = Scene()
    for p2 in p2list:
        c = createCone(p1, p2, angle)
        res += Scene([Shape(c, material)])
    
    return res



class GLMTGEditor(QGLViewer):

    Edit, Selection, TagScale, TagProperty, Rotate = 1,2,4,8,16

    def __init__(self,parent,pointfile = None, mtgfile = None):
        QGLViewer.__init__(self,parent)
        self.setStateFileName('.mtgeditor.xml') 
        
        self.mode = None
        
        # shape and material to display the object
        self.greytheme = {'BackGround': (0,0,0), 
                          'Points' : (180,180,180),
                          'ContractedPoints' : (255,0,0),
                          'CtrlPoints' : (30,250,30),
                          'NewCtrlPoints' : (30,250,250),
                          'SelectedCtrlPoints' : (30,250,30),
                          'EdgeInf' : (255,255,255),
                          'EdgePlus' : (255,0,0),
                          'Radius' : (200,200,200),
                          '3DModel' : (128,64,0),
                          'LocalAttractors' :(255, 255, 0),
                          'Cone' :(255,255,0),
                          'TaggedCtrlPoint' : (255,0,0),
                          'UnTaggedCtrlPoint' : (255,255,255),
                          'UpscaleCtrlPoint' : [(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255)]}
                            
        self.whitetheme = {'BackGround': (255,255,255), 
                          'Points' : (180,180,180),
                          'ContractedPoints' : (255,0,0),
                          'CtrlPoints' : (250,30,30),
                          'NewCtrlPoints' : (30,250,250),
                          'SelectedCtrlPoints' : (30,250,30),
                          'EdgeInf' : (0,0,0),
                          'EdgePlus' : (200,200,0),
                          'Radius' : (100,100,100),
                          '3DModel' : (128,64,0),
                          'LocalAttractors' :(255, 255, 0),
                          'Cone' :(255,255,0),
                          'TaggedCtrlPoint' : (255,0,0),
                          'UnTaggedCtrlPoint' : (0,0,0),
                          'UpscaleCtrlPoint' : [(0,255,0),(0,0,255),(255,255,0),(255,0,255),(0,255,255)]}
                            
        self.theme = self.greytheme
        
        self.pointMaterial = Material(self.theme['Points'],1)
        self.contractedpointMaterial = Material(self.theme['ContractedPoints'],1)
        self.ctrlPointColor = self.theme['CtrlPoints']
        self.newCtrlPointColor = self.theme['NewCtrlPoints']
        self.edgeInfMaterial = Material(self.theme['EdgeInf'],1)
        self.edgePlusMaterial = Material(self.theme['EdgePlus'],1)
        self.selectedPointColor = Material(self.theme['SelectedCtrlPoints'],1)
        self.radiusMaterial = Material(self.theme['Radius'],1)
        self.modelMaterial =  Material(self.theme['3DModel'],1)
        self.pointDisplay = True
        self.contractedpointDisplay = True
        self.mtgDisplay = True
        self.ctrlPointDisplay = True
        self.modelDisplay = True
        self.radiusDisplay = True
        self.pointfilter = 0
        self.pointWidth = 2
        
        # plantgl basic object 
        self.discretizer = Discretizer()
        self.glrenderer = GLRenderer(self.discretizer)
        self.glrenderer.renderingMode = GLRenderer.Dynamic
        self.ctrlrenderer=GLCtrlPointRenderer(self.discretizer)
        try:
            self.glrenderer.setGLFrame(self)
        except:
            print 'no text on GL Display'
        
        self.modelRep = None
        
        self.points = None if pointfile is None else Scene(pointfile)[0].geometry
        self.contractedpoints = None
        self.mtgfile = mtgfile
        self.propertyposition = 'position'        
        self.propertyradius = 'radius'        
        
        self.pointsRep = None
        self.contractedpointsRep = None
        
        self.pointsKDTree = None
        
        self.mtg  = None        
        self.mtgrep = None
        self.mtgrepindex = None
        
        self.ctrlPoints = None
        self.ctrlPointPrimitive = None
        self.nodeWidth = 4
        self.ctrlPointsRep = None
        
        self.radiusRep = None
        self.radiusRepIndex = dict()

        if self.mtgfile : self.readMTG(mtgfile)
        
        self.focus = None
        self.selection = None
        self.selectionTrigger = None
        
        # Debug Information
        self.nodesinfo = None
        self.nodesinfoRepIndex = {}
        
        
        self.attractorsMaterial = Material(self.theme['LocalAttractors'],1)
        self.attractorsDisplay = True
        self.attractors = None
        self.attractorsRep = Scene() 
        
        self.coneMaterial = Material(ambient=self.theme['Cone'], diffuse=1, transparency=0.5)
        self.conesDisplay = True
        self.cones = None
        self.conesRep = Scene()
        
        self.translation = None
        
        self.clippigPlaneEnabled = False        
        self.frontVisibility = 0
        self.backVisibility = 1.0

        self.backupdata = []
        self.redodata = []
        self.maxbackup = 4
        
        self.temporaryinfo2D = None
        self.temporaryinfo = None
        
        self.progressdialog = QProgressDialog('Processing ...','Ok',0,100,self)
        self.progressdialog.setWindowModality(Qt.WindowModal)

        def showProgress(msg,percent):
            #print msg % percent
            if percent < 1 : self.progressdialog.show()
            self.progressdialog.setValue(percent)

        pgl_register_progressstatus_func(showProgress)

        self.currenttagname = 'ScaleTag'

        if not os.path.exists(get_shared_data('mtg')):
            self.parent().menuLoad.setEnabled(False)

        self.propertyeditor = None

    def createBackup(self):
        from copy import deepcopy
        if len(self.backupdata) == self.maxbackup:
            del self.backupdata[0]
        self.backupdata.append(deepcopy(self.mtg))
        self.emit(SIGNAL('undoAvailable(bool)'),True)
        self.redodata = []
        self.emit(SIGNAL('redoAvailable(bool)'),False)
        self.discardTempInfoDisplay()
        
    def createPointBackup(self):
        from copy import deepcopy
        if len(self.backupdata) == self.maxbackup:
            del self.backupdata[0]
        self.backupdata.append(PointSet(Point3Array(self.points.pointList),Color4Array(self.points.colorList)))
        self.emit(SIGNAL('undoAvailable(bool)'),True)
        self.redodata = []
        self.emit(SIGNAL('redoAvailable(bool)'),False)
        self.discardTempInfoDisplay()


    def undo(self):
        if len(self.backupdata) > 0:
            data = self.backupdata.pop()
            if type(data) == MTG:
                self.redodata.append(self.mtg)
                self.mtg = data
                self.__update_all_mtg__()
            elif type(data) == PointSet:
                self.redodata.append(self.points)
                self.setPoints(data)
            else:
                QMessageBox.error(self,'undo',"Bad type for undo data")
                return

            self.showMessage("Undo "+str(type(data))+" at "+str(id(data)))
            self.emit(SIGNAL('redoAvailable(bool)'),True)
            if len(self.backupdata) == 0:
                self.emit(SIGNAL('undoAvailable(bool)'),False)
            self.updateGL()
        else:
            self.showMessage("No backup available.")
            self.emit(SIGNAL('undoAvailable(bool)'),False)

    def redo(self):
        if len(self.redodata) > 0:
            data = self.redodata.pop()
            if type(data) == MTG:
                self.backupdata.append(self.mtg)
                self.mtg = data
                self.__update_all_mtg__()
            elif type(data) == PointSet:
                self.backupdata.append(self.points)
                self.setPoints(data)
            else:
                QMessageBox.error(self,'undo',"Bad type for undo data")
                return
            self.showMessage("Redo "+str(type(data))+" at "+str(id(data)))
            self.emit(SIGNAL('undoAvailable(bool)'),True)
            if len(self.redodata) == 0:
                self.emit(SIGNAL('redoAvailable(bool)'),False)
            self.updateGL()
        else:
            self.showMessage("No redo available.")
            self.emit(SIGNAL('redoAvailable(bool)'),False)
        
    def enabledClippingPlane(self, enabled):
        self.clippigPlaneEnabled = enabled
        if (enabled) : self.showMessage('Enabled Clipping Plane')
        else: self.showMessage( 'Disabled Clipping Plane')
        if self.isVisible() : self.updateGL()
        
    def setFrontVisibility(self, value):
        self.frontVisibility = (value / 100.)
        if self.isVisible() : self.updateGL()
    
    def setBackVisibility(self, value):
        self.backVisibility = value / 100.
        if self.isVisible() : self.updateGL()
    
    def applySelectionTrigger(self,node):
        if self.selectionTrigger:
            self.selectionTrigger(node)
        self.selectionTrigger = None
    def setSelectionTrigger(self,func):
        self.selectionTrigger = func
        
    def init(self):
        #self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.AltModifier)
        #self.setHandlerKeyboardModifiers(QGLViewer.FRAME,  Qt.NoModifier)
        #self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.ControlModifier)
        #self.setMouseBinding(Qt.LeftButton,QGLViewer.FRAME,QGLViewer.TRANSLATE)

        self.setMouseBindingDescription(Qt.ShiftModifier+Qt.LeftButton,"Rectangular selection")
        self.setMouseBindingDescription(Qt.LeftButton,"Camera/Control Points manipulation")
        self.setMouseBindingDescription(Qt.LeftButton,"When double clicking on a line, create a new line",True)
        self.setMode(self.Rotate)
        self.camera().setViewDirection(Vec(0,-1,0))
        self.camera().setUpVector(Vec(0,0,1))
        self.setBackgroundColor(QColor(*self.theme['BackGround']))
    
    def setFocus(self,point):
        """ Set focus to given control point """
        if self.focus:
            self.focus.hasFocus = False
            self.__update_ctrlpoint__(self.focus.id)
        self.focus = point
        if self.focus:
            point.hasFocus = True
            self.__update_ctrlpoint__(self.focus.id)
        
    def setSelection(self,point):
        """ Set focus to given control point """
        if self.selection:
            self.selection.selected = False
            self.__update_ctrlpoint__(self.selection.id)
        self.selection = point
        if self.selection:
            point.selected = True
            self.__update_ctrlpoint__(point.id)
            self.camera().setRevolveAroundPoint(toVec(point.position()))

    def fastDraw(self):
        """ paint in opengl """
        glDisable(GL_LIGHTING)
        if self.attractorsDisplay and self.attractors:
            self.attractorsRep.apply(self.glrenderer)
        
        if self.pointDisplay and self.points:
            #self.pointMaterial.apply(self.glrenderer)
            #self.points.apply(self.glrenderer)
            self.pointsRep.apply(self.glrenderer)
            
           
        if self.mtgDisplay and self.mtgrep:
            self.mtgrep.apply(self.glrenderer)

        if self.ctrlPointDisplay and self.focus :
            scid = self.ctrlPointsRepIndex[self.focus.id]
            self.ctrlPointsRep[scid].apply(self.glrenderer)
            
             
    def draw(self):
        """ paint in opengl """
        if self.clippigPlaneEnabled:
            glPushMatrix()
            glLoadIdentity()
            zNear = self.camera().zNear()
            zFar = self.camera().zFar()
            zDelta = (zFar-zNear) / 2
            viewDir = self.camera().viewDirection()
            if self.frontVisibility > 0:
                eq = [0.,0.,-1., -(zNear+  zDelta * self.frontVisibility)]
                glClipPlane(GL_CLIP_PLANE0,eq)
                glEnable(GL_CLIP_PLANE0)
            if self.backVisibility < 1.0:
                eq2 = [0.,0.,1., (zNear+  zDelta * self.backVisibility)]
                glClipPlane(GL_CLIP_PLANE1,eq2)
                glEnable(GL_CLIP_PLANE1)
            
            glPopMatrix()           
        else:
            glDisable(GL_CLIP_PLANE0)
            glDisable(GL_CLIP_PLANE1)
        glDisable(GL_LIGHTING)
        if self.attractorsDisplay and self.attractors:
            self.attractorsRep.apply(self.glrenderer)
         
        if self.pointDisplay and self.points:
            #self.pointMaterial.apply(self.glrenderer)
            #self.points.apply(self.glrenderer)
            self.pointsRep.apply(self.glrenderer)
            
           
        if self.mtgDisplay and self.mtgrep:
            self.mtgrep.apply(self.glrenderer)
        
        if self.ctrlPointDisplay and self.ctrlPointsRep:
            if self.focus is None:
                self.ctrlPointsRep.apply(self.glrenderer)
            else:
                scid = self.ctrlPointsRepIndex[self.focus.id]
                self.ctrlPointsRep[scid].apply(self.glrenderer)
            
        if self.radiusDisplay and self.radiusRep:    
            self.radiusRep.apply(self.glrenderer)

        glEnable(GL_LIGHTING)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)
        if self.modelDisplay and self.modelRep:
            self.modelRep.apply(self.glrenderer)
        

        if self.conesDisplay and self.cones:
            self.conesRep.apply(self.glrenderer)

        glDisable(GL_BLEND)
        glDisable(GL_LIGHTING)
         
        if self.temporaryinfo2D:
            self.startScreenCoordinatesSystem()
            self.temporaryinfo2D.apply(self.glrenderer)
            self.stopScreenCoordinatesSystem()
            
        if self.temporaryinfo:
            self.temporaryinfo.apply(self.glrenderer)
    
    def setTempInfoDisplay2D(self, sc):
        self.temporaryinfo2D = sc
    
    def setTempInfoDisplay(self, sc):
        self.temporaryinfo = sc
    
    def discardTempInfoDisplay(self):
        self.temporaryinfo2D = None
        self.temporaryinfo = None
        
    
    def setclassicdata(self,dataedit, dataoriginal, pointname = None):
        from os.path import join,exists
        firstname = join(get_shared_data('mtg'),'edition', dataedit+'.bmtg')
        if exists(firstname): mtgname = firstname
        else : mtgname = join(get_shared_data('mtg'),dataoriginal+'.bmtg')
        self.readMTG(str(mtgname))
        self.mtgfile = firstname
        
        if pointname is None: pointname = dataedit
        pointfname = str(join(get_shared_data('pointset'), pointname+'.bgeom'))
        print pointfname
        self.readPoints(pointfname)

    def puu1(self):
        self.setclassicdata('puu1','puu1')
        
    def puu3(self):
        self.setclassicdata('puu3','puu3')
        self.reorient()
        
    def cherry(self):
        self.setclassicdata('cherry','cherry','cherry_200k')
    
    def arabido(self):
        self.setclassicdata('arabido','arabido','arabido-yassin-200k')
        self.reorient()
        
    def appletree(self):
        self.readMTG("/Users/fboudon/Develop/oagit/plantscan3d/data/LidarPommier/digitmtg/X0342_r1.mtg", True)
        self.readPoints("/Users/fboudon/Develop/oagit/plantscan3d/data/LidarPommier/digitmtg/X0342_r1_004.xyz")
        self.alignScaleAndCenter()
        
    def openMTG(self):
        initialname = os.path.dirname(self.mtgfile) if self.mtgfile else get_shared_data('mtgdata')
        fname = QFileDialog.getOpenFileName(self, "Open MTG file",
                                                initialname,
                                                "MTG Files (*.mtg;*.bmtg);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.readMTG(fname)
        
    def importMTG(self):
        initialname = os.path.dirname(self.mtgfile) if self.mtgfile else get_shared_data('mtgdata')
        fname = QFileDialog.getOpenFileName(self, "Open MTG file",
                                                initialname,
                                                "MTG Files (*.mtg);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.readMTG(fname, True)
        
    def readMTG(self, fname, fromdigit = False):
        import os.path
        import sys
        import traceback as tb
        
        self.showMessage("Reading "+repr(fname))
        try:
            if os.path.splitext(fname)[1] == '.bmtg':
               mtg = readfile(fname)
            else: # .mtg
                # readable mtg format from openalea.mtg module
                stdmtg = read_mtg_file(fname)
                if fromdigit : convertStdMTGWithNode(stdmtg)
                mtg = stdmtg
                
            self.setMTG(mtg,fname)
            self.modelRep = None
            self.showEntireScene()
        except Exception, e:
            tb.print_exception(*sys.exc_info())
            QMessageBox.critical(self, 'Import Error', 'Import Error:'+repr(e))
        
    def setMTG(self,mtg,fname):
        self.mtg = mtg
        self.mtgfile = fname

        self.selection = None
        self.focus = None

        self.__update_all_mtg__()


    def updateMTGView(self):
        pt = self.camera().revolveAroundPoint()
        self.setMTG(self.mtg,self.mtgfile)
        self.camera().setRevolveAroundPoint(pt)
       
    def getUnitCtrlPointSize(self):
        scradius = self.sceneRadius()
        return  scradius/400

    def setNodeWidth(self, value):
        self.nodeWidth = value
        if self.ctrlPointPrimitive:
            self.ctrlPointPrimitive.radius = self.nodeWidth * self.getUnitCtrlPointSize()
        print self.sceneRadius()
        self.showMessage('Set Node Width to '+str(value)+' ('+str(self.ctrlPointPrimitive.radius)+')')
        self.updateGL()

    def createCtrlPoints(self):
        self.ctrlPoints = createCtrlPoints(self.mtg,self.ctrlPointColor,self.propertyposition,self.__update_value__)
        if self.mode == self.TagScale: self.tagScaleRepresentation()
        elif self.mode == self.TagProperty: selt.tagPropertyRepresentation()
        self.createCtrlPointRepresentation()


    def createCtrlPointRepresentation(self):
        self.ctrlPointsRep = Scene([ ctrlPoint.representation(self.ctrlPointPrimitive) for ctrlPoint in self.ctrlPoints.itervalues() ])
        self.ctrlPointsRepIndex = dict([( sh.id , i) for i,sh in enumerate(self.ctrlPointsRep) ])
        # self.ctrlPointsRepIndex = {2:0, 3:1, ..., 4362: 4360}

    def save(self):
        if self.mtgfile :
            self.writeMTG(self.mtgfile)
        else:
            self.saveMTG()
        
    def saveMTG(self):
        initialname = os.path.dirname(self.mtgfile) if self.mtgfile else get_shared_data('mtgdata')
        fname = QFileDialog.getSaveFileName(self, "Save MTG file",
                                                initialname,
                                                "MTG Files (*.mtg;*.bmtg);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.writeMTG(fname)
        
    def writeMTG(self,fname):
        fname = str(fname)
        import os.path,shutil
        if os.path.exists(fname):
            shutil.copy(fname,fname+'~')
        if os.path.splitext(fname)[1] == '.bmtg':
           writefile(fname,self.mtg)
        else: # .mtg
            # readable mtg format from openalea.mtg module
            stdmtg = convertToStdMTG(self.mtg)
            writeMTGfile(fname, stdmtg)
        self.mtgfile = fname
        self.showMessage("Write MTG in "+repr(fname))
        self.updateGL()
    
    def filter_points(self, pointset, pointfilter = None, ignorednodes = None):
        if pointfilter is None:
            pointfilter = self.pointfilter
        if not ignorednodes is None:
            ignorednodes = set(ignorednodes)

        if pointfilter > 0 and self.mtg:
            if ignorednodes:
                nodeids = [vid for vid in self.mtg.vertices(scale=self.mtg.max_scale()) if not vid in ignorednodes]
                nonone = lambda x, y : y if (x is None or x in ignorednodes) else x
            else:
                nodeids = list(self.mtg.vertices(scale=self.mtg.max_scale()))
                nonone = lambda x, y : y if (x is None) else x

            pos = self.mtg.property('position')
            nodes = [pos[i] for i in nodeids]
            
            nodeiddict = dict([(vid,i) for i,vid in enumerate(nodeids)])
            parents = [nodeiddict[nonone(self.mtg.parent(i),i)] for i in nodeids]
            print 'points_at_distance_from_skeleton', pointfilter
            distantpoints = points_at_distance_from_skeleton(pointset.pointList,nodes, parents, -pointfilter,1)
            #print distantpoints
            if pointset.colorList:
                return pointset.pointList.subset(distantpoints), pointset.colorList.subset(distantpoints)
            else:
                return pointset.pointList.subset(distantpoints), pointset.colorList
        else :
            return pointset.pointList, pointset.colorList
            
    
    def createPointsRepresentation(self):
        pointList, colorList = self.filter_points(self.points)
        self.pointsRep = Scene([Shape(PointSet(pointList,colorList, width = self.pointWidth), self.pointMaterial)])
    
    
    def setPointFilter(self, value):
        self.pointfilter = self.sceneRadius() * value / 10000.
        self.showMessage("Remove points at a distance "+str(self.pointfilter)+" of the skeleton")
        print self.pointfilter, self.sceneRadius(), value
        if self.points : self.createPointsRepresentation()
        if self.isVisible(): self.updateGL()
        
    def setPointWidth(self, value):
        self.pointWidth = value
        if self.pointsRep:
            self.pointsRep[0].geometry.width = value
        self.showMessage('Set Point Width to '+str(value))
        self.updateGL()
    
    def show3DModel(self):
        self.create3DModelRepresentation()
        self.modelDisplay = True
        self.updateGL()

    def create3DModelRepresentation(self, translation=None):
        scene = Scene()
        section= Polyline2D.Circle(1,30)
        
        for vid in self.mtg.vertices(scale=self.mtg.max_scale()):
            if self.mtg.parent(vid) is None or self.mtg.edge_type(vid) == "+":
                axe = self.mtg.Axis(vid)
                if not self.mtg.parent(vid) is None: axe.insert(0, self.mtg.parent(vid))
                points = [self.mtg.property(self.propertyposition)[nodeID] for nodeID in axe]
                radius = [(self.mtg.property(self.propertyradius).get(nodeID,0), self.mtg.property(self.propertyradius).get(nodeID,0)) for nodeID in axe]
                geometry = Extrusion(Polyline(points), section, radius)
                if translation: geometry = Translated(translation,geometry)
                scene += Shape(geometry, self.modelMaterial)
        self.modelRep =  scene
    
    def importPoints(self):
        initialname = get_shared_data('pointset')
        fname = QFileDialog.getOpenFileName(self, "Open Points file",
                                                initialname,
                                                "Points Files (*.asc;*.xyz;*.pwn;*.pts;*.txt;*.bgeom);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.readPoints(fname)
        
        
    def readPoints(self,fname):
        sc = Scene(fname)
        if len(sc) == 0:
            QMessageBox.warning(self,'file error','Not able to read points from file '+repr(fname))
            return
        try:
            points = sc[0].geometry.geometry
            self.translation =  sc[0].geometry.translation
            points.pointList.translate(self.translation)
        except AttributeError:
            points = sc[0].geometry
            self.translation =  Vector3(0,0,0)
        self.setPoints(points)
        self.showEntireScene()
        
    def setPoints(self,points, keepinfo = False):
        self.points = points
        class PointInfo():
            def __init__(self): pass

        if not keepinfo: self.pointinfo = PointInfo()
        if self.points.colorList is None: 
            bbx = BoundingBox(self.points)
            print 'generate color'
            colorList = [(100+int(100*((i.x-bbx.getXMin())/bbx.getXRange())),
                          100+int(100*((i.y-bbx.getYMin())/bbx.getYRange())),
                          100+int(100*((i.z-bbx.getZMin())/bbx.getZRange())),0) for i in self.points.pointList]
            self.points.colorList = colorList
        self.adjustTo(points)
        self.createPointsRepresentation()
        

    def exportPoints(self):
        if self.points is None:
            QMessageBox.warning(self,'data error','No points to save')
        initialname = get_shared_data('pointset')
        fname = QFileDialog.getSaveFileName(self, "Save Points file",
                                                initialname,
                                                "Points Files (*.asc;*.xyz;*.pwn;*.pts;*.bgeom);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.savePoints(fname)

    def savePoints(self,fname):
        Scene([self.points]).save(fname)
    

    
    def exportAsGeom(self):
        initialname = 'out.bgeom'
        fname = QFileDialog.getSaveFileName(self, "Save Geom file",
                                                initialname,
                                                "GEOM Files (*.bgeom;*.geom);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.saveAsGeom(fname)
        
    def saveAsGeom(self,fname):
        sc = Scene()
        if self.attractorsDisplay and self.attractors:
            #sc += self.attractorsRep
            pointset = PointSet(self.attractors)
            pointset.width = self.pointWidth
            sc += Shape(Translated(self.translation,PointSet(pointset)), self.attractorsMaterial)
        
        if self.pointDisplay and self.points:
            #sc += self.pointsRep
            sc += Shape(Translated(self.translation,PointSet(self.points.pointList)), self.pointMaterial)
            
        if self.contractedpointDisplay and self.contractedpoints:
            #sc += self.contractedpointsRep
            sc += Shape(Translated(self.translation,PointSet(self.contractedpoints.pointList)), self.contractedpointMaterial)
            
        if self.mtgDisplay and self.mtgrep:
            #sc +=  self.mtgrep
            mtgrep, mtgrepindex  = createMTGRepresentation(self.mtg,self.edgeInfMaterial,self.edgePlusMaterial, translation=self.translation)
            sc += mtgrep
        
        #if self.conesDisplay and self.cones:
        #    sc += self.conesRep
         
        if self.ctrlPointDisplay and self.ctrlPointsRep: pass
            #sc += self.ctrlPointsRep
            #sc += Scene([ ctrlPoint.representation(self.ctrlPointPrimitive) for ctrlPoint in self.ctrlPoints.itervalues() ])
            
        if self.modelDisplay and self.modelRep:
            sc += self.create3DModelRepresentation(self.translation)
            
        sc.save(fname)
         
    def exportNodeList(self):
        initialname = os.path.dirname(self.mtgfile)+'/'+os.path.basename(self.mtgfile)+'.txt' if self.mtgfile else get_shared_data('mtgdata')
        fname = QFileDialog.getSaveFileName(self, "Save Geom file",
                                                initialname,
                                                "Txt Files (*.txt);;All Files (*.*)")
        if not fname: return
        fname = str(fname)
        self.saveNodeList(fname)
        self.showMessage("Export done ...")
        
    def saveNodeList(self,fname):
        from vplants.pointreconstruction.mtgdata import export_mtg_in_txt
        stream = file(fname,'w')
        export_mtg_in_txt(self.mtg, stream)
        stream.close()
        
    def adjustTo(self,obj):
        bbx = BoundingBox(obj)
        self.setSceneBoundingBox(toVec(bbx.lowerLeftCorner),toVec(bbx.upperRightCorner))

    def __update_ctrlpoint__(self,pid):
        scid = self.ctrlPointsRepIndex[pid]
        self.ctrlPointsRep[scid] = self.ctrlPoints[pid].representation(self.ctrlPointPrimitive)
        
    def __update_edges__(self,pid):
        eid = self.mtgrepindex.get(pid)
        positions = self.mtg.property(self.propertyposition)
        mat = self.edgeInfMaterial if self.mtg.edge_type(pid) == '<' else self.edgePlusMaterial
        if eid:
            self.mtgrep[eid] = createEdgeRepresentation(self.mtg.parent(pid),pid,positions,mat)
        for son in self.mtg.children(pid):
            mat = self.edgeInfMaterial if self.mtg.edge_type(son) == '<' else self.edgePlusMaterial
            self.mtgrep[self.mtgrepindex[son]] = createEdgeRepresentation(pid,son,positions,mat)

    def __update_radius__(self, pid):
        positions = self.mtg.property(self.propertyposition)
        if self.mtg.property(self.propertyradius).get(pid):
            rep = createRadiusRepresentation(self.mtg, pid, positions, self.mtg.property(self.propertyradius), self.radiusMaterial )
            if self.radiusRepIndex.get(pid):
                self.radiusRep[self.radiusRepIndex[pid]] = rep
            else:
                self.radiusRepIndex[pid] = len(self.radiusRep)
                self.radiusRep.add(rep)

    def __update_value__(self,pid):
        """ update rep of mtg """
        self.__update_ctrlpoint__(pid)
        self.__update_edges__(pid)
        self.__update_radius__(pid)

    def __update_all_mtg__(self):
        self.mtgrep, self.mtgrepindex  = createMTGRepresentation(self.mtg,self.edgeInfMaterial,self.edgePlusMaterial)

        pointsize = self.nodeWidth * self.getUnitCtrlPointSize()
        self.ctrlPointPrimitive = Sphere(pointsize)
        self.createCtrlPoints()

        if self.points is None: 
            self.adjustTo(self.ctrlPointsRep)

            pointsize = self.nodeWidth * self.getUnitCtrlPointSize()
            self.ctrlPointPrimitive.radius = self.nodeWidth * self.getUnitCtrlPointSize()

        self.radiusRep, self.radiusRepIndex = createRadiiRepresentation(self.mtg, self.radiusMaterial, positionproperty= self.propertyposition, radiusproperty = self.propertyradius)

    def enablePointDisplay(self,enabled) : 
        if self.pointDisplay != enabled:
            self.pointDisplay = enabled
            self.updateGL()

    def enableContractedPointDisplay(self,enabled) : 
        if self.contractedpointDisplay != enabled:
            self.contractedpointDisplay = enabled
            self.updateGL()

    def enableMTGDisplay(self,enabled) : 
        if self.mtgDisplay != enabled:
            self.mtgDisplay = enabled
            self.updateGL()

    def enableControlPointsDisplay(self,enabled) : 
        if self.ctrlPointDisplay != enabled:
            self.ctrlPointDisplay = enabled
            self.updateGL()

    def enable3DModelDisplay(self,enabled): 
        if self.modelDisplay != enabled:
            self.modelDisplay = enabled
            self.updateGL()

    def enableRadiusDisplay(self,enabled): 
        if self.radiusDisplay != enabled:
            self.radiusDisplay = enabled
            self.updateGL()

    def isPointDisplayEnabled(self) : return self.pointDisplay
    def isContractedPointDisplayEnabled(self) : return self.contractedpointDisplay
    def isMTGDisplayEnabled(self) : return self.mtgDisplay
    def isControlPointsDisplayEnabled(self) : return self.ctrlPointDisplay
    def is3DModelDisplayEnabled(self): return self.modelDisplay
    def isRadiusDisplayEnabled(self): return self.radiusDisplay
    
    def adjustView(self):
        self.showEntireScene()
        
    def refreshView(self):
        self.setMTG(self.mtg,self.mtgfile)
   
    def getSelection(self,pos):
        possibles = []
        if self.ctrlPoints and self.ctrlPointDisplay:
            for cCtrlPoint in self.ctrlPoints.itervalues():
                cCtrlPoint.checkIfGrabsMouse(pos.x(), pos.y(), self.camera())
                if cCtrlPoint.grabsMouse():
                    pz = self.camera().viewDirection() * (cCtrlPoint.position()-self.camera().position()) 
                    z =  (pz - self.camera().zNear()) /(self.camera().zFar()-self.camera().zNear())
                    if z > 0 and not self.clippigPlaneEnabled or self.frontVisibility <= z*2 <= self.backVisibility:
                        possibles.append((z,cCtrlPoint))
        if len(possibles) > 0:
            possibles.sort(lambda x,y : cmp(x[0],y[0]))
            return possibles[0][1]
        return None
        
    def keyPressEvent(self, event):
        globalpos = self.geometry().topLeft()
        p  = self.parent()
        while p:
            globalpos += p.geometry().topLeft()
            p  = p.parent()
            
        mousepos = QCursor.pos() - globalpos
        cCtrlPoint = self.getSelection(mousepos)
        if cCtrlPoint:
            if event.key() == Qt.Key_T:            
                    self.setSelection(cCtrlPoint)
                    self.stickToPoints()
            elif event.key() == Qt.Key_G:            
                    self.setSelection(cCtrlPoint)
                    self.stickSubtree()
            elif event.key() == Qt.Key_R:            
                    self.setSelection(cCtrlPoint)
                    self.revolveAroundSelection()
            elif event.key() == Qt.Key_N:            
                    self.setSelection(cCtrlPoint)
                    self.newChild()
            elif event.key() == Qt.Key_M:            
                    self.setSelection(cCtrlPoint)
                    self.setAxialPoint()
            elif event.key() == Qt.Key_P:            
                    self.setSelection(cCtrlPoint)
                    self.beginReparentSelection()
            elif event.key() == Qt.Key_E:            
                    self.setSelection(cCtrlPoint)
                    self.splitEdge()
            elif event.key() == Qt.Key_Delete:            
                    self.setSelection(cCtrlPoint)
                    self.removeSelection()
            else: QGLViewer.keyPressEvent(self, event)
        else: QGLViewer.keyPressEvent(self, event)

    def mousePressEvent(self,event):
        """ Check for eventual operations the user asks: 
            shift start rectangular selection
            else check for which point is selected
        """
        nompe = False
        if self.mode == self.TagScale:
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setSelection(cCtrlPoint)
                self.tagScaleToNode()
                self.updateGL()
            else:
                self.setMode(self.Rotate | self.TagScale)

        elif self.mode == self.TagProperty:
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setSelection(cCtrlPoint)
                self.tagPropertyToNode()
                self.updateGL()
            else:
                self.setMode(self.Rotate | self.TagProperty)

        elif self.mode == self.Selection:
            # Selection of a second point to finish a previous action
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.applySelectionTrigger(cCtrlPoint)
            else:
                QMessageBox.warning(self,'Selection','Cannot find a node to select')
        elif event.modifiers() & Qt.ControlModifier :
            # only rotation
            self.setSelection(None)
            self.setMode(self.Edit)
        elif event.button() == Qt.RightButton:
            # context menu asked
            self.setSelection(None)
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setSelection(cCtrlPoint)
                self.updateGL()
                self.contextMenu(event.globalPos())
                nompe = True
            else:
                self.setMode(self.Rotate)
        else:
            # move selection or rotate
            self.setSelection(None)
            cCtrlPoint = self.getSelection(event.pos())
            if cCtrlPoint:
                self.setFocus(cCtrlPoint)
                self.createBackup()
                self.camera().setRevolveAroundPoint(toVec(cCtrlPoint.position()))
                self.setManipulatedFrame(cCtrlPoint)
                self.showMessage("Move point "+str(cCtrlPoint.id))
                # move manipulated frame
                self.setMode(self.Edit)
                self.updateGL()
            else: # if no point is selected, then move camera
                self.setMode(self.Rotate)
        if not nompe :
            QGLViewer.mousePressEvent(self,event)
        
    def mouseDoubleClickEvent(self,event):
        cCtrlPoint = self.getSelection(event.pos())
        if cCtrlPoint:
            print 'Select point ',cCtrlPoint.id
            if self.mode == self.Selection:
                self.applySelectionTrigger(cCtrlPoint)
            else:                
                self.camera().setRevolveAroundPoint(toVec(cCtrlPoint.position()))

    def mouseMoveEvent(self,event):
        """On mouse release, we release every grabbed objects"""
        QGLViewer.mouseMoveEvent(self,event)
        
    def mouseReleaseEvent(self,event):
        """On mouse release, we release every grabbed objects"""
        QGLViewer.mouseReleaseEvent(self,event)
        # clear manipulated object
        self.setManipulatedFrame(None)
        self.setFocus(None)
        if self.mode & self.TagScale: self.setMode(self.TagScale)
        elif self.mode & self.TagProperty: self.setMode(self.TagProperty)
        else : self.setMode(self.Rotate)
        self.updateGL()
    
    def contextMenu(self,pos):
        menu = QMenu(self)
        action = menu.addAction("Node "+str(self.selection.id))
        f = QFont()
        f.setBold(True)
        action.setFont(f)
        if not self.mode in [self.TagScale, self.TagProperty]:
            menu.addSeparator()
            menu.addAction("Remove node (DEL)",self.removeSelection)
            if len(list(self.mtg.children(self.selection.id))) > 0:
                menu.addAction("Remove subtree",self.removeSubtree)
            menu.addSeparator()
            menu.addAction("New child (N)",self.newChild)
            menu.addAction("Reparent (P)",self.beginReparentSelection)
            menu.addAction("Split Edge (E)",self.splitEdge)
            menu.addMenu(self.mainwindow.menuReconstruction)
        menu.addSeparator()
        menu.addAction("Set Branching Points",self.setBranchingPoint)
        menu.addAction("Set Axial Points (M)",self.setAxialPoint)        
        if self.points:
            menu.addSeparator()
            menu.addAction("S&tick to points (T)",self.stickToPoints)
            menu.addAction("Stick subtree (G)",self.stickSubtree)
            menu.addSeparator()
            menu.addAction("Estimate radius",self.estimateRadius)
        menu.addSeparator()
        menu.addAction("Revolve Around (R)",self.revolveAroundSelection)
        menu.addSeparator()
        menu.addAction("Properties",self.editProperty)
        if self.mode == self.TagScale:
            menu.addSeparator()
            menu.addAction("Tag (A)",self.tagNode)
        menu.exec_(pos)
        
    def setMode(self,mode):
        if self.mode != mode:
            if mode == self.Edit or mode == self.Selection:
                self.mode = mode
                self.setMouseBinding(Qt.LeftButton,QGLViewer.FRAME,QGLViewer.TRANSLATE)
                self.setMouseBinding(Qt.RightButton,QGLViewer.FRAME,QGLViewer.NO_MOUSE_ACTION)

                self.setMouseBinding(Qt.ControlModifier+QtCore.Qt.LeftButton,  QGLViewer.CAMERA,QGLViewer.ROTATE)
                self.setMouseBinding(Qt.ControlModifier+QtCore.Qt.RightButton, QGLViewer.CAMERA,QGLViewer.TRANSLATE)
                self.setMouseBinding(Qt.ControlModifier+QtCore.Qt.MiddleButton,QGLViewer.CAMERA,QGLViewer.ZOOM) 

                #self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.AltModifier)
                #self.setHandlerKeyboardModifiers(QGLViewer.FRAME,  Qt.NoModifier)
                #self.setHandlerKeyboardModifiers(QGLViewer.CAMERA, Qt.ControlModifier)
            elif mode == self.Rotate or mode == self.TagScale or mode == self.TagProperty:
                self.mode = mode
   
                self.setMouseBinding(QtCore.Qt.ControlModifier+QtCore.Qt.LeftButton,QGLViewer.FRAME,QGLViewer.TRANSLATE)
                self.setMouseBinding(QtCore.Qt.ControlModifier+QtCore.Qt.RightButton,QGLViewer.FRAME,QGLViewer.NO_MOUSE_ACTION)
                self.setMouseBinding(QtCore.Qt.LeftButton,QGLViewer.CAMERA,QGLViewer.ROTATE)
                self.setMouseBinding(QtCore.Qt.RightButton,QGLViewer.CAMERA,QGLViewer.TRANSLATE)     
                self.setMouseBinding(QtCore.Qt.MiddleButton,QGLViewer.CAMERA,QGLViewer.ZOOM)     

                #self.setHandlerKeyboardModifiers(QGLViewer.FRAME, Qt.AltModifier)
                #self.setHandlerKeyboardModifiers(QGLViewer.CAMERA,  Qt.NoModifier)
                #self.setHandlerKeyboardModifiers(QGLViewer.FRAME, Qt.ControlModifier)
            self.actionTagProperty.setChecked(self.mode & self.TagProperty)
            self.actionEditScale.setChecked(self.mode & self.TagScale)

# ---------------------------- Checking ----------------------------------------   
    def check_input_points(self):
        if self.points is None : 
            QMessageBox.warning(self,'Points','No points loaded')
            return False
        return True
 
    def check_input_mtg(self):
        if self.mtg is None : 
            QMessageBox.warning(self,'MTG','No mtg loaded')            
            return False
        return True

    def check_input_data(self):
        if not self.check_input_points() : return False
        return self.check_input_mtg()



# ---------------------------- MTG edition ----------------------------------------   
     
    def removeSubtree(self):
        assert not self.selection is None
        self.createBackup()
        nid = self.selection.id
        self.showMessage("Remove subtree rooted in "+str(nid)+". Repaint.")
        self.mtg.remove_tree(nid)
        self.updateMTGView()
        self.updateGL()
    
    def removeSelection(self):
        assert not self.selection is None
        self.createBackup()
        nid = self.selection.id
        self.showMessage("Remove "+str(nid)+".")
        parent = self.mtg.parent(nid)
        for son in self.mtg.children(nid):
            self.mtg.replace_parent(son,parent)
        self.mtg.remove_vertex(nid)
        
        del self.ctrlPoints[nid]
        del self.ctrlPointsRep[self.ctrlPointsRepIndex[nid]]
        self.ctrlPointsRepIndex = dict([(sh.id,i) for i,sh in enumerate(self.ctrlPointsRep)])
        
        del self.mtgrep[self.mtgrepindex[nid]]
        self.mtgrepindex = dict([(sh.id,i) for i,sh in enumerate(self.mtgrep)])
        
        self.selection = None
        self.focus = None
        self.__update_value__(parent)
        self.updateGL()
    
    def newChild(self):
        assert not self.selection is None
        self.createBackup()
        nid = self.selection.id
        self.showMessage("Add child to "+str(nid)+".")
        positions = self.mtg.property(self.propertyposition)
        if self.mtg.parent(nid):
            l = positions[nid]-positions[self.mtg.parent(nid)]
            norml = norm(l)
        else:
            l = Vector3.OZ
            norml = 1.0
        nbchild = len(list(self.mtg.children(nid)))
        if nbchild == 0:
            npos = positions[nid]+l
            npos, nbg = self.stickPosToPoints(npos)
        elif nbchild >= 1:
            ipos = positions[nid]
            dirl = direction(l)
            dirView = toV3(self.camera().viewDirection())
            nbcandidates = 10
            candidates = [ipos + Matrix3.axisRotation(dirView,ang*2*pi/nbcandidates)*l for ang in xrange(nbcandidates)]
            ocandidates = candidates
            candidates = [self.stickPosToPoints(c)[0] for c in candidates]
            siblings = list(self.mtg.siblings(nid))+list(self.mtg.children(nid))
            if self.mtg.parent(nid):
                siblings += [self.mtg.parent(nid)]
            siblingpos = [ipos+norml*direction(positions[sib]-ipos) for sib in siblings]
            # point set at a given distance criteria
            factor1 = [abs(norm(c-ipos) - norml) for c in candidates]
            # distance to other nodes criteria
            factor2 = [sum([norm(pos-c) for pos in siblingpos]) for c in candidates]
            max1, max2 = max(factor1), max(factor2)
            cmplist = [(i,(factor1[i]/max1)+2*(1-(factor2[i]/max2))) for i in xrange(nbcandidates)]
            # self.setTempInfoDisplay(Scene([Shape(PointSet(ocandidates,width = self.pointWidth+2),Material((255,0,255))),
                                    # Shape(PointSet(candidates,width = self.pointWidth+2),Material((255,255,0))),
                                    # Shape(PointSet(siblingpos,width = self.pointWidth+8),Material((255,255,255))),
                                    # Shape(Group([Translated(ocandidates[i],Text(str(int(100*cmplist[i][1])))) for i in xrange(len(candidates))]),Material((255,255,0)))
                                    # ]))
            cmplist.sort(lambda x,y : cmp(x[1],y[1]))
            print cmplist
            npos = candidates[cmplist[0][0]]
            
        if self.mtg.is_leaf(nid):
            cid = self.mtg.add_child(nid,position=npos,edge_type='<',label='N')
        else:
            cid = self.mtg.add_child(nid,position=npos,edge_type='+',label='B')
        
        ctrlPoint = createCtrlPoint(self.mtg,cid,self.ctrlPointColor,self.propertyposition,self.__update_value__)
        self.ctrlPoints[cid] = ctrlPoint
        self.ctrlPointsRep += ctrlPoint.representation(self.ctrlPointPrimitive)
        self.ctrlPointsRepIndex[cid] = len(self.ctrlPointsRep)-1
        self.mtgrep += createEdgeRepresentation(nid,cid,positions, self.edgePlusMaterial)
        self.mtgrepindex[cid] = len(self.mtgrep)-1 
        self.setSelection(ctrlPoint)
        if self.points is None and len(self.mtg.vertices(scale=self.mtg.max_scale())) < 100:
            self.refreshView()
        self.updateGL()
        
    def splitEdge(self):
        assert not self.selection is None
        self.createBackup()
        nid = self.selection.id
        self.showMessage("Split edge before "+str(nid)+".")
        positions = self.mtg.property(self.propertyposition)
        cposition = positions[nid]
        pposition = positions[self.mtg.parent(nid)]
        newposition = (cposition+pposition)/2
        edge_type = self.mtg.edge_type(nid)
        cid = self.mtg.insert_parent(nid, edge_type = edge_type, position = newposition, label = 'N' if edge_type == '<' else 'B')
        self.mtg.property('edge_type')[nid] = '<'        
        ctrlPoint = createCtrlPoint(self.mtg,cid,self.ctrlPointColor,self.propertyposition,self.__update_value__)
        self.ctrlPoints[cid] = ctrlPoint
        self.ctrlPointsRep += ctrlPoint.representation(self.ctrlPointPrimitive)
        self.ctrlPointsRepIndex[cid] = len(self.ctrlPointsRep)-1
        self.mtgrep += createEdgeRepresentation(nid,cid,positions, self.edgePlusMaterial)
        self.mtgrepindex[cid] = len(self.mtgrep)-1 
        self.setSelection(ctrlPoint)
        self.updateGL()
        
    def beginReparentSelection(self):    
        self.setSelectionTrigger(self.endReparentSelection)
        self.setMode(self.Selection)
        self.showMessage("Select Parent")
        self.displayMessage("Select Parent",5000)
        
    def endReparentSelection(self,node):
        self.createBackup()
        nid = self.selection.id
        if node.id in mtgalgo.descendants(self.mtg,nid):
            QMessageBox.warning(self,"Invalid parent",'Cannot reparent a node with one of its descendants')
            return
        nsons = list(self.mtg.children(node.id))
        ndirectsons = [son for son in nsons if self.mtg.edge_type(son) == '<']
        
        self.mtg.replace_parent(nid,node.id)
        if len(ndirectsons) > 0:
            self.mtg.property('edge_type')[nid] = '+'
            self.mtg.property('label')[nid] = 'B'
        else:
            self.mtg.property('edge_type')[nid] = '<'
            self.mtg.property('edge_type')[nid] = 'N'
        self.showMessage("Parent selected : "+str(node.id)+".")
        self.__update_value__(nid)
        self.updateGL()
        #self.updateMTGView()
        
    def setBranchingPoint(self):
        assert not self.selection is None
        self.createBackup()
        nid = self.selection.id
        self.mtg.property('edge_type')[nid] = '+'
        self.mtg.property('label')[nid] = 'B'
        self.__update_value__(nid)
        self.updateGL()
        
    def setAxialPoint(self):
        assert not self.selection is None
        self.createBackup()
        nid = self.selection.id
        edge_type = self.mtg.property('edge_type')
        edge_type[nid] = '<'
        self.mtg.property('label')[nid] = 'N'
        siblings = self.mtg.siblings(nid)
        self.__update_value__(nid)
        for sib in siblings:
            if edge_type[sib] == '<' :
                edge_type[sib] = '+'
                self.mtg.property('label')[sib] = 'B'
                self.__update_value__(sib)
            
        self.updateGL()
        
        
    def stickPosToPoints(self, initpos):
        if not self.pointsRep : return initpos, ()
        if not self.pointsKDTree or len(self.pointsKDTree) != len(self.pointsRep[0].geometry.pointList):
            self.pointsKDTree = ANNKDTree3(self.pointsRep[0].geometry.pointList)
        
        nbg = self.pointsKDTree.k_closest_points(initpos, 5)
        newposition = centroid_of_group(self.pointsRep[0].geometry.pointList,nbg)
        return newposition, nbg
        
    def stickNodeToPoints(self, nid):        
        initpos = self.mtg.property(self.propertyposition)[nid]
        newposition, nbg = self.stickPosToPoints(initpos)
        self.ctrlPoints[nid].setPosition ( toVec(newposition) )
        self.__update_value__(nid)
        return nbg
        
    def stickToPoints(self, withupdate = True):
        assert not self.selection is None
        if not self.points: return
        nid = self.selection.id
        
        self.createBackup()
        nbg = self.stickNodeToPoints(nid)
        self.setTempInfoDisplay(Scene([Shape(PointSet(self.pointsRep[0].geometry.pointList.subset(nbg),width = self.pointWidth+2),Material((255,0,255)))]))
        self.showMessage("Stick "+str(nid)+" to points.")
        self.updateGL()
        
    def stickSubtree(self):
        assert not self.selection is None
        if not self.points: return
        nid = self.selection.id
                    
        self.createBackup()
        self.stickNodeToPoints(nid)
        nbg = []
        for ci in mtgalgo.descendants(self.mtg,nid):
            nbg += self.stickNodeToPoints(ci)
        self.setTempInfoDisplay(Scene([Shape(PointSet(self.pointsRep[0].geometry.pointList.subset(nbg),width = self.pointWidth+2),Material((255,0,255)))]))
        self.showMessage("Stick subtree of "+str(nid)+" to points.")
        self.updateGL()
        
    def revolveAroundSelection(self):
        self.camera().setRevolveAroundPoint(toVec(self.selection.position()))
        self.showMessage("Revolve around "+str(self.selection.id))
        
    def revolveAroundScene(self):
        self.camera().setRevolveAroundPoint(self.sceneCenter())
        self.showMessage("Revolve around scene center")
        
    def showMessage(self,message,timeout = 0):
        if self.statusBar:
            self.statusBar.showMessage(message,timeout)
        else:
            self.displayMessage(message,timeout)
        print message
        
# ---------------------------- Point edition ----------------------------------------   

    def reorient(self):
        if not self.check_input_points() : return

        self.points.pointList.swapCoordinates(1,2)
        if self.pointsRep[0].geometry.pointList.getPglId() != self.points.pointList.getPglId():
           self.pointsRep[0].geometry.pointList.swapCoordinates(1,2)
        self.updateGL()

    def estimateKDensity(self):
        if not self.check_input_points() : return

        kclosests = self.estimateKClosest()
        densities = densities_from_k_neighborhood(self.points.pointList, kclosests, 7)
        self.pointinfo.densities = densities

        return densities

    def estimateKClosest(self):
        if not self.check_input_points() : return

        if hasattr(self.pointinfo,'kclosests'):
            kclosests = self.pointinfo.kclosests
        else:
            kclosests = k_closest_points_from_ann(self.points.pointList, 7, True)
            kclosests = connect_all_connex_components(self.points.pointList,kclosests,True)
            self.pointinfo.kclosests = kclosests
        return kclosests

    def estimateRNeigbor(self, radius):
        if not self.check_input_points() : return

        if not hasattr(self.pointinfo, 'rnbg') or not self.pointinfo.rnbg.has_key(radius):
            kclosests = self.estimateKClosest()

            rnbgs = r_neighborhoods(self.points.pointList, kclosests, radius, True)
            if not hasattr(self.pointinfo, 'rnbg') : self.pointinfo.rnbg = dict()
            self.pointinfo.rnbg[radius] = rnbgs
        else:
            rnbgs = self.pointinfo.rnbg[radius]
        return rnbgs


    def pointDensityDisplay(self, densities):

        def get_colormap():
            try : 
                from matplotlib.cm import get_cmap
                p = get_cmap('jet')
                ncmap = [p(i) for i in xrange(p.N)]
                print 'Use matplotlib'
                return [Color4(int(round(255*r)),int(round(255*g)),int(round(255*b)),0) for r,g,b,a in ncmap ]
            except Exception, e:
                print e
                print 'use qt colormap'
                def makeColor4(h) : 
                    q = QColor()
                    q.setHsv(h,255,255)
                    return Color4(q.red(),q.green(),q.blue(),0)
                minhue, maxhue = 255, 0
                stephue = -1
                return [makeColor4(minhue+i*stephue) for i in xrange(256)]

        cmap = get_colormap()
        #cmap = list(reversed(cmap))
        #d += 1        
        #d = d.log()
        self.points.colorList = apply_colormap(cmap, densities)

        self.createPointsRepresentation()
        self.updateGL()

    def pointKDensity(self):
        from time import time
        t = time()
        densities = self.estimateKDensity()
        t = time() - t
        self.pointDensityDisplay(densities)
        self.showMessage('Density range for K=7 : '+str((min(densities), max(densities)))+'. Computed in {}'.format(t))


    def pointRDensity(self):
        mini,maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z-self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(self,'Density Radius','Select a radius of density (Pointset height : %f)' % zdist,zdist/100.,0,decimals=3)
        if ok:
            from time import time
            t = time()
            rnbgs = self.estimateRNeigbor(radius)
            densities = densities_from_k_neighborhood(self.points.pointList, rnbgs)
            t = time() - t
            self.pointinfo.densities = densities
            self.pointDensityDisplay(densities)
            self.showMessage('Density range for R='+str(radius)+' : '+str((min(densities), max(densities)))+'. Computed in {}'.format(t))

    def filterPointsMin(self):
        densityratio, ok = QInputDialog.getInt(self,'Density Ratio','Select the minimum density (percentage ratio) to select points to remove' ,5, 1, 100)
        if ok:
            if not hasattr(self.pointinfo,'densities'):
                self.estimatePointDensity()
            densities = self.pointinfo.densities
            mind, maxd = min(densities), max(densities)
            densitythreshold = mind + (maxd-mind) * densityratio / 100
            self.createPointBackup()
            nbPoints = len(self.points.pointList)
            subset = [i for i in xrange(nbPoints) if densities[i] < densitythreshold] 
            self.setPoints(PointSet(self.points.pointList.opposite_subset(subset), self.points.colorList.opposite_subset(subset)))
            self.updateGL()
            self.showMessage("Applied density filtering (d<"+str(densitythreshold)+"). Nb of points : "+str(len(self.points.pointList))+".")

    def filterPointsMax(self):
        densityratio, ok = QInputDialog.getInt(self,'Density Ratio','Select a maximum density (percentage ratio) to select points to remove' ,5, 1, 100)

        if ok:
            if not hasattr(self.pointinfo,'densities'):
                self.estimatePointDensity()
            densities = self.pointinfo.densities
            mind, maxd = min(densities), max(densities)
            densitythreshold = mind + (maxd-mind) * densityratio / 100
            self.createPointBackup()
            nbPoints = len(self.points.pointList)
            subset = [i for i in xrange(nbPoints) if densities[i] > densitythreshold] 
            self.setPoints(PointSet(self.points.pointList.opposite_subset(subset), self.points.colorList.opposite_subset(subset)))
            self.updateGL()
            self.showMessage("Applied density filtering (d>"+str(densitythreshold)+"). Nb of points : "+str(len(self.points.pointList))+".")

    def subSampling(self):
        nbPoints = len(self.points.pointList)
        ratio = 50 if nbPoints < 2000000 else 2000000./nbPoints
        pointratio, ok = QInputDialog.getInt(self,'Point Ratio','Select a percentage ratio of points to keep (Actual nb of points: %i)' % nbPoints,ratio,1,100)
        if ok:
            from random import sample
            subset = sample(xrange(nbPoints),nbPoints * pointratio / 100)
            self.createPointBackup()
            self.setPoints(PointSet(self.points.pointList.subset(subset), self.points.colorList.subset(subset)))
            self.updateGL()
            self.showMessage("Applied sub-sampling. Nb of points : "+str(len(self.points.pointList))+".")

    def euclidianContraction(self):
        mini,maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z-self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(self,'Contraction Radius','Select a radius of contraction (Pointset height : %f)' % zdist,zdist/100.,0,decimals=3)
        if ok:
            self.createPointBackup()
            from time import time
            t = time()
            self.points.pointList = contract_point3(self.points.pointList,radius)
            t = time() - t
            self.setPoints(self.points, True )
            self.updateGL()
            self.showMessage("Applied contraction in {} sec.".format(t))
        

    def riemannianContraction(self):
        mini,maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z-self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(self,'Contraction Radius','Select a radius of contraction (Pointset height : %f)' % zdist,zdist/100.,0,decimals=3)
        if ok:
            self.createPointBackup()
            from time import time
            t = time()
            rnbgs = self.estimateRNeigbor(radius)
            self.points.pointList = centroids_of_groups(points, nbgs)
            t = time() - t
            self.setPoints(self.points, True )
            self.updateGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    def laplacianContraction(self):
            self.createPointBackup()
            points = self.points.pointList
            from time import time
            t = time()
            kclosests = self.estimateKClosest()
            self.points.pointList = centroids_of_groups(points, kclosests)
            t = time() - t
            self.setPoints(self.points, True )
            self.updateGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

    def adaptiveRiemannianContraction(self):
        mini,maxi = self.points.pointList.getZMinAndMaxIndex()
        zdist = self.points.pointList[maxi].z-self.points.pointList[mini].z
        radius, ok = QInputDialog.getDouble(self,'Contraction Radius','Select a radius of contraction (Pointset height : %f)' % zdist,zdist/100.,0,decimals=3)
        if ok:
            self.createPointBackup()
            points = self.points.pointList
            kclosests = self.estimateKClosest()
            from time import time
            t = time()
            nbgs = r_neighborhoods(points, kclosests, radius)
            self.points.pointList = centroids_of_groups(points, nbgs)
            t = time() - t
            self.setPoints(self.points, True )
            self.updateGL()
            self.showMessage("Applied contraction in {} sec.".format(t))

# ---------------------------- Align ----------------------------------------   

    def applyAlignement(self, funcname, *params):
        if not self.check_input_data(): return

        print 'apply', funcname 

        self.createBackup()

        if type(funcname) == str:
            import alignement
            func = alignement.__dict__[funcname]

        if len(params):
            func(self.points.pointList, self.mtg, *params)
        else:
            func(self.points.pointList, self.mtg)

        self.__update_all_mtg__()
        self.updateGL()

    def alignGlobally(self):
        self.applyAlignement('alignGlobally')

    def alignOptimizeAll(self):
        self.applyAlignement('optimizeAlignementAll')

    def alignOptimizeOrientation(self):
        self.applyAlignement('optimizeAlignementOrientation')

    def alignOptimizePosition(self):
        mtgextent = Point3Array(self.mtg.property(self.propertyposition).values()).getExtent()
        distanceratio, ok = QInputDialog.getInt(self,'Distance Ratio','Select a percentage ratio of distance to optimize (size={})'.format(str(list(mtgextent))) ,10,1,100)
        if ok:
            self.applyAlignement('optimizeAlignementPosition', distanceratio)

    def alignScaleAndCenter(self):
        self.applyAlignement('scale_and_center')

# ---------------------------- DEBUG Information ----------------------------------------   

            
    
    def showAttractors(self):
        assert not self.selection is None
        if self.contractedpoints is None or not self.contractedpointDisplay: 
            QMessageBox.warning(self,'contracted points','No contracted points loaded OR contracted points view is disable')
            return
        if self.nodesinfo is None:
            QMessageBox.warning(self,'Note','No debug information loaded..')
            return 
        
        nid = self.selection.id
        i = self.getNodeInfoIndex(nid)
        self.cleanNodeInfo()
        
        if i:
            self.attractors = self.getAttractorSubset(self.nodesinfo[i].Attractors())
            self.attractorsRep = createAttractorsRepresentation(self.attractors, self.pointWidth, self.attractorsMaterial)
            self.printNodeInfo(i)
        else: QMessageBox.warning(self,'Note','No information of this node.')
        

# ------- Contraction ---------------------------------------- 

    def getContractParam(self):
        import contraction_ui
        from vplants.plantgl.gui.curve2deditor import FuncConstraint
        
        class ContractionDialog(QDialog, contraction_ui.Ui_Dialog) :
                def __init__(self, parent=None):
                    QDialog.__init__(self, parent)
                    contraction_ui.Ui_Dialog.__init__(self)
                    self.setupUi(self)
                    
     
        cdialog = ContractionDialog(self)
        nbN = 7
        denR = 10
        min_conR = 10
        max_conR = 25
        Rfunc = NurbsCurve2D([(0,0,1),(0.3,0.3,1),(0.7,0.7,1),(1,1,1)])
        geom_system = True 
        if hasattr(self,'cached_contraction_params'):
             nbN, denR, min_conR, max_conR, Rfunc, geom_system = self.cached_contraction_params
        
        if geom_system:
          cdialog.Z_radioButton.setChecked(True)
        else:
          cdialog.Y_radioButton.setChecked(True)
  
        cdialog.nbNeighborEditor.setValue(nbN)
        cdialog.densityRadiusEditor.setValue(denR)
        cdialog.min_contractRadiusEditor.setValue(min_conR)
        cdialog.max_contractRadiusEditor.setValue(max_conR)
        cdialog.radiusFuncEditor.pointsConstraints = FuncConstraint()
        cdialog.radiusFuncEditor.setCurve(Rfunc)
        if cdialog.exec_() == QDialog.Accepted:
            if cdialog.Y_radioButton.isChecked(): 
                geom_system = False
            elif cdialog.Z_radioButton.isChecked():
                geom_system = True
            nbN = cdialog.nbNeighborEditor.value()
            denR = cdialog.densityRadiusEditor.value()
            min_conR = cdialog.min_contractRadiusEditor.value()
            max_conR = cdialog.max_contractRadiusEditor.value()
            Rfunc = cdialog.radiusFuncEditor.getCurve()
            
            # check values
            # if 
            
            params = nbN, denR, min_conR, max_conR, Rfunc, geom_system
            self.cached_contraction_params = params 
            return params

    
    def contractPoints(self):
        if self.points is None: 
            QMessageBox.warning(self,'points','No point loaded ...')
            return
        

        from vplants.pointreconstruction.contractpoints import PointsContraction
        params = self.getContractParam()
        if not params is None:
            nbN, denR, min_conR, max_conR, Rfunc, geom_system = params
            progress = QProgressDialog(self)
            progress.setLabelText('Contraction')
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            contraction = PointsContraction(self.points.pointList, nbN, denR, min_conR, max_conR, Rfunc, geom_system)
            contractPoints = contraction.run(progress)
            self.setContractedPoints(PointSet(contractPoints))
        
        

# ---------------------------- End Contraction ----------------------------------------     



# ------- Reconstruction ---------------------------------------- 

    def getSkeletonParam(self):
        import reconstruction_ui, math
        from vplants.plantgl.gui.curve2deditor import FuncConstraint
        
        class ReconstructionDialog(QDialog, reconstruction_ui.Ui_Dialog) :
            def __init__(self, parent=None):
                QDialog.__init__(self, parent)
                reconstruction_ui.Ui_Dialog.__init__(self)
                self.setupUi(self)

        nbNeighbor = 15
        pcaRadius = 10
        min_D = 6
        max_D = 8
        Di = 2.0
        Dk = 1.2
        delta = 20
        angleratio = 2
        Rfunc = NurbsCurve2D([(0,0,1),(0.3,0.3,1),(0.7,0.7,1),(1,1,1)])
        geom_system = True 
        if hasattr(self,'cached_reconstruction_params'):
            nbNeighbor, pcaRadius, Rfunc, min_D, max_D, Di, Dk, angleratio, geom_system, delta, denthreshold = self.cached_reconstruction_params
           
        cdialog = ReconstructionDialog(self)
        if geom_system:
          cdialog.Z_radioButton.setChecked(True)
        else:
          cdialog.Y_radioButton.setChecked(True)
        cdialog.nbNeighborEditor.setValue(nbNeighbor)
        cdialog.pcaRadiusEditor.setValue(pcaRadius)
        cdialog.min_DEditor.setValue(min_D)
        cdialog.max_DEditor.setValue(max_D)
        cdialog.DiEditor.setValue(Di)
        cdialog.DkEditor.setValue(Dk)
        cdialog.deltaEditor.setValue(delta)
        cdialog.distanceFuncEditor.pointsConstraints = FuncConstraint()
        cdialog.distanceFuncEditor.setCurve(Rfunc)
        cdialog.angleSlider.setValue(angleratio)
        
        if cdialog.exec_() == QDialog.Accepted:
            if cdialog.Y_radioButton.isChecked(): 
                geom_system = False
            elif cdialog.Z_radioButton.isChecked():
                geom_system = True
            nbNeighbor = cdialog.nbNeighborEditor.value()
            pcaRadius = cdialog.pcaRadiusEditor.value()
            min_D = cdialog.min_DEditor.value()
            max_D = cdialog.max_DEditor.value()
            Di = cdialog.DiEditor.value()
            Dk = cdialog.DkEditor.value()
            angleratio = cdialog.angleSlider.value()
            Rfunc = cdialog.distanceFuncEditor.getCurve()
            delta = cdialog.deltaEditor.value()
            denthreshold = cdialog.methodSlider.value()
            self.cached_reconstruction_params = nbNeighbor, pcaRadius, Rfunc, min_D, max_D, Di, Dk, angleratio, geom_system, delta, denthreshold
            
            angle = math.pi/angleratio
            return nbNeighbor, pcaRadius, Rfunc, min_D, max_D, Di, Dk, angle, geom_system, delta, denthreshold

    
    def createSkeleton(self):
        if self.contractedpoints is None: 
            QMessageBox.warning(self,'points','No contraction point loaded ...')
            return
        
        from vplants.pointreconstruction.scaskeleton import SCASkeleton
        params = self.getSkeletonParam()
        if not params is None:
            nbN, pcaR, Rfunc, min_D, max_D, Di, Dk, angle, geom_system, delta, denthreshold = params
            progress = QProgressDialog(self)
            progress.setLabelText('Reconstruction')
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            
            skeleton = SCASkeleton(self.contractedpoints.pointList, nbN, pcaR,Rfunc, min_D, max_D, Di, Dk, angle, geom_system, delta, denthreshold)
            mtg, nodesinfo = skeleton.run(progress)
            progress.setRange(0,100)
            progress.setValue(100)
            self.setMTG(mtg,None)
            self.setNodesInfo(nodesinfo)
        

# ---------------------------- Radius Reconstruction ----------------------------------------     

    def determine_radius(self, pid):
        mtg = self.mtg

        nbgs = list(mtg.children(pid))
        if mtg.parent(pid) : nbgs.append(mtg.parent(pid))

        pos = mtg.property(self.propertyposition)
        spos = pos[pid]

        meandist = sum([norm(pos[nbg] - spos) for nbg in nbgs]) / len(nbgs)

        selection = points_at_distance_from_skeleton(self.points.pointList,[spos], [0], meandist * 0.75, 1)
        if selection:

            if mtg.parent(pid):
                    dir = spos - pos[nbgs[-1]]
            else :
                apicalchild = [vid for vid in mtg.children(pid) if mtg.edge_type(vid) == '<']
                if len(apicalchild) > 0:
                    dir = direction(Point3Array([pos[vid] - spos for vid in apicalchild]).getCenter())
                elif len(mtg.children(pid)) > 0:
                    dir = direction(Point3Array([pos[vid] - spos for vid in mtg.children(pid)]).getCenter())
                else: 
                    dir = (0,0,1)

            radius = pointset_mean_radial_distance(spos, dir, self.points.pointList, selection )
            print 'radius[',pid,']:',radius
            return radius

    def estimateRadius(self):
        assert not self.selection is None
        sid = self.selection.id

        self.mtg.property(self.propertyradius)[sid] = self.determine_radius(sid)

        self.__update_radius__(sid)
        self.updateGL()

    def estimateAllRadius(self, maxmethod=True, overwrite = True):
        assert self.mtg

        from mtgmanip import mtg2pgltree

        nodes, parents, vertex2node = mtg2pgltree(self.mtg)
        node2vertex = dict([(i,vid) for vid,i in vertex2node.items()])

        estimatedradii = estimate_radii_from_points(self.points.pointList, nodes, parents, maxmethod=maxmethod)

        radii = self.mtg.property(self.propertyradius) 
        for nid, vid in node2vertex.items():
            if not vid in radii or overwrite:
                radii[vid] = estimatedradii[nid]

        self.radiusRep, self.radiusRepIndex = createRadiiRepresentation(self.mtg, self.radiusMaterial, positionproperty= self.propertyposition, radiusproperty = self.propertyradius)
        self.updateGL()


# ---------------------------- Check MTG ----------------------------------------     
        
    def correct_labelMTG(self):
        print 'Correcting label in MTG..'
        for vtx in self.mtg.vertices(scale=self.mtg.max_scale()):
            if vtx != 2: # root node
                if self.mtg.edge_type(vtx) == '<':
                    self.mtg.property('label')[vtx] = 'N'
                elif self.mtg.edge_type(vtx) == '+':
                    self.mtg.property('label')[vtx] = 'B'
                elif self.mtg.edge_type(vtx) == '':
                    print vtx
                    if self.mtg.label(vtx) == 'N': 
                        self.mtg.property('edge_type')[vtx] = '<'
                    else: self.mtg.property('edge_type')[vtx] = '+'
                    
                child = [c for c in self.mtg.children(vtx)]
                if len(child) == 1:
                    self.mtg.property('edge_type')[child[0]] = '<'
    
    def checkMTG(self):
        self.correct_labelMTG()
        
        error_vtx=[]
        for vtx in self.mtg.vertices(scale=self.mtg.max_scale()):
            if len([i for i in self.mtg.children(vtx) if self.mtg.edge_type(i) == '<']) > 1:
                error_vtx.append(vtx)
        
        if len(error_vtx) != 0:
            print 'Multiple direct sons of some nodes of the MGT : ', error_vtx
                 
        s = []
        for ctrlPoint in self.ctrlPoints.itervalues():
            shape = ctrlPoint.representation(self.ctrlPointPrimitive)
            if shape.id in  error_vtx:
                shape.appearance.ambient = (255,0,0) #blue                
            s.append(shape)
        
        self.ctrlPointsRep = Scene(s)
        
        print 'finish check'

# ---------------------------- Root ----------------------------------------     


    def addBottomRoot(self):
        if self.points is None:
            root = Vector3(0,0,0)
        else:
            root = Vector3(self.points.pointList[self.points.pointList.getZMinIndex()])
        self.addRoot(root)

    def addTopRoot(self):
        if self.points is None:
            root = Vector3(0,0,0)
        else:
            root = Vector3(self.points.pointList[self.points.pointList.getZMaxIndex()])
        self.addRoot(root)

    def addRoot(self, position):
        import mtgmanip as mm
        self.setMTG(mm.initialize_mtg(position), None)
        self.showEntireScene()


# ---------------------------- Reconstruction ----------------------------------------     

    def xuReconstruction(self, startfrom = None):
        print 'Xu Reconstruction'
        if type(startfrom) != int:
            if not self.selection is None:
                startfrom = self.selection.id
                points = None
            else:
                vtx = list(self.mtg.vertices(self.mtg.max_scale()))
                if len(vtx) > 1 : QMessageBox.warning(self,"Root","Select a node")
                elif len(vtx) ==0 : QMessageBox.warning(self,"Root","Add a root node")
                else : startfrom = vtx[0]
                points = self.points.pointList
        else:
            return

        if hasattr(self,'defaultbinratio'):
            defaultbinratio = self.defaultbinratio
        else: defaultbinratio = 50

        binratio, ok = QInputDialog.getInt(self,'Bin Ratio','Select a bin ratio',defaultbinratio,10,1000)

        if ok:
            self.createBackup()
            self.showMessage("Apply Xu et al. reconstruction from  node "+str(startfrom)+".")
            self.defaultbinratio = binratio
            mini,maxi = self.points.pointList.getZMinAndMaxIndex()
            zdist = self.points.pointList[maxi].z-self.points.pointList[mini].z
            binlength = zdist / binratio
            verbose = False
            if points is None:
                print 'filter',len(self.points.pointList),'points with distance', binlength
                points, emptycolor = self.filter_points(PointSet(self.points.pointList),binlength)#,[startfrom])
                verbose = False
                if len(points) < 10: 
                    self.showMessage("Not enough points ("+str(len(points))+") to apply reconstruction from "+str(startfrom)+".")
                    return
            from xumethod import xu_method
            xu_method(self.mtg,startfrom,points,binlength,verbose=verbose)
            self.updateMTGView()
            self.updateGL()

    def livnyReconstruction(self, startfrom = None):
        print 'Xu Reconstruction'
        if type(startfrom) != int:
            if not self.selection is None:
                startfrom = self.selection.id
                points = None
            else:
                vtx = list(self.mtg.vertices(self.mtg.max_scale()))
                if len(vtx) > 1 : QMessageBox.warning(self,"Root","Select a node")
                elif len(vtx) ==0 : QMessageBox.warning(self,"Root","Add a root node")
                else : startfrom = vtx[0]
                points = self.points.pointList
        else:
            return

        if hasattr(self,'defaultlivnycontractionnb'):
            defaultlivnycontractionnb = self.defaultlivnycontractionnb
        else: defaultlivnycontractionnb = 3

        livnycontractionnb, ok = QInputDialog.getInt(self,'Contraction Number of Steps','Select a number of contraction step',defaultlivnycontractionnb,0,50)

        if ok:
            self.createBackup()
            self.showMessage("Apply Livny et al. reconstruction from  node "+str(startfrom)+".")
            self.defaultlivnycontractionnb = livnycontractionnb
            verbose = False
            if points is None:
                print 'filter',len(self.points.pointList),'points with distance', binlength
                points, emptycolor = self.filter_points(PointSet(self.points.pointList),binlength)#,[startfrom])
                verbose = False
                if len(points) < 10: 
                    self.showMessage("Not enough points ("+str(len(points))+") to apply reconstruction from "+str(startfrom)+".")
                    return
            from livnymethod import livny_method_mtg
            livny_method_mtg(self.mtg, startfrom, points, livnycontractionnb)
            self.updateMTGView()
            self.updateGL()
    
    def angleEstimate(self):
        from angleanalysis import lines_estimation, phylo_angles, lines_representation, write_phylo_angles
        tdegree, ok = QInputDialog.getInt(self,'Degree of trunk line','Select a degree for the trunk line estimation',1,1,5)
        if ok:
            trunk_line, lateral_lines, nodelength = lines_estimation(self.mtg,tdegree)
            print type(trunk_line), trunk_line
            if hasattr(trunk_line,'isValid') and not trunk_line.isValid():
                QMessage.error(self,'Invalid approximation','Invalid approximation')
                return
            self.setTempInfoDisplay(lines_representation(trunk_line, lateral_lines))
            self.updateGL()
            phyangles = phylo_angles(trunk_line, lateral_lines)
            self.setTempInfoDisplay(lines_representation(trunk_line, lateral_lines,phyangles))
            self.updateGL()
            fname = QFileDialog.getSaveFileName(self, "Save Angles",
                                                    'angles.txt',
                                                    "Txt Files (*.txt);;All Files (*.*)")
            if fname:
                write_phylo_angles(fname, phyangles, nodelength)

# ---------------------------- Tagging ----------------------------------------     
    
    def tagColor(self, tag):
        if tag == True:
            return self.theme['TaggedCtrlPoint']
        elif tag == False:
            return self.theme['UnTaggedCtrlPoint']
        else:
            assert tag < 0
            return self.theme['UpscaleCtrlPoint'][-1-tag]

    def tagScaleToNode(self):
        assert not self.selection is None
        sid = self.selection.id
        tagprop = self.mtg.property(self.currenttagname)
        tagvalue = tagprop.get(sid,False)
        if tagvalue in [True,False]:
            tagvalue = not tagvalue
            tagprop[sid] = tagvalue
            self.selection.color = self.tagColor(tagvalue)
            self.setSelection(None)
            self.__update_value__(sid)
            self.showMessage("Tag "+str(sid))

    def tagScale(self):
        if self.mode != self.TagScale:
            self.setMode( self.TagScale)
            self.tagScaleRepresentation()
            self.tagUpdateVisu()
            self.showMessage("Tag Scale Mode.")
        else:
            self.endTagRepresentation()
            self.setMode( self.Rotate)
        self.updateGL()

    def tagScaleRepresentation(self):
        tagprop = self.mtg.property(self.currenttagname)
        if len(tagprop) == 0:
            mscale = self.mtg.max_scale()
            for scale in xrange(1,mscale):
                for uvid in self.mtg.vertices(scale):
                    for vid in self.mtg.component_roots_at_scale(uvid, mscale):
                        if not tagprop.has_key(vid):
                            tagprop[vid] = -(mscale-scale)
        for cid, cpoint in self.ctrlPoints.items():
                tag = tagprop.get(cid,False) 
                cpoint.color = self.tagColor(tag)

    def tagUpdateVisu(self):
        self.createCtrlPointRepresentation()
        self.prevVisu = (self.pointDisplay, self.contractedpointDisplay)
        self.pointDisplay = False
        self.contractedpointDisplay = False  

    def endTagRepresentation(self):
        self.pointDisplay, self.contractedpointDisplay = self.prevVisu
        for cid, cpoint in self.ctrlPoints.items():
            cpoint.color = self.ctrlPointColor
        self.createCtrlPointRepresentation()

    def commitScale(self):
        if not len(self.mtg.property(self.currenttagname)) :
            QMessageBox.warning(self,'Data error','No tagged node to create scale.')
        
        if self.mode != self.TagScale :
            QMessageBox.warning(self,'Data error','Select Tag Scale Mode first.')
        
        default_label, ok = QInputDialog.getText(self,'Scale Label','Select a label for nodes at the new scale')
        default_label = str(default_label)
        if not ok: return
        self.createBackup()

        self.mtg.insert_scale(self.mtg.max_scale(), lambda vid : self.mtg.property(self.currenttagname).get(vid,False) != False,default_label=default_label)
        self.mtg.property(self.currenttagname).clear()
        self.showMessage("New scale "+str(self.mtg.max_scale()-1)+" commited in the MTG.")
        self.tagScaleRepresentation()
        self.createCtrlPointRepresentation()
        self.updateGL()

    def createProperty(self, vid = None):
        import propwidget_ui
        main = self

        class PDialog(QDialog):
            def __init__(self,parent):
                QDialog.__init__(self,parent)
                self.main = parent
                self.widget = propwidget_ui.Ui_Dialog()
                self.widget.setupUi(self)
                self.init(self.widget)

            def init(self, widget):
                QObject.connect(widget.actionAdd,SIGNAL('clicked()'),self.add_item)
                QObject.connect(widget.actionMinus,SIGNAL('clicked()'),self.remove_item)
                QObject.connect(widget.buttonBox,SIGNAL('accepted()'),self.commit)

            def add_item(self, propname = 'prop', value = 'value', model = None):
                if model is None: model = self.models[self.widget.tabWidget.currentIndex()]
                model.appendRow([QStandardItem(propname), QStandardItem(repr(value) if value else '')])

            def remove_item(self):
                ci = self.widget.tabWidget.currentIndex()
                mi = self.tableViews[ci].selectedIndexes()
                if mi:
                    r = mi[0].row()
                    print r
                    self.models[ci].removeRows(r,1)

            def set_properties(self, mtg, vid, model = None):
                for propname, propval in mtg.properties().items():
                    if not propval is None:
                        self.add_item(propname, propval.get(vid), model)

                for propname, propval in mtg.properties().items():
                    if propval is None:
                        self.add_item(propname, propval.get(vid), model)

            def retrieve_properties(self):
                props = dict()
                for vid, model in zip(self.vids, self.models):
                    vidprops = dict()
                    for i in xrange(self.model.rowCount()):
                        propname = self.model.item(i,0).text()
                        valuerepr = self.model.item(i,1).text()
                        if len(valuerepr) > 0:
                            try:
                                value = eval(valuerepr)
                                vidprops[propname] = value
                            except Exception, e:
                                QMessageBox.warning(self,'Data error','Error with vertex '+str(vid)+' for '+propname+'='+repr(valuerepr)+'\n'+str(e))
                                raise ValueError(e)
                        else:
                            vidprops[propname] = None
                    props[vid] = vidprops
                return props

            def apply_properties(self):
                mtg = self.main.mtg
                try:
                    props = self.retrieve_properties()
                    main.createBackup()
                    for vid, vidprop in props.items:
                        for pname, pvalue in vidprops.items():
                            if pvalue is None:
                                if mtg.property(pname).has_key(vid) : 
                                    del mtg.property(pname)[vid]
                            else:
                                mtg.property(pname)[vid] = pvalue
                        return True
                except ValueError, ve:
                    return False

            def create_tab_for_vertex(self, mtg, vid):
                newwidget = QWidget()
                gridLayout = QGridLayout(newwidget)
                newtableview = QTableView(self)
                gridLayout.addWidget(newtableview, 1, 0, 1, 5)
                newtableview.setEditTriggers(QAbstractItemView.AllEditTriggers)
                newtableview.setSortingEnabled(False)
                
                newmodel = QStandardItemModel(0, 1)
                newmodel.setHorizontalHeaderLabels(["Parameter", "Value" ])
                newtableview.setModel(newmodel)

                self.tableViews.append(newtableview)
                self.models.append(newmodel)
                self.vids.append(vid)

                self.set_properties(mtg, vid, newmodel)
                self.widget.tabWidget.addTab(newwidget, str(mtg.scale(vid))+' : '+str(vid))

            def edit(self, vid):
                self.widget.tabWidget.clear()
                self.tableViews = []
                self.models = []
                self.vids = []

                while not vid is None and vid != self.main.mtg.root:
                    self.create_tab_for_vertex(self.main.mtg, vid)
                    vid = self.main.mtg.complex(vid)

            def commit(self):
                self.widget.tableView.clearSelection()
                    
                if hasattr(self, "vids"):
                    if not self.apply_properties():
                        return

                self.accept()

        if self.propertyeditor is None:
            dialog = PDialog(self)
            self.propertyeditor = dialog

        if not vid is None:
            self.propertyeditor.edit(vid)
        self.propertyeditor.show()

    def editProperty(self):
        assert not self.selection is None
        self.createProperty(self.selection.id)

    def startTagProperty(self):
        if self.mode != self.TagProperty:
            self.createProperty()
            QObject.connect(self.propertyeditor, SIGNAL("accepted()"), self.launchTagProperty)
        else:
            self.endTagRepresentation()
            self.setMode( self.Rotate)
        self.updateGL()

    def launchTagProperty(self):
        self.setMode( self.TagProperty)
        self.propertiestotag = self.propertyeditor.retrieve_properties()
        self.tagPropertyRepresentation()
        self.tagUpdateVisu()
        self.showMessage("Tag Properties Mode.")
 
    def tagPropertyRepresentation(self):
        proptarget = self.propertyeditor.retrieve_properties()
        props = [self.mtg.property(propname) for propname in proptarget.keys()]
        mscale = self.mtg.max_scale()
        for cid, cpoint in self.ctrlPoints.items():
            tag = True
            for pvalues in props:
                if not pvalues.has_key(cid):
                    tag = False
                    break
            cpoint.color = self.tagColor(tag)

          
       
    def tagPropertyToNode(self):
        assert not self.selection is None
        sid = self.selection.id
        self.propertyeditor.apply_properties(sid)
        self.selection.color = self.tagColor(True)
        self.setSelection(None)
        self.__update_value__(sid)
        self.showMessage("Tag "+str(sid))


# ---------------------------- End Property ----------------------------------------     


    
def main():
    qapp = QApplication([])
    viewer = GLMTGEditor() #None,get_shared_data('contractdata/puu1_shortr140_n10x140.bgeom'),get_shared_data('mtgdata/puu1_attractors.mtg'))
    viewer.setWindowTitle("MTGEditor")
    viewer.show()
    qapp.exec_()

if __name__ == '__main__':
    main()
