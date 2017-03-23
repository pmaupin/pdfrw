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

# Create blank page
blank = PageMerge()
blank.mbox = ipages[0].MediaBox
blank = blank.render()

# Make sure we have a multiple of 4 pages
while len(ipages) % 4:
    ipages.append(blank)

opages = []
while ipages:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
    opages.append(fixpage(ipages.pop(0), ipages.pop()))

PdfWriter().addpages(opages).write(outfn)
