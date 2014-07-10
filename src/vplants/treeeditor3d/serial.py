# -*- coding: utf-8 -*-
from openalea.plantgl.all import *
from openalea.plantgl.codec.asc import *
from openalea.mtg.io import *
import cPickle as pickle



def getpointset(fn):
    scene = Scene(fn)
    points = scene[0].geometry.geometry.pointList
    tr = scene[0].geometry.translation
    return points, tr

def quantisefunc(fn=None, qfunc=None):
    if fn: s = Scene(fn)
    else : s = Scene([qfunc])
    curve = s[0].geometry
    curve = curve.deepcopy()
    
    return QuantisedFunction(curve) 
    
def writefile(fn, obj):
    f = open(fn,'wb')
    pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    f.close()
    
def readfile(fn, mode='rb'):
    f = open(fn,mode)
    obj = pickle.load(f)
    f.close()
    return obj

    
def writeAscPoints(fn, points):
    scene = Scene([Shape(PointSet(points), Material(ambient=(0,0,0)))])
    AscCodec().write(fn, scene)
  
def writeXYZ(fn, points):
    space = ' '
    newline = '\n'
    f = open(fn, 'w')
  
    s = str()
    for p in points:
        s += str(p.x) + space + str(p.y) + space + str(p.z) + newline
    
    f.write(s)
    f.close()
    
def writeMTGfile(fn, g, properties=[('XX','REAL'), ('YY','REAL'), ('ZZ','REAL'), ('radius','REAL')], nb_tab=20):
    
    if properties == []:
      properties = [(p, 'REAL') for p in g.property_names() if p not in ['edge_type', 'index', 'label']]
    str = write_mtg(g, properties, nb_tab=nb_tab)
    f = open(fn, 'w')
    f.write(str)
    f.close()
  

def convertToStdMTG(g):
  from copy import deepcopy
  newg = deepcopy(g)
  
  pdic = newg.property('position')
  xx = {}
  yy = {}
  zz = {}
  
  for i,v in pdic.iteritems():
      xx[i] = v.x
      yy[i] = v.y
      zz[i] = v.z
  
  newg.add_property('XX')
  newg.add_property('YY')
  newg.add_property('ZZ')
  newg.property('XX').update(xx)
  newg.property('YY').update(yy)
  newg.property('ZZ').update(zz)
  del newg.properties()['position']
  return newg


def convertToMyMTG(g):
  from openalea.mtg import MTG
  
  def addProperties(mtg, vid, px, py, pz, radius):
      mtg.property('position')[vid] = Vector3(px,py,pz)
      mtg.property('radius')[vid] = radius
      
  mtg = MTG()
  mtg.add_property('position')
  mtg.add_property('radius')
    
  plantroot = mtg.root
  branchroot = mtg.add_component(plantroot,label='B')
  noderoot = mtg.add_component(branchroot,label='N')
  
  rdic = g.property('radius')
  
  for k,r in rdic.iteritems():
    parentid = g.parent(k)
    px = g.property('XX')[k]
    py = g.property('YY')[k]
    pz = g.property('ZZ')[k]
    
    if parentid == None:
      addProperties(mtg, k, px, py, pz, r)
    else:
      label = g.label(k)
      if label == 'N':
        vid = mtg.add_child(parentid,edge_type='<',label='N')
      else:
        vid = mtg.add_child(parentid,edge_type='+',label='B')
        
      addProperties(mtg, vid, px, py, pz, r)
    
  return mtg
  
  
  