from openalea.plantgl.all import *

def xu_method(pointList,root, binlength, k = 20):
    skeleton = skeleton_from_distance_to_root_clusters(pointList,root,binlength,k, connect_all_points=True, verbose=True)

    return skeleton      