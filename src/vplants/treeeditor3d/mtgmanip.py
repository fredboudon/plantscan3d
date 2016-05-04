

def initialize_mtg(root):
    from openalea.mtg import MTG
    mtg = MTG()
    plantroot = mtg.root
    branchroot = mtg.add_component(plantroot,label='B')
    noderoot = mtg.add_component(branchroot,label='N')
    mtg.property('position')[noderoot] = root  
    mtg.property('radius')[noderoot] = 0   
    assert len(mtg.property('position')) == 1
    return mtg

def mtg2pgltree(mtg):
    vertices = mtg.vertices(scale = mtg.max_scale())
    vertex2node = dict([(vid,i) for i,vid in enumerate(vertices)])
    positions = mtg.property('position')
    nodes = [positions[vid] for vid in vertices]
    parents = [vertex2node[mtg.parent(vid)] if mtg.parent(vid) else vid for vid in vertices]
    return nodes, parents, vertex2node