

def initialize_mtg(root):
    from openalea.mtg import MTG
    mtg = MTG()
    plantroot = mtg.root
    branchroot = mtg.add_component(plantroot,label='B')
    noderoot = mtg.add_component(branchroot,label='N')
    mtg.property('position')[noderoot] = root  
    mtg.property('radius')[noderoot] = 0   
    assert len(mtg.property('position')) == 1
    return mtg

def mtg2pgltree(mtg):
    vertices = mtg.vertices(scale = mtg.max_scale())
    vertex2node = dict([(vid,i) for i,vid in enumerate(vertices)])
    positions = mtg.property('position')
    nodes = [positions[vid] for vid in vertices]
    parents = [vertex2node[mtg.parent(vid)] if mtg.parent(vid) else vertex2node[vid] for vid in vertices]
    return nodes, parents, vertex2node

from openalea.plantgl.all import *

def pgltree2mtg(mtg, startfrom, parents, positions, radii = None, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    from math import degrees, acos

    rootpos = Vector3(mtg.property('position')[startfrom])
    if norm(positions[0]-rootpos) > 1e-3:
        startfrom = mtg.add_child(parent=startfrom,position=positions[0])

    children, root = determine_children(parents)
    clength = subtrees_size(children,root)

    mchildren = list(children[root])
    npositions = mtg.property('position')
    removed = [] 
    if len(mchildren) >= 2 and filter_short_branch:
        mchildren = [c for c in mchildren if len(children[c]) > 0]
        if len(mchildren) != len(children[root]): 
            removed = list(set(children[root])-set(mchildren))

    mchildren.sort(lambda x,y : -cmp(clength[x],clength[y]))
    toprocess = [(c,startfrom,'<' if i == 0 else '+') for i,c in enumerate(mchildren)]
    while len(toprocess) > 0:
        nid, parent, edge_type = toprocess.pop(0)
        pos = positions[nid]
        parameters = dict(parent = parent, label='N', edge_type = edge_type, position = pos)
        if radii :
            parameters['radius'] = radii[nid]
        mtgnode = mtg.add_child(**parameters)
        mchildren = list(children[nid])
        if len(mchildren) > 0:
            if len(mchildren) >= 2 and filter_short_branch:
                mchildren = [c for c in mchildren if len(children[c]) > 0]
                if len(mchildren) != len(children[nid]): 
                    removed = list(set(children[nid])-set(mchildren))
            if len(mchildren) > 0:
                mchildren.sort(lambda x,y : -cmp(clength[x],clength[y]))
                first_edge_type = '<'
                langle = degrees(acos(dot(direction(pos-npositions[parent]),direction(positions[mchildren[0]]-pos))))
                if langle > angle_between_trunk_and_lateral:
                    first_edge_type = '+'
                edges_types = [first_edge_type]+['+' for i in xrange(len(mchildren)-1)]
                toprocess += [(c,mtgnode,e) for c,e in zip(mchildren,edges_types)]
    print 'Remove short nodes ',','.join(map(str,removed))
    return mtg

def gaussian_weight(x,var): 
    from math import exp, sqrt, pi
    return exp(-x**2/(2*var))/sqrt(2*pi*var*var)

def gaussian_filter(mtg, propname, considerapicalonly = True):
    prop = mtg.property(propname)
    nprop = dict()
    gw0 = gaussian_weight(0,1)
    gw1 = gaussian_weight(1,1)
    for vid, value in prop.items():
        nvalues = [value*gw0]
        parent   = mtg.parent(vid)
        if parent and prop.has_key(parent):
            nvalues.append(prop[parent]*gw1)
        children = mtg.children(vid)
        if considerapicalonly: children = [child for child in children if mtg.edge_type(child) == '<']
        for child in children:
            if child in prop:
                nvalues.append(prop[child]*gw1)

        nvalue = sum(nvalues[1:],nvalues[0]) / sum([gw0 + (len(nvalues)-1)*gw1])
        nprop[vid] = nvalue

    prop.update(nprop)


def threshold_filter(mtg, propname):
    from openalea.mtg.traversal import iter_mtg2

    prop = mtg.property(propname)
    nprop = dict()
    for vid in iter_mtg2(mtg, mtg.root):
        if vid in prop:
            parent   = mtg.parent(vid)
            if parent and parent in prop:
                pvalue = nprop.get(parent,prop[parent])
                if pvalue  < prop[vid]:            
                    nprop[vid] = pvalue

    prop.update(nprop)
