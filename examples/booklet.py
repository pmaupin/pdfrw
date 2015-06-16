#!/usr/bin/env python

'''
usage:   booklet.py my.pdf

Creates booklet.my.pdf

Pages organized in a form suitable for booklet printing, e.g.
to print 4 8.5x11 pages using a single 11x17 sheet (double-sided).
'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge


def fixpage(*pages):
    result = PageMerge() + (x for x in pages if x is not None)
    result[-1].x += result[0].w
    return result.render()


inpfn, = sys.argv[1:]
outfn = 'booklet.' + os.path.basename(inpfn)
ipages = PdfReader(inpfn).pages

# Make sure we have an even number
if len(ipages) & 1:
    ipages.append(None)

opages = []
while len(ipages) > 2:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
    opages.append(fixpage(ipages.pop(0), ipages.pop()))

opages += ipages

PdfWriter().addpages(opages).write(outfn)
