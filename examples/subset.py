#!/usr/bin/env python

'''
usage:   subset.py my.pdf page[range] [page[range]] ...
         eg. subset.py 1-3 5 7-9

Creates subset.my.pdf

'''

import sys
import os

from pdfrw import PdfReader, PdfWriter

inpfn = sys.argv[1]
ranges = sys.argv[2:]
assert ranges, "Expected at least one range"

ranges = ([int(y) for y in x.split('-')] for x in ranges)
outfn = 'subset.%s' % os.path.basename(inpfn)
pages = PdfReader(inpfn).pages
outdata = PdfWriter()

for onerange in ranges:
    onerange = (onerange + onerange[-1:])[:2]
    for pagenum in range(onerange[0], onerange[1]+1):
        outdata.addpage(pages[pagenum-1])
outdata.write(outfn)
