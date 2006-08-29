import os, sys
from os.path import join, exists, isdir, isfile, dirname, abspath, expanduser

from defs import *

UNINSTALLED_LAB = False
def _check (path):
    return exists(path) and isdir(path) and isfile(path+"/AUTHORS")
    
name = join (dirname (__file__), '..')
if _check (name):
    UNINSTALLED_LAB = True
    
if UNINSTALLED_LAB:
    SHARED_DATA_DIR = abspath(join(dirname(__file__), '..', 'data'))
else:
        SHARED_DATA_DIR = join(DATA_DIR, "labyrinth")
