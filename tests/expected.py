# A part of pdfrw (https://github.com/pmaupin/pdfrw)
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
result_dir = 'tmp_results'
if os.path.exists('ramdisk'):
    result_dir = os.path.join('ramdisk', result_dir)
result_dir = os.path.join(root_dir, result_dir)

for sourcef in ('mytests.txt', 'expected.txt'):
    expectedf = os.path.join(root_dir, sourcef)
    if os.path.exists(expectedf):
        break


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
