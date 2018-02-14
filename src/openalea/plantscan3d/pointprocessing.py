
def  np_inertia_axis(points, verbose = False):
    assert len(points) > 0
    import numpy as np
    import openalea.plantgl.all as pgl
    if type(points) != pgl.Point3Array:
        points = pgl.Point3Array(points)

    if verbose: print 'centering points'
    center = points.getCenter()
    npoints = pgl.Point3Array(points)
    if pgl.norm(center) < 1e-5:
        npoints.translate(- center)

    if verbose: print 'compute covariance'
    # compute 1/N*P.P^T
    #cov = 1./len(points)*np.dot(npoints.T,npoints)
    cov = pgl.pointset_covariance(npoints)
    cov = np.array([cov.getRow(i) for i in xrange(3)])
    if verbose: print cov

    if verbose: print "compute eigen vectors"
    # Find the eigen values and vectors.
    eig_val, eig_vec = np.linalg.eig(cov)

    if verbose: 
        for i in xrange(3):
            print eig_val[i], eig_vec[:,i]

    eig_vec = np.array(eig_vec).T

    eig_vec = np.array([eig_vec[i] for i in reversed(pgl.get_sorted_element_order(eig_val))])
    eig_val = np.array([eig_val[i] for i in reversed(pgl.get_sorted_element_order(eig_val))])

    return eig_val, eig_vec, center

def  pgl_inertia_axis(points):
    import openalea.plantgl.all as pgl
    if type(points) != pgl.Point3Array:
        points = pgl.Point3Array(points)
    center = points.getCenter()
    u,v,w,s = pgl.Fit.inertiaAxis(points)
    return s, [u,v,w], center

def inertia_axis(points):
    return np_inertia_axis(points)