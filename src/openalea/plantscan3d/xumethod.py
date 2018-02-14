from openalea.plantgl.all import *
from mtgmanip import pgltree2mtg

def xu_method(mtg, startfrom, pointList, binlength, k = 20, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    rootpos = Vector3(mtg.property('position')[startfrom])
    root = len(pointList)
    connect_all_points = False if mtg.nb_vertices(mtg.max_scale()) > 1 else True
    pointList.append(rootpos)
    positions, parents, pointcomponents = skeleton_from_distance_to_root_clusters(pointList,root,binlength,k, connect_all_points=connect_all_points, verbose=True)
    del pointList[root]

    pgltree2mtg(mtg, startfrom, parents, positions, None, filter_short_branch, angle_between_trunk_and_lateral)

    return mtg

def graphcolonization_method(mtg, startfrom, pointList, densities, minbinlength, maxbinlength, binlengthfunc, k = 20, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    rootpos = Vector3(mtg.property('position')[startfrom])
    root = len(pointList)
    connect_all_points = False if mtg.nb_vertices(mtg.max_scale()) > 1 else True
    pointList.append(rootpos)

    kclosests = k_closest_points_from_ann(pointList, k, True)
    kclosests = connect_all_connex_components(pointList, kclosests,True)

    mindensity, maxdensity = densities.getMinAndMax()
    deltadensity = maxdensity - mindensity 
    binlengthfunc.clamped = False
    normeddensity = lambda x : binlengthfunc(abs(x - mindensity)/deltadensity)

    deltabinlength = maxbinlength-minbinlength
    binlength = lambda x: minbinlength + deltabinlength * normeddensity(x)

    class CustomSCA(GraphColonization):
        def __init__(self, *args):
            GraphColonization.__init__(self,*args)
            self.use_jonction_points = True
          
        def node_buds_preprocess(self,nid):
              #print 'node_buds_preprocess', nid
              pos = self.node_position(nid)
              components = self.node_components(nid)
              # print nid, self.parents[nid], pos, components
              
              self.grid.enable_points(components)
              aid = self.grid.closest_point(pos)
              self.grid.disable_points(components)
              adensity  = densities[aid]

              l = binlength(adensity)
              self.setLengths(l)

    sc = GraphColonization(pointList, maxbinlength, kclosests, root)
    sc.run()
    
    nodes = sc.nodes
    parents = sc.parents

    del pointList[root]

    pgltree2mtg(mtg, startfrom, parents, nodes, None, filter_short_branch, angle_between_trunk_and_lateral)

    return mtg    