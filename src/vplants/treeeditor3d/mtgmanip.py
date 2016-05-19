

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
    parents = [vertex2node[mtg.parent(vid)] if mtg.parent(vid) else vid for vid in vertices]
    return nodes, parents, vertex2node

from openalea.plantgl.all import *

def pgltree2mtg(mtg, startfrom, parents, positions, radii = dict(), filter_short_branch = False, angle_between_trunk_and_lateral = 60):
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
        mtgnode = mtg.add_child(parent = parent, label='N',edge_type = edge_type, position = pos, radius = radii.get(nid))
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