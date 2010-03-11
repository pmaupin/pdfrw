#!/usr/bin/env python

'''
usage:   subset.py my.pdf firstpage lastpage

Creates subset_<pagenum>_to_<pagenum>.my.pdf

'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter

inpfn, firstpage, lastpage = sys.argv[1:]
firstpage, lastpage = int(firstpage), int(lastpage)

outfn = 'subset_%s_to_%s.%s' % (firstpage, lastpage, os.path.basename(inpfn))
pages = PdfReader(inpfn, decompress=False).pages
pages = pages[firstpage-1:lastpage]
PdfWriter().addpages(pages).write(outfn)
