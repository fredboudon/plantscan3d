

def alignGlobally(points, mtg):
    import openalea.plantgl.all  as pgl
    import numpy as np
    from pointprocessing import np_inertia_axis

    mtgpoints = pgl.Point3Array(mtg.property('position').values())


    axispoints = np_inertia_axis(points)
    axismtg    = np_inertia_axis(mtgpoints)

    p_eval, p_edir, p_center = axispoints
    m_eval, m_edir, m_center = axismtg

    pointextent = pgl.norm(points.getExtent())
    mtgextent = pgl.norm(mtgpoints.getExtent())
    scaleratio = mtgextent / pointextent

    from math import log
    scale = 1./pow(10, round(log(scaleratio,10)))

    checkorientation = False
    if checkorientation:
        if np.dot(np.cross(p_edir[1],p_edir[2]), p_edir[0]) < 0:
            p_edir = np.array([-p_edir[0], p_edir[1], p_edir[2]])
        if np.dot(np.cross(m_edir[1],m_edir[2]), m_edir[0]) < 0:
            m_edir = np.array([-m_edir[0], m_edir[1], m_edir[2]])

        a = np.dot(mtg.property('position')[mtg.component_roots_at_scale(mtg.root,mtg.max_scale())[0]]-m_center, m_edir[0])
        print a
        if a > 0 :
            m_edir = np.array([-m_edir[0], -m_edir[1], m_edir[2]])

        print 'find orientation of scan', p_edir[0]
        npoints = pgl.Point3Array(points)
        npoints.directional_sort(p_edir[0])
        nbpoints = len(npoints)
        conspoints = max(nbpoints*5/100,10)
        c1, r1 = pgl.pointset_circle(npoints,range(conspoints,2*conspoints),p_edir[0])
        c2, r2 = pgl.pointset_circle(npoints,range(nbpoints-2*conspoints,nbpoints-conspoints),p_edir[0])
        print r1, r2
        print np.dot(npoints[0],p_edir[0]) , np.dot(npoints[-1],p_edir[0])
        if r1 > r2:
            print 'inverse scan'
            p_edir = np.array([-p_edir[0], -p_edir[1], p_edir[2]])

    def transform(v):
        v = v - m_center
        nval = [np.dot(v,ed) for ed in m_edir]
        nv = sum([val * scale * ed for val,ed in zip(nval, p_edir)],pgl.Vector3())
        return nv + p_center

    print 'Point center :', p_center
    print 'Point axis   :',p_edir, p_eval
    print 'MTG center   :', m_center
    print 'MTG axis     :',m_edir, m_eval
    print 'scale ratio  :',scaleratio, scale


    npos = dict([(vid, transform(pos)) for vid, pos in mtg.property('position').items()])
    mtg.property('position').update(npos)


def optimizeAlignementOrientation(points, mtg, p_edir = None):
    from mtgmanip import mtg2pgltree
    import openalea.plantgl.all  as pgl
    from pointprocessing import np_inertia_axis
    from math import pi, degrees

    nodes, parents, vertex2node = mtg2pgltree(mtg)
    dist = pgl.average_distance_to_shape(points, nodes, parents, [0 for i in xrange(len(nodes))])
    print dist

    if p_edir is None:
        p_eval, p_edir, p_center  = np_inertia_axis(points)

    nbtest = 72
    rotangle = 2*pi/nbtest
    tangle = 0

    def check_rot_angle(crotangle, dist, tangle):
        print 'test rotation of',degrees(crotangle),':',
        m = pgl.Matrix3.axisRotation(p_edir[0],crotangle)
        nnodes = [m*p for p in nodes]
        ndist = pgl.average_distance_to_shape(points, nnodes, parents, [0 for j in xrange(len(nodes))])
        print ndist
        if ndist < dist:
            tangle = crotangle
            dist = ndist
        return dist, tangle

    for i in xrange(1,nbtest):
        crotangle = rotangle*i
        dist, tangle = check_rot_angle(crotangle, dist, tangle)
    if tangle != 0:
        nbtest = 10
        rotangle = 2 * rotangle / nbtest
        gtangle = tangle
        for i in xrange(1,nbtest/2):
            crotangle = gtangle - rotangle*i
            dist, tangle = check_rot_angle(crotangle, dist, tangle)
        for i in xrange(1,nbtest/2):
            crotangle = gtangle + rotangle*i
            dist, tangle = check_rot_angle(crotangle, dist, tangle)

    if tangle != 0:
        print 'select', degrees(tangle), dist
        npos = dict()
        m = pgl.Matrix3.axisRotation(p_edir[0],tangle)
        for vid, pos in mtg.property('position').items():
            npos[vid] = m * pos
        mtg.property('position').update(npos)
        #nodes = [m*p for p in nodes]



def optimizeAlignementPosition(points, mtg, nbtests = 10, p_edir = None):
    from mtgmanip import mtg2pgltree
    import openalea.plantgl.all  as pgl
    from pointprocessing import np_inertia_axis
    from math import pi, degrees

    nodes, parents, vertex2node = mtg2pgltree(mtg)
    dist = pgl.average_distance_to_shape(points, nodes, parents, [0 for i in xrange(len(nodes))])
    print dist

    if p_edir is None:
        p_eval, p_edir, p_center  = np_inertia_axis(points)

    
    mtgextent = pgl.Point3Array(mtg.property('position').values()).getExtent()

    def test_shift(cshift, dist, tshift):
        print 'test shift of',cshift,':',
        nnodes = [p + cshift for p in nodes]
        ndist = pgl.average_distance_to_shape(points, nnodes, parents, [0 for j in xrange(len(nodes))])
        print ndist
        if ndist < dist:
            tshift = cshift
            dist = ndist
        return dist, tshift

    for i in xrange(3):
        tshift = None
        unitshift = mtgextent[i] / 100.
        for t in xrange(1, nbtests):
            cshift = p_edir[i]*t*unitshift
            dist, tshift = test_shift(cshift, dist, tshift)

        for t in xrange(1, nbtests):
            cshift = -p_edir[i]*t*unitshift
            dist, tshift = test_shift(cshift, dist, tshift)

        if not tshift is None:
            print 'select', tshift, dist
            npos = dict()
            for vid, pos in mtg.property('position').items():
                npos[vid] = pos + tshift
            mtg.property('position').update(npos)


def optimizeAlignementAll(points, mtg):
    from pointprocessing import np_inertia_axis
    p_eval, p_edir, p_center  = np_inertia_axis(points)
    optimizeAlignementOrientation(points, mtg, p_edir)
    optimizeAlignementPosition(points, mtg, p_edir=p_edir)
