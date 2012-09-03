'''
    find_xxx.py -- Find the place in the tree where xxx lives.

    Ways to use:
                1) Make a copy, change 'xxx' in package to be your name; or
                2) Under Linux, just ln -s to where this is in the right tree

    Created by Pat Maupin, who doesn't consider it big enough to be worth copyrighting
'''

import sys
import os

myname = __name__[5:]   # remove 'find_'
myname = os.path.join(myname, '__init__.py')

def trypath(newpath):
    path = None
    while path != newpath:
        path = newpath
        if os.path.exists(os.path.join(path, myname)):
            return path
        newpath = os.path.dirname(path)

root = trypath(__file__) or trypath(os.path.realpath(__file__))

if root is None:
    raise SystemExit('%s: Could not find path to package %s' % (__file__, myname))

if root not in sys.path:
    sys.path.append(root)
