from openalea.plantgl.all import *
import pipeline as pp

def points_to_scene(points):
    pset = PointSet(points)
    pset.colorList = generate_point_color(pset)
    return Scene([pset])


def view_points(points):
    view(points_to_scene(points))

def to_image(sc):
    try:
        z = ZBufferEngine(800,800, (255,255,255), eColorBased)
        
        bbx = BoundingBox(sc)
        xmin = bbx.lowerLeftCorner.x
        xmax = bbx.upperRightCorner.x
        center = bbx.getCenter()
        size = bbx.getSize()
        msize = max(size[1],size[2])*1.05
        dist = 1

        z.setOrthographicCamera(-msize, msize, -msize, msize, dist,dist+xmax-xmin)
        position = (xmax+dist,center[1],center[2])
        z.lookAt(position,center,(0,0,1))

        z.process(sc)

        i = z.getImage()
        return i.to_array()
    except:
        pass

def view(sc):
    img = to_image(sc)
    if not img is None:
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 9))
        ax.imshow(img)
        plt.show()    

def nodemtg_to_scene(mtg, segment_inf_color = (0, 0, 0),
                      segment_plus_color = (200, 200, 0),
                      node_color = (0,200,0),
                      node_size = 5,
                      segment_size = 2,
                      positionproperty='position'):

    def createEdgeRepresentation(begnode, endnode, positions, material):
        res = Polyline([positions[begnode], positions[endnode]], width=segment_size)
        return Shape(res, material, endnode)

    scene = Scene()
    positions = mtg.property(positionproperty)
    r = set(mtg.component_roots_at_scale(mtg.root, scale=mtg.max_scale()))

    def choose_mat(mtg, nid):
        return Material(segment_inf_color) if mtg.edge_type(nid) == '<' else Material(segment_plus_color)

    l =   [createEdgeRepresentation(mtg.parent(nodeID), nodeID, positions, choose_mat(mtg, nodeID)) for nodeID in mtg.vertices(scale=mtg.max_scale()) if not nodeID in r]
    l.append(Shape(PointSet([mtg.property(positionproperty)[nodeID] for nodeID in mtg.vertices(scale=mtg.max_scale())], width=node_size), Material(node_color)))
    scene = Scene(l)

    return scene

def mtg_to_scene(mtg, positionproperty='position', radiusproperty = 'radius'):
    scene = Scene()
    section = Polyline2D.Circle(1, 30)
    shortaxis, longaxis = pp.trunk_lateral_axes(mtg)

    def get_radius(nodeid):
        val = mtg.property(radiusproperty).get(nodeid, 0)
        if val is None: val = 0
        return (val, val)

    defaultmat = Material((128, 64, 0))
    defaultshmat = Material((60, 60, 60))
    for vid in mtg.vertices(scale=mtg.max_scale()):
        if mtg.parent(vid) is None or mtg.edge_type(vid) == "+":
            axe = mtg.Axis(vid)
            if not mtg.parent(vid) is None: 
                axe.insert(0, mtg.parent(vid))
            mat = defaultmat
            if vid in shortaxis:
                mat = defaultshmat
            if len(axe) > 2:
                points = [mtg.property(positionproperty)[nodeID] for nodeID in axe]
                radius = [get_radius(nodeID) for nodeID in axe]
                geometry = Extrusion(Polyline(points), section, radius)
                scene += Shape(geometry, mat, vid)

    return scene    
