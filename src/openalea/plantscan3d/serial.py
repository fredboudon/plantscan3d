# -*- coding: utf-8 -*-
from openalea.plantgl.all import *
from openalea.plantgl.codec.asc import *
from openalea.mtg.io import *



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
    
    
import pickle as pickle
def readfile(fn, mode='rb'):
    f = open(fn,mode)
    obj = pickle.load(f)
    f.close()
    return obj

def writefile(fn, obj):
    f = open(fn,'wb')
    pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)
    f.close()

    
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
  
  for i,v in pdic.items():
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


def convertToMyMTG(mtg):
    from copy import deepcopy
    g = deepcopy(mtg)

    position = {}

    XXpropname = 'XX' if 'XX' in g.properties() else 'X'
    YYpropname = 'YY' if 'YY' in g.properties() else 'Y'
    ZZpropname = 'ZZ' if 'ZZ' in g.properties() else 'Z'

    XX = g.property(XXpropname)
    YY = g.property(YYpropname)
    ZZ = g.property(ZZpropname)    

    for i,x in XX.items():
        position[i] = Vector3(x,YY[i],ZZ[i])

    for propname in [XXpropname, YYpropname, ZZpropname]:
        del g.properties()[propname]

    mtg.property('position').update(position)
    
    return mtg

def complete_lines(mtg):
    lines = mtg.property('_line')
    nlines = dict(lines)
    for vid, line in list(lines.items()):
        while mtg.parent(vid) and lines.get(mtg.parent(vid)) == None:              
            vid = mtg.parent(vid)
            nlines[vid] = line
    lines.update(nlines)

  
from openalea.plantgl.all import *
def convertStdMTGWithNode(g, useHeuristic = True, 
                             invertCoord = False, 
                             propagate_parent = False):

    from openalea.mtg import MTG

    XXpropname = 'XX' if 'XX' in g.properties() else 'X'
    YYpropname = 'YY' if 'YY' in g.properties() else 'Y'
    ZZpropname = 'ZZ' if 'ZZ' in g.properties() else 'Z'

    XX = g.property(XXpropname)
    YY = g.property(YYpropname)
    ZZ = g.property(ZZpropname)

    lines = g.property('_line')
    complete_lines(g)

    positions = dict()

    scale = g.max_scale()
    dointerpolation = False

    def toVector3(vtx): return Vector3(XX[vtx],YY[vtx], -ZZ[vtx] if invertCoord else ZZ[vtx])

    for vtx in g.vertices(scale):
        v = None
        if vtx in XX:
            v = toVector3(vtx)
            positions[vtx] = v

        for i in range(scale+1, 0, -1):
            cpx = g.complex_at_scale(vtx, scale=i)
            if vtx in g.component_roots_at_scale(cpx, scale=scale) and cpx in XX:
                v = toVector3(cpx)
                parent =  g.parent(vtx)
                if (g.edge_type(vtx) == '+') and (not parent in XX) and (len(g.children(parent)) == 1 or propagate_parent):
                    positions[parent] = v
                else:
                    positions[vtx] = v
                    

    notpositionned =  set(g.vertices(scale)) - set(positions.keys())
    if len(notpositionned) > 0:
        print('interpolate positions')
        positionned = list(positions.keys())

        components = dict()
        cparent = dict()
        for vtx in positionned:
            ancestors = g.Ancestors(vtx, EdgeType = '<')
            if len(ancestors) == 0: continue
            if ancestors[0] == vtx: ancestors.pop(0)
            if len(ancestors) == 0: continue

            if g.parent(ancestors[-1]):
                ancestors.append(g.parent(ancestors[-1]))
            if g.parent(ancestors[-1]):
                ancestors.append(g.parent(ancestors[-1]))

            for i,p in enumerate(ancestors):
                if p in positions:
                    break
            else:
                continue
                i = None

            posi = positions[vtx]            
            if not i is None:
                axe = ancestors[:i]
                posj = positions[ancestors[i]]
                cparent[vtx] = ancestors[i]
            else:
                axe = ancestors
                posj = None
                cparent[vtx] = ancestors[-1]

            components[vtx] = (posi, posj, axe)

        a = [(vtx, lines[vtx], info[2]) for vtx, info in list(components.items())]
        a.sort(key=lambda v:v[1])

        for vtx, info in list(components.items()):
            posi, posj, axe = info
            nbseg = len(axe)+1

            for i,v in enumerate(axe,1):
                positions[v] = posi * ((nbseg-i)/float(nbseg)) + posj * (i/float(nbseg))


    notpositionned =  set(g.vertices(scale)) - set(positions.keys())
    #print notpositionned
    #print [g.property('_line').get(vid) for vid in notpositionned]
    if len(notpositionned) > 0 and useHeuristic:
        print('use heuristic for', list(notpositionned))
        groups = []
        while len(notpositionned) > 0:
            seed = notpositionned.pop()
            group = [seed]
            p = g.parent(seed)
            while p in notpositionned:
                notpositionned.discard(p)
                group.insert(0,p)
            c = seed
            while True:
                ch = g.children(c)
                if len(ch) > 1:
                    raise ValueError('Cannot determine coordinates for branch starting at:'+str(seed)+' at lines '+str(lines.get(seed)))
                if len(ch) == 1:
                    c = ch[0]
                    #assert c in notpositionned
                    if not c in notpositionned: break
                    notpositionned.discard(c)
                    group.append(c)
                else: break
            groups.append(group)
        for group in groups:
            p = g.parent(group[0])
            initpos = positions[p]
            parentdir = initpos - positions[g.parent(p)]
            length = parentdir.normalize()
            latdir = parentdir.anOrthogonalVector()
            for i,vid in enumerate(group,1):
                positions[vid] = initpos + i * length * latdir

    if 'Diameter' in g.property_names():
        g.property('radius').update(dict([(vid,d/2.) for vid,d in list(g.property('Diameter').items())]))
    g.property('position').update(positions)



