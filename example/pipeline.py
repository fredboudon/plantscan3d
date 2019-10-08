from openalea.plantgl.all import *
import numpy as np


def load_points(filename):
    s = Scene(filename)
    points = s[0].geometry.geometry.pointList
    return points


def subsample(points, ptsnb):
    from random import sample
    nbPoints = len(points)
    subset = sample(xrange(nbPoints), ptsnb)
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
    subset = [i for i in xrange(nbPoints) if densities[i] < densitythreshold]
    # Return result
    return points.opposite_subset(subset)

try:
    import mtgmanip as mm
    from xumethod import xu_method
    import serial
except ImportError, ie:
    import openalea.plantscan3d.mtgmanip as mm
    from openalea.plantscan3d.xumethod import xu_method
    import openalea.plantscan3d.serial as serial


def skeleton(points, binratio = 50, k = 20):

    mini,maxi = points.getZMinAndMaxIndex()
    root = Vector3(points[mini]) 

    mtg = mm.initialize_mtg(root)
    zdist = points[maxi].z-points[mini].z
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
   
def node_angle(g, n ):
    from numpy.linalg import norm
    parent = g.parent(n)
    if parent:
        p1 = node_position(g,n)
        p0 = node_position(g,parent)
        return horizontalangle(p0,p1)
    else:
        return 0
    
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

def horizontalangle(p1, p2):
    from math import degrees
    from numpy.linalg import norm
    direction = p1-p2
    refdir = np.array([direction[0],direction[1],0])
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

def trunk_length(g):
    rootpoint = g.roots(scale=g.max_scale())[0]
    return axis_length(g,rootpoint)

def trunk_nodes(g):
    rootpoint = g.roots(scale=g.max_scale())[0]
    return g.Axis(rootpoint)
    
def lateral_children(g, vid):
    return [cid for cid in g.children(vid) if g.edge_type(cid) == '+']

def nb_lateral_children(g, vid):
    return sum(lateral_children(g, vid))

def trunk_branching_zone_start(g):
    trunknode = trunk_nodes(g)
    firstidpos = None
    for i,vid in enumerate(trunknode):
        if nb_lateral_children(g,vid) > 0:
            firstidpos = i
            break
            
    trunknode = trunknode[:firstidpos+1]
    return sum([node_length(g,n) for n in trunknode])

def trunk_branching_zone_end(g):
    trunknode = trunk_nodes(g)
    
    lastidpos = None
    for i,vid in enumerate(reversed(trunknode)):
        if nb_lateral_children(g, vid) > 0:
            lastidpos = i
            break
    trunknode = trunknode[:-lastidpos]    
    return sum([node_length(g,n) for n in trunknode])

def trunk_branching_zone_length(g):
    trunknode = trunk_nodes(g)
    
    firstidpos = None
    for i,vid in enumerate(trunknode):
        if nb_lateral_children(g,vid) > 0:
            firstidpos = i
            break
    trunknode = trunknode[firstidpos+1:]
    lastidpos = None
    for i,vid in enumerate(reversed(trunknode)):
        if nb_lateral_children(g, vid) > 0:
            lastidpos = i
            break
    trunknode = trunknode[:-lastidpos]
    
    return sum([node_length(g,n) for n in trunknode])

# First order characterization

def trunk_lateral_axes(g, length_threshold = 0.05):
    trunknode = trunk_nodes(g)
    shortaxis, longaxis = [],[]
    for n in trunknode:
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

