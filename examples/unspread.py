#!/usr/bin/env python

'''
usage:   unspread.py my.pdf

Creates unspread.my.pdf

Chops each page in half, e.g. if a source were
created in booklet form, you could extract individual
pages.
'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge


def splitpage(src):
    ''' Split a page into two (left and right)
    '''
    # Yield a result for each half of the page
    for x_pos in (0, 0.5):
        yield PageMerge().add(src, viewrect=(x_pos, 0, 0.5, 1)).render()


inpfn, = sys.argv[1:]
outfn = 'unspread.' + os.path.basename(inpfn)
writer = PdfWriter()
for page in PdfReader(inpfn).pages:
    writer.addpages(splitpage(page))
writer.write(outfn)
