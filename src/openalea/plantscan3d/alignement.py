
def scale_and_center(points, mtg):
    import openalea.plantgl.all  as pgl

    if type(mtg) != pgl.Point3Array:
        mtgpoints = pgl.Point3Array(list(mtg.property('position').values()))
    else:
        mtgpoints = mtg

    pointextent = pgl.norm(points.getExtent())
    mtgextent   = pgl.norm(mtgpoints.getExtent())
    scaleratio  = mtgextent / pointextent

    m_center = mtgpoints.getCenter()
    p_center = points.getCenter()

    from math import log
    scale = 1./pow(10, round(log(scaleratio,10)))

    def transform(v):
        return ((v - m_center) * scale) + p_center

    npos1 = dict([(vid, transform(pos)) for vid, pos in list(mtg.property('position').items())])
    mtg.property('position').update(npos1)


def alignGlobally(points, mtg, verbose = False):
    import openalea.plantgl.all  as pgl
    import numpy as np
    from .pointprocessing import np_inertia_axis

    mtgpoints = pgl.Point3Array(list(mtg.property('position').values()))


    axispoints = np_inertia_axis(points,    verbose=verbose)
    axismtg    = np_inertia_axis(mtgpoints, verbose=verbose)

    p_eval, p_edir, p_center = axispoints
    m_eval, m_edir, m_center = axismtg

    pointextent = pgl.norm(points.getExtent())
    mtgextent   = pgl.norm(mtgpoints.getExtent())
    scaleratio  = mtgextent / pointextent

    from math import log
    scale = 1./pow(10, round(log(scaleratio,10)))

    normalizeorientation = True
    checkorientation = True


    if normalizeorientation:
            def normalize_frame(edir):
                a, b = edir[0], edir[1]
                c = np.cross(a,b)
                return np.array([a, np.cross(c,a), c])

            p_edir = normalize_frame(p_edir)
            m_edir = normalize_frame(m_edir)

    if verbose:
        print('Point center :', p_center)
        print('MTG center   :', m_center)
        print('Point axis   :',p_edir)
        print('MTG axis     :',m_edir)
        print('Point variance :',p_eval)
        print('MTG variance :',m_eval)

    def transform(v,t_edir):
        v = (v - m_center) 
        nval = [ pgl.dot(v,ed) for ed in m_edir]
        nv = sum([val * ed for val, ed in zip(nval, t_edir)],pgl.Vector3(0,0,0))
        return (nv + p_center)

    ppos = mtg.property('position').copy()

    npos1 = dict([(vid, transform(pos, p_edir)) for vid, pos in list(ppos.items())])
    #npos1 = dict([(vid, pos*scale) for vid, pos in ppos.items()])
    mtg.property('position').update(npos1)

    if checkorientation:
        if verbose: print('check orientation')
        from .mtgmanip import mtg2pgltree
        nodes, parents, vertex2node = mtg2pgltree(mtg)
        dist1 = pgl.average_distance_to_shape(points, nodes, parents, [0 for i in range(len(nodes))])
    
        if verbose: print('check flipped orientation')
        p_edir2 = np.array([-p_edir[0], -p_edir[1], np.cross(-p_edir[0], -p_edir[1])])
        npos2 = dict([(vid, transform(pos, p_edir2)) for vid, pos in list(ppos.items())])
        mtg.property('position').update(npos2)

        nodes, parents, vertex2node = mtg2pgltree(mtg)
        dist2 = pgl.average_distance_to_shape(points, nodes, parents, [0 for i in range(len(nodes))])

        if verbose: print(dist1, dist2)
        if dist1 < dist2:
            if verbose: print('Use first orientation')
            mtg.property('position').update(npos1)
        else:
            if verbose: print('Use flipped orientation')


def optimizeAlignementOrientation(points, mtg, p_edir = None):
    from .mtgmanip import mtg2pgltree
    import openalea.plantgl.all  as pgl
    from .pointprocessing import np_inertia_axis
    from math import pi, degrees

    nodes, parents, vertex2node = mtg2pgltree(mtg)
    dist = pgl.average_distance_to_shape(points, nodes, parents, [0 for i in range(len(nodes))])
    print(dist)

    if p_edir is None:
        p_eval, p_edir, p_center  = np_inertia_axis(points)

    nbtest = 72
    rotangle = 2*pi/nbtest
    tangle = 0

    def check_rot_angle(crotangle, dist, tangle):
        print('test rotation of',degrees(crotangle),':', end=' ')
        m = pgl.Matrix3.axisRotation(p_edir[0],crotangle)
        nnodes = [m*p for p in nodes]
        ndist = pgl.average_distance_to_shape(points, nnodes, parents, [0 for j in range(len(nodes))])
        print(ndist)
        if ndist < dist:
            tangle = crotangle
            dist = ndist
        return dist, tangle

    for i in range(1,nbtest):
        crotangle = rotangle*i
        dist, tangle = check_rot_angle(crotangle, dist, tangle)

    nbtest = 10
    rotangle = 2 * rotangle / nbtest
    gtangle = tangle
    for i in range(1,nbtest/2):
        crotangle = gtangle - rotangle*i
        dist, tangle = check_rot_angle(crotangle, dist, tangle)
    for i in range(1,nbtest/2):
        crotangle = gtangle + rotangle*i
        dist, tangle = check_rot_angle(crotangle, dist, tangle)

    if tangle != 0:
        print('select', degrees(tangle), dist)
        npos = dict()
        m = pgl.Matrix3.axisRotation(p_edir[0],tangle)
        for vid, pos in list(mtg.property('position').items()):
            npos[vid] = m * pos
        mtg.property('position').update(npos)
        #nodes = [m*p for p in nodes]



def optimizeAlignementPosition(points, mtg, distanceratio = 10, nbtests = 10, p_edir = None):
    from .mtgmanip import mtg2pgltree
    import openalea.plantgl.all  as pgl
    from .pointprocessing import np_inertia_axis
    from math import pi, degrees

    nodes, parents, vertex2node = mtg2pgltree(mtg)
    dist = pgl.average_distance_to_shape(points, nodes, parents, [0 for i in range(len(nodes))])
    print(dist)

    if p_edir is None:
        p_eval, p_edir, p_center  = np_inertia_axis(points)

    
    mtgextent = pgl.Point3Array(list(mtg.property('position').values())).getExtent()

    def test_shift(cshift, dist, tshift):
        print('test shift of',cshift,':', end=' ')
        nnodes = [p + cshift for p in nodes]
        ndist = pgl.average_distance_to_shape(points, nnodes, parents, [0 for j in range(len(nodes))])
        print(ndist)
        if ndist < dist:
            tshift = cshift
            dist = ndist
        return dist, tshift

    for i in range(3):
        tshift = None
        unitshift = mtgextent[i]  * distanceratio / 1000.
        for t in range(1, nbtests):
            cshift = p_edir[i]*t*unitshift
            dist, tshift = test_shift(cshift, dist, tshift)

        for t in range(1, nbtests):
            cshift = -p_edir[i]*t*unitshift
            dist, tshift = test_shift(cshift, dist, tshift)

        if not tshift is None:
            print('select', tshift, dist)
            npos = dict()
            for vid, pos in list(mtg.property('position').items()):
                npos[vid] = pos + tshift
            mtg.property('position').update(npos)


def optimizeAlignementAll(points, mtg):
    from .pointprocessing import np_inertia_axis
    scale_and_center(points, mtg)
    p_eval, p_edir, p_center  = np_inertia_axis(points)
    optimizeAlignementOrientation(points, mtg, p_edir)
    optimizeAlignementPosition(points, mtg, p_edir=p_edir)
