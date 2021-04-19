from math import *
from openalea.plantgl.all import *


class Line:
    def __init__(self, pos, dir, extend):
        self.pos = pos
        self.dir = dir
        self.extend = extend
    def __repr__(self):
        return 'Line('+str(self.pos)+','+str(self.dir)+','+str(self.extend)+')'
    
    @staticmethod
    def estimate(positions, nodes):
        lpoints = [positions[n] for n in nodes]
        idx = list(range(len(nodes)))
        pos = centroid_of_group(lpoints,idx)
        dir = direction(pointset_orientation(lpoints,idx))
        if dot(pos-positions[nodes[0]],dir) < 0: dir *= -1
        extend = max([abs(dot(p-pos,dir)) for p in lpoints])
        return Line(pos,dir,extend)

def NurbsEstimate(positions, nodes, degree):
    from scipy.interpolate import splprep
    lpoints = [positions[n] for n in nodes]
    x,y,z = [[p[i] for p in lpoints] for i in range(3)]
    tck,u = splprep([x,y,z],k=degree)
    t,c,k = tck
    return NurbsCurve(ctrlPointList = Point4Array([(x,y,z,1) for x,y,z in zip(c[0],c[1],c[2])]),degree=k,knotList=t )   

def NurbsEstimate0(positions, nodes, degree):
    lpoints = [positions[n] for n in nodes]
    print(lpoints)
    curve = Fit.nurbsCurve(lpoints, degree, len(lpoints)/10)
    return curve

def lines_estimation(mtg, degree = 1):
    r = mtg.roots(scale=mtg.max_scale())[0]
    positions = mtg.property('position')
    trunk_nodes = mtg.Axis(r)
    if degree > 1:
        trunk_line = NurbsEstimate(positions,trunk_nodes,degree)
    else:
        trunk_line = Line.estimate(positions,trunk_nodes)
    lateral_roots = sum([[n for n in mtg.children(i) if mtg.edge_type(n) == '+'] for i in trunk_nodes],[])
    lateral_lines = [Line.estimate(positions,mtg.Axis(lr))  for lr in lateral_roots]
    nodelength = [norm(positions[mtg.parent(lateral_roots[i])]-positions[mtg.parent(lateral_roots[i+1])]) for i in range(len(lateral_roots)-1)]
    
    return trunk_line, lateral_lines, nodelength

def get_ref_dir(trunkdir):
    return  cross(Vector3.OY,trunkdir) 

def lines_representation(trunk, branches, phylo_angles = None, trunk_color = (255,0,255), result_color = (255,0,0), reference_bar_color = (255,0,255)):
    # for l in lines: print l
    sc = Scene()
    if isinstance(trunk,Line):
        refdir = get_ref_dir(trunk.dir)
        rootpos = trunk.pos-trunk.dir*trunk.extend
        sc += Shape(Polyline([rootpos,trunk.pos+trunk.dir*trunk.extend],width=3),Material(trunk_color),id=0)
        sc += Shape(Polyline([rootpos,rootpos+refdir*trunk.extend/5],width=2),Material(reference_bar_color),id=0)
    else:
        refdir = get_ref_dir(direction(trunk.getTangentAt(0)))
        rootpos = trunk.getPointAt(0)
        trunk.width=3
        sc += Shape(trunk,Material(trunk_color),id=0)
        sc += Shape(Polyline([rootpos,rootpos+refdir*trunk.getLength()/5],width=2),Material(reference_bar_color),id=0)
    for i,l in enumerate(branches):
        sc += Shape(Polyline([l.pos-l.dir*l.extend,l.pos+l.dir*l.extend],width=3),Material(result_color),id=i+1)
        if phylo_angles:
            sc += Shape(Translated(l.pos+l.dir*l.extend,Text('%.2f' %phylo_angles[i])),Material(result_color),id=i+1)

    return sc
        
def phylo_angles(trunk, branches):
    def mangle(d,rd,td):
        a = angle(d,rd,td)
        da = degrees(a)
        return da

    if isinstance(trunk,Line):
        trunkdir = trunk.dir
        refdir = get_ref_dir(trunkdir) 
        print('Angle taken from initial direction', refdir,'rotating around', trunkdir)
        return [mangle(l.dir,refdir,trunkdir) for l in branches]
    else:
        result = []
        for l in branches:
            initpos = l.pos-l.dir*l.extend
            cp, u = trunk.findClosest(initpos)
            trunkdir = trunk.getTangentAt(u)
            refdir = get_ref_dir(trunkdir)
            result.append(mangle(l.dir,refdir,trunkdir))
        return result

def relative_angles(angles,ccw=True):
    lastangle = angles[0]
    relangles = []
    for a in angles[1:]:
        if ccw :
            while a < lastangle:
                a += 360
            ra = a-lastangle
        else:
            while a > lastangle:
                a -= 360
            ra = lastangle-a            
        relangles.append(ra)
        lastangle = a
    return relangles
    
def write_phylo_angles(output_phy,phyangles,nodelength,sep='\t'):
    f = open(output_phy,'w')
    f.write('Absolute'+sep+'Relative (CCW)'+sep+'Relative (CW)'+sep+'NodeLength'+'\n')
    f.write(str(phyangles[0])+sep+sep+sep+'\n')
    for data in zip(phyangles[1:],relative_angles(phyangles),relative_angles(phyangles,False),nodelength):
        f.write(sep.join(map(str,data)))
        f.write('\n')
    f.close()
 