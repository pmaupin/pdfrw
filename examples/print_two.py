#!/usr/bin/env python

'''
usage:   print_two.py my.pdf

Creates print_two.my.pdf

This is only useful when you can cut down sheets of paper to make two
small documents.  Works for double-sided only right now.
'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge


def fixpage(page, count=[0]):
    count[0] += 1
    oddpage = (count[0] & 1)

    result = PageMerge()
    for rotation in (180 + 180 * oddpage, 180 * oddpage):
        result.add(page, rotate=rotation)
    result[1].x = result[0].w
    return result.render()


inpfn, = sys.argv[1:]
outfn = 'print_two.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages
PdfWriter().addpages(fixpage(x) for x in pages).write(outfn)
