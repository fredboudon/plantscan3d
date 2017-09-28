from openalea.plantgl.all import *

def filter(points, densityfilterratio = 0.05, densityradius = None,  k = 15):
    # Determine default value of radius for density estimation
    if densityradius is None:
        mini,maxi = points.getZMinAndMaxIndex()
        zdist = points[maxi].z-points[mini].z
        densityradius = zdist/100.
    # Connect all points to k closest neighbors
    kclosests = k_closest_points_from_ann(points, k, True)
    kclosests = connect_all_connex_components(points,kclosests,True)
    # Determine the neighbors in a radius
    rnbgs = r_neighborhoods(points, kclosests, densityradius, True)
    # Estimate densities
    densities = densities_from_r_neighborhood(rnbgs, densityradius)
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
    import vplants.treeeditor3d.mtgmanip as mm
    from vplants.treeeditor3d.xumethod import xu_method
    import vplants.treeeditor3d.serial as serial


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
