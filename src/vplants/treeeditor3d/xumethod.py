from openalea.plantgl.all import *
from mtgmanip import pgltree2mtg

def xu_method(mtg, startfrom, pointList, binlength, k = 20,verbose=False, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    rootpos = Vector3(mtg.property('position')[startfrom])
    if verbose: print startfrom, rootpos
    root = len(pointList)
    connect_all_points = False if mtg.nb_vertices(mtg.max_scale()) > 1 else True
    pointList.append(rootpos)
    positions, parents, pointcomponents = skeleton_from_distance_to_root_clusters(pointList,root,binlength,k, connect_all_points=connect_all_points, verbose=True)
    del pointList[root]

    pgltree2mtg(mtg, startfrom, parents, positions, None, filter_short_branch, angle_between_trunk_and_lateral)

    return mtg