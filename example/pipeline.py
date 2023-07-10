from openalea.plantgl.all import *
import numpy as np
import os

class Line:
    def __init__(self, position, direction, extend):
        self.position = position
        self.direction = direction
        self.extend = extend
    def __repr__(self):
        return 'Line('+str(self.position)+','+str(self.direction)+','+str(self.extend)+')'
    
    @staticmethod
    def estimate(positions):
        idx = range(len(positions))
        pos = centroid_of_group(positions, idx)
        dir = direction(pointset_orientation(positions,idx))
        if dot(pos-positions[0],dir) < 0: dir *= -1
        extend = max([abs(dot(p-pos,dir)) for p in positions])
        return Line(pos,dir,extend)

def load_points(filename):
    # Check if file exists
    assert os.path.exists(filename)
    s = Scene(filename)
    # Check if pointList is on the loaded file
    assert len(s) == 1
    points = s[0].geometry.geometry.pointList
    #points.translate(s[0].geometry.translation)
    return points


def subsample(points, ptsnb):
    from random import sample
    nbPoints = len(points)
    subset = sample(range(nbPoints), ptsnb)
    return points.subset(subset)

# Reconstrution of the mtg

def filter_points(points, densityfilterratio = 0.05, #densityradius = None,  
                  k = 16):
    # Determine default value of radius for density estimation
    #if densityradius is None:
    #    mini,maxi = points.getZMinAndMaxIndex()
    #    zdist = points[maxi].z-points[mini].z
    #    densityradius = zdist/100.
    # Connect all points to k closest neighbors
    kclosests = k_closest_points_from_ann(points, k, True)
    kclosests = connect_all_connex_components(points,kclosests,True)
    # Determine the neighbors in a radius
    #rnbgs = r_neighborhoods(points, kclosests, densityradius, True)
    # Estimate densities
    densities = densities_from_k_neighborhood(points, kclosests, k)
    # Determine value of density under which we filter
    mind, maxd = densities.getMinAndMax(True)
    densitythreshold = mind + (maxd-mind) * densityfilterratio
    # Determine index of points to filter
    nbPoints = len(points)
    subset = [i for i in range(nbPoints) if densities[i] < densitythreshold]
    # Return result
    return points.opposite_subset(subset)

try:
    import mtgmanip as mm
    from xumethod import xu_method
    import serial
except ImportError as ie:
    import openalea.plantscan3d.mtgmanip as mm
    from openalea.plantscan3d.xumethod import xu_method
    import openalea.plantscan3d.serial as serial

def find_root(points):
    center = points.getCenter()
    pminid,pmaxid = points.getZMinAndMaxIndex()
    zmin = points[pminid].z
    zmax = points[pmaxid].z
    initp = center
    initp.z = zmin
    return points.findClosest(initp)[0], zmin, zmax


def skeleton(points, binratio = 50, k = 20):

    root, zmin, zmax = find_root(points)

    mtg = mm.initialize_mtg(root)
    zdist = zmax-zmin
    binlength = zdist / binratio

    vtx = list(mtg.vertices(mtg.max_scale()))
    startfrom = vtx[0]
    mtg = xu_method(mtg, startfrom, points, binlength, k)

    return mtg

def determine_radius(mtg, points, meanmethod=True, radiusproperty = 'radius'):
    nodes, parents, vertex2node = mm.mtg2pgltree(mtg)

    estimatedradii = estimate_radii_from_points(points, nodes, parents, maxmethod = not meanmethod)

    radii = mtg.property(radiusproperty)
    for vid, nid in vertex2node.items():
        radii[vid] = estimatedradii[nid]

# Navigation in the mtg

def node_position(g,n):
    if 'position' in g.property_names():
        return g.property('position')[n]
    return np.array([g.property('XX')[n], g.property('YY')[n], g.property('ZZ')[n]])

def node_length(g,n):
    from numpy.linalg import norm
    parent = g.parent(n)
    if parent:
        p1 = node_position(g,n)
        p0 = node_position(g,parent)
        return norm(p1-p0)
    else:
        return 0
   
def node_angle(g, n, refdir = (0,0,1) ):
    parent = g.parent(n)
    if parent:
        p1 = node_position(g,n)
        p0 = node_position(g,parent)
        return angle(p1-p0, refdir)
    else:
        return 0
    
def axis_extremities_angle(g, n, refdir = (0,0,1) ):
    p0, p1 = axis_extremities(g,n)
    return angle(p1 - p0, refdir)

   
def length_to_axis_begin(g, n):
    length = node_length(g,n)
    while g.edge_type(n) == '<':
        n = g.parent(n)
        length += node_length(g,n)
    return length

def axis_extremities(g,n):
    axis = g.Axis(n)
    p1 = node_position(g,axis[-1])
    a0 = axis[0]
    if g.parent(a0):
        a0 = g.parent(a0)
    p0 = node_position(g,a0)    
    return p0, p1

# Axis characterization

def horizontalangle(direction):
    from math import degrees
    from numpy.linalg import norm
    refdir = np.array([direction[0],direction[1],0])
    return angle(direction, refdir)
 
def angle(direction, refdir = (0,0,1)):
    from math import degrees
    from numpy.linalg import norm
    cosinus = np.dot(direction,refdir)
    vy = np.cross(direction,refdir)
    sinus = norm(vy)
    return degrees(np.math.atan2(sinus, cosinus))
 

def axis_chord_length(g, n):
    from numpy.linalg import norm
    p0, p1 = axis_extremities(g,n)
    return norm(p1-p0)

def axis_length(g, n):
    return sum(map(lambda vid : node_length(g,vid),g.Axis(n)))

def axis_nodes_normedposition(g, axisroot):
    data = [(node,node_length(g,node)) for node in g.Axis(axisroot)]
    length = 0
    for i in range(len(data)):
        length += data[i][1]      
        data[i] = (data[i][0],length)
    res = [(node,l/length) for node,l in data]
    if not g.parent(axisroot) is None:
        res = [(g.parent(axisroot),0)]+res
    return res

def axis_subpart(g, axisroot, beglengthratio, endlengthratio):
    data = axis_nodes_normedposition(g, axisroot)
    beg = 0
    end = len(data)-1
    while data[beg][1] < beglengthratio:
        if beg+1 == end or data[beg+1][1] >= endlengthratio: 
            break
        else:
            beg += 1
    while data[end][1] > endlengthratio:
        if end-1 == beg or data[end-1][1] <= beglengthratio: 
            break
        else:
            end -= 1
    return  [node for node,l in data[beg:end+1]]

def axis_subpart_angle(g, axisroot, beglengthratio, endlengthratio, refdir = (0,0,1) ):
    nodes = axis_subpart(g,axisroot,beglengthratio,endlengthratio)
    positions = [node_position(g, n) for n in nodes]
    if len(positions) > 2:
        return angle(Line.estimate(positions).direction, refdir)
    return angle(positions[1] - positions[0], refdir)


def axis_length_distribution(g):
    axislengths = []
    for node in g.vertices(scale=g.max_scale()):
        apical_child = [n for n in g.children(node) if g.edge_type(n) == '<']
        if len(apical_child) == 0 : # We look for end of branch nodes i.e. with no apical child
            axislengths.append(length_to_axis_begin(g, node))
    return axislengths

def axis_length_histogram(g):
    from matplotlib.pyplot import hist, show
    dist = axis_length_distribution(g)
    hist(dist, bins=np.arange(0, max(dist), 0.2))
    show()

# Trunk Characterization

def trunk_root(g):
    return g.roots(scale=g.max_scale())[0]

def trunk_length(g):
    return axis_length(g,trunk_root(g))

def trunk_nodes(g):
    return g.Axis(trunk_root(g))

def trunk_direction(g, trunkratio = 1):
    nodes = axis_subpart(g, trunk_root(g), 0, trunkratio)
    positions = [node_position(g, v) for v in nodes]
    line = Line.estimate(positions)
    return line.direction
    
def lateral_children(g, vid):
    return [cid for cid in g.children(vid) if g.edge_type(cid) == '+']

def nb_lateral_children(g, vid):
    return sum(lateral_children(g, vid))

def trunk_branching_zone_start(g):
    trunknodes = trunk_nodes(g)
    firstidpos = None
    for i,vid in enumerate(trunknodes):
        if nb_lateral_children(g,vid) > 0:
            firstidpos = i
            break
    if firstidpos is None:
        return None
    trunknodes = trunknodes[:firstidpos+1]
    return sum([node_length(g,n) for n in trunknodes])

def trunk_branching_zone_end(g):
    trunknodes = trunk_nodes(g)
    
    lastidpos = None
    for i,vid in enumerate(reversed(trunknodes)):
        if nb_lateral_children(g, vid) > 0:
            lastidpos = i
            break
    if lastidpos is None:
        return None
    trunknodes = trunknodes[:-lastidpos]    
    return sum([node_length(g,n) for n in trunknodes])

def trunk_branching_zone_length(g):
    trunknodes = trunk_nodes(g)
    firstidpos = None
    for i,vid in enumerate(trunknodes):
        if nb_lateral_children(g,vid) > 0:
            firstidpos = i
            break
    if firstidpos is None:
        return None
    trunknodes = trunknodes[firstidpos+1:]
    lastidpos = None
    for i,vid in enumerate(reversed(trunknodes)):
        if nb_lateral_children(g, vid) > 0:
            lastidpos = i
            break
    if lastidpos is None:
        return 0
    trunknodes = trunknodes[:-lastidpos]
    
    return sum([node_length(g,n) for n in trunknodes])

# First order characterization

def trunk_lateral_axes(g, length_threshold = 0.05):
    trunknodes = trunk_nodes(g)
    shortaxis, longaxis = [],[]
    for n in trunknodes:
        for l in lateral_children(g,n):
            if axis_length(g,l) >= length_threshold:
                longaxis.append(l)
            else:
                shortaxis.append(l)
    return shortaxis, longaxis

def length_first_order(g):
    shortaxis, longaxis = trunk_lateral_axes(g)
    return [axis_length(g,l) for l in longaxis]

def chord_length_first_order(g):
    shortaxis, longaxis = trunk_lateral_axes(g)
    return [axis_chord_length(g,l) for l in longaxis]

def angles_first_order(g):
    shortaxis, longaxis = trunk_lateral_axes(g)
    return [node_angle(g,l) for l in longaxis]

def trunk_radii(g, begratio = 0.1, endratio = 0.1 ):
    begtrunk = axis_subpart(g, trunk_root(g), 0, begratio)
    endtrunk = axis_subpart(g, trunk_root(g), 1-endratio, 1)
    radii = g.property('radius')
    return max([radii[n] for n in begtrunk]), max([radii[n] for n in endtrunk])

def retrieve_axis_radii(g,vid):
    radii = g.property('radius')
    axis = g.Axis(vid)
    axis = [vid for vid in axis if vid in radii]
    nbnodes = len(axis)
    if nbnodes == 0:
        return None, None, None
    elif nbnodes == 1:
        r = radii[axis[0]]
        return r,r,r
    elif nbnodes == 2:
        r0 = radii[axis[0]]
        r1 = radii[axis[1]]
        return r0,(r0+r1)/2,r1
    elif nbnodes == 3:
        r0 = radii[axis[0]]
        r1 = radii[axis[1]]
        r2 = radii[axis[2]]
        return r0,r2,r1
    else:
        radius = lambda v : radii[v]
        lradii = list(map(radius,axis))
        lradii.sort()
        meanradius = lradii[int(len(lradii)/2)] 
        return (radii[axis[0]],
                meanradius,
                radii[axis[-2]])