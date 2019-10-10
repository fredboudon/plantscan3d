from os.path import join as pj

def get_shared_data(file, share_path='data'):
    try:
        from openalea.deploy.shared_data import get_shared_data_path
        import openalea.plantscan3d as ted
        shared_data_path = get_shared_data_path(ted.__path__, share_path=share_path)
        return pj(shared_data_path, file)
    except:
        import os
        return os.getcwd()
   

def get_shared_mtg(file):
    from os.path import join
    return get_shared_data(file,share_path=join('data','mtgdata'))