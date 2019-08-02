# -*- coding: iso-8859-15 -*-

# Header

import os, sys
pj = os.path.join

py2exe_file = pj(os.path.dirname(__file__),'src', 'vplants', 'treeeditor3d','py2exe_release.py')
if not os.path.exists(py2exe_file):
    f = file(py2exe_file,'w')
    f.close()

##############
# Setup script

# Package name
name = 'plantscan3d'
namespace = 'vplants'
version = 0.6
pkg_name= namespace + '.' + name

print pkg_name,': version =',version

description= '3D Tree structure editor.' 
long_description= '''
An editor of 3D structure of plants and trees.
Implemented by the Virtual Plants team.'''

# Author
author= 'Frederic Boudon'
author_email= 'frederic.boudon@cirad.fr'

url= 'http://openalea.gforge.inria.fr/'

# LGPL compatible INRIA license
license= 'Cecill V2' 

# Scons build directory
build_prefix= "build-scons"


from setuptools import setup
import matplotlib

MainScript = 'src/vplants/treeeditor3d/main_window.py'

import sys
if sys.platform =='darwin':
  import py2app
  option_name = 'py2app'
  extra_options = { 'argv_emulation' : True, 
                    'compressed'     : False,
                    'optimize'       : 0,
                    # 'iconfile'       : 'lpy.icns',
                    'excludes' : [],
                    }
  builderoptions = {'app' : [MainScript]}
  build_prefix = 'build-scons'
else:
  import py2exe
  import zmq
  os.environ["PATH"] = os.environ["PATH"] + os.path.pathsep + os.path.split(zmq.__file__)[0]
  
  option_name = 'py2exe'
  #extra_options =  { "dll_excludes" : ['MSVCP80.dll','MSVCR80.dll'] }
  extra_options = {"includes": ["zmq.utils", "zmq.utils.jsonapi",  "zmq.utils.strtypes"],
                    'dll_excludes': ['libgdk-win32-2.0-0.dll',
                                         'libgobject-2.0-0.dll',
                                         'libgdk_pixbuf-2.0-0.dll',
                                         'libgtk-win32-2.0-0.dll',
                                         'libglib-2.0-0.dll',
                                         'libcairo-2.dll',
                                         'libpango-1.0-0.dll',
                                         'libpangowin32-1.0-0.dll',
                                         'libpangocairo-1.0-0.dll',
                                         'libglade-2.0-0.dll',
                                         'libgmodule-2.0-0.dll',
                                         'libgthread-2.0-0.dll',
                                        ]}
  builderoptions = {'windows' : [{'script' : MainScript, 
                                 #'icon_resources' : [(1, "src/openalea/lpy/gui/logo.ico")]
                                 'options' : {"py2exe": {"includes":["sip"]}},
                                 }] }
  build_prefix = ''

import glob
from os.path import splitext,basename,abspath


                                     

goptions = { option_name : 
                {
                    #'packages' : ['sip','stat','PyQt4', 'distutils', 'ctypes', 'random', 'IPython', 'pygments', 'PIL','PyOpenGL']
                    'packages' : [ 'sip', 'vplants.treeeditor3d','openalea.plantgl', 'openalea.mtg','PyQt4','openalea.core','OpenGL',  'scipy', 'scipy.interpolate', 'scipy.interpolate._interpolate', 'scipy.special', 'scipy.sparse','matplotlib', 'six']

                }
            }
goptions[option_name].update(extra_options)
print goptions

pgl_dir = 'C:/Python27/Lib/site-packages/VPlants.PlantGL-2.20.0-py2.7-win32.egg/'
libdirs = pj(pgl_dir,'lib')
pgl_py = pj(pgl_dir,'openalea/plantgl')
#libdirs = pj('../vplants/PlantGL',build_prefix,'lib')

import openalea.plantgl as pgl
pgl_pys = pgl.__path__

import modulefinder
for p in   pgl.__path__:
    modulefinder.AddPackagePath('openalea',abspath(pj(p,'..')))

import openalea.mtg as mtg
for p in   mtg.__path__:
    modulefinder.AddPackagePath('openalea',abspath(pj(p,'..')))

import openalea.vpltk as mtg
for p in   mtg.__path__:
    modulefinder.AddPackagePath('openalea',abspath(pj(p,'..')))

import openalea
for p in   openalea.__path__:
    modulefinder.AddPackagePath('openalea',p)

pgl_py = pgl_pys[0]
if len(pgl_pys) > 1:
    pgl_dir = pj(pgl_py,'..','..')
    pgl_dir = abspath(pgl_dir)
    libdirs = pj(pgl_dir,'build-scons','lib')
else:
    pgl_dir = pj(pgl_py,'..','..')
    pgl_dir = abspath(pgl_dir)
    libdirs = pj(pgl_dir,'lib')

    
print pgl_py
print libdirs

setup(
    name="PlantScan3D",
    version=version,
    description=description,
    long_description=long_description,
    author=author,
    author_email=author_email,
    url=url,
    license=license,
    
    #scons_scripts = ['SConstruct'],
    #scons_parameters = ["build_prefix="+build_prefix],
    
    namespace_packages = [namespace],
    create_namespaces = True,
    
    # pure python  packages
    packages = [  'vplants.treeeditor3d'],
    #py_modules = ['lpygui_postinstall'],

    # python packages directory
    package_dir = { '' : 'src', 
                    'vplants.treeeditor3d' : 'src/vplants/treeeditor3d', 
                    #'openalea.plantgl' : pgl_py
                    },
                   
    # Add package platform libraries if any
    include_package_data = True,
    package_data = {'' : ['*.pyd', '*.so', '*.lpy', '*.dylib'],},
    zip_safe = False,

    # Specific options of openalea.deploy
    #lib_dirs = { 'lib' : libdirs},
    #inc_dirs = {'include' : pj(build_prefix, 'include') },
    share_dirs = {'share' : 'data', },
    data_files=matplotlib.get_py2exe_datafiles(),
    
    # Dependencies
    setup_requires = ['openalea.deploy'],
    dependency_links = ['http://openalea.gforge.inria.fr/pi'],

    # py2exe or py2app options
    options=goptions,

    **builderoptions

    )

if  os.path.exists(py2exe_file):
    os.remove(py2exe_file)
    py2exe_cfile = py2exe_file.replace('.py','.pyc')
    if  os.path.exists(py2exe_cfile):
        os.remove(py2exe_cfile)
