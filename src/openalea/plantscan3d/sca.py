from openalea.plantgl.all import *
from .mtgmanip import pgltree2mtg

def adaptivespacecolonization_method(mtg, startfrom, pointList, densities, mingrowthlength, maxgrowthlength, growthlengthfunc, killradiusratio, perceptionradiusratio, min_nb_pt_per_bud, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    rootpos = Vector3(mtg.property('position')[startfrom])

    mindensity, maxdensity = densities.getMinAndMax()
    deltadensity = maxdensity - mindensity
    growthlengthfunc.clamped = False
    normeddensity = lambda x : growthlengthfunc(abs(x - mindensity)/deltadensity)

    deltabinlength = maxgrowthlength-mingrowthlength
    binlength = lambda x: mingrowthlength + deltabinlength * normeddensity(x) 

    print(maxgrowthlength, maxgrowthlength*killradiusratio, maxgrowthlength*perceptionradiusratio)

    class CustomSCA(SpaceColonization):
        def __init__(self, *args):
            SpaceColonization.__init__(self,*args)
          
        def node_buds_preprocess(self,nid):
              pos = self.node_position(nid)
              components = self.node_attractors(nid)
              # print nid, self.parents[nid], pos, components
              aid, aidist = findClosestFromSubset(pos, pointList, components)
              adensity  = densities[aid]

              l = binlength(adensity)
              assert l >= mingrowthlength
              self.setLengths(l,killradiusratio,perceptionradiusratio)

    sc = CustomSCA(pointList, maxgrowthlength, maxgrowthlength*killradiusratio, maxgrowthlength*perceptionradiusratio, rootpos)
    sc.min_nb_pt_per_bud = min_nb_pt_per_bud
    sc.run()
    
    nodes = sc.nodes
    parents = sc.parents

    pgltree2mtg(mtg, startfrom, parents, nodes, None, filter_short_branch, angle_between_trunk_and_lateral)

    return mtg    

def spacecolonization_method(mtg, startfrom, pointList, growthlength, killradiusratio, perceptionradiusratio, min_nb_pt_per_bud, filter_short_branch = False, angle_between_trunk_and_lateral = 60):
    rootpos = Vector3(mtg.property('position')[startfrom])

    sc = SpaceColonization(pointList, growthlength, growthlength*killradiusratio, growthlength*perceptionradiusratio, rootpos)
    sc.min_nb_pt_per_bud = min_nb_pt_per_bud
    sc.run()
    
    nodes = sc.nodes
    parents = sc.parents

    pgltree2mtg(mtg, startfrom, parents, nodes, None, filter_short_branch, angle_between_trunk_and_lateral)

    return mtg    