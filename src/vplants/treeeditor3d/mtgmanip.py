

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