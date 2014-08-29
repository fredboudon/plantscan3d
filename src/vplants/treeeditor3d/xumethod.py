from openalea.plantgl.all import *
from math import degrees, acos

def xu_method(mtg, startfrom, pointList, binlength, k = 20,verbose=False, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    rootpos = Vector3(mtg.property('position')[startfrom])
    if verbose: print startfrom, rootpos
    root = len(pointList)
    connect_all_points = False if mtg.nb_vertices(mtg.max_scale()) > 1 else True
    pointList.append(rootpos)
    positions, parents, pointcomponents = skeleton_from_distance_to_root_clusters(pointList,root,binlength,k, connect_all_points=connect_all_points, verbose=True)
    del pointList[root]



 

    children, root = determine_children(parents)
    clength = subtrees_size(children,root)

    node2skel = {}
    assert parents[0] == 0
    if verbose: print positions[0], mtg.property('position')[startfrom]
    if norm(positions[0]-rootpos) > 1e-3:
        startfrom = mtg.add_child(parent=startfrom,position=positions[0])
    node2skel[0] = startfrom

    # for node, parent in enumerate(parents[1:len(parents)]):
    #     if verbose: print node, parent, node2skel.get(parent)
    #     ni = mtg.add_child(parent=node2skel[parent],position=positions[node+1])
    #     node2skel[node+1] = ni

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
        mtgnode = mtg.add_child(parent = parent, label='N',edge_type = edge_type, position = pos)
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