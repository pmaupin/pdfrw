# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
    Read expected.txt, which should be in the format:

       testname/srcname.pdf validhash

    More than one validhash is allowed (on separate lines),
    and hash-delimited comments are allowed.
'''

import os
import collections
from pdfrw.py23_diffs import convert_load

root_dir = os.path.dirname(__file__)
result_dir = os.path.join(root_dir, 'tmp_results')
expectedf = os.path.join(root_dir, 'expected.txt')

def results():
    results = collections.defaultdict(set)
    with open(expectedf, 'rb') as f:
        for line in f:
            line = convert_load(line)
            line = line.split('#', 1)[0].split()
            if not line:
                continue
            key, value = line
            results[key].add(value)
    return results

results = results()

