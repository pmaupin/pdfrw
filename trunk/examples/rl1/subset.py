#!/usr/bin/env python

'''
usage:   subset.py my.pdf firstpage lastpage

Creates subset_<pagenum>_to_<pagenum>.my.pdf


Uses Form XObjects and reportlab to create output file.

Demonstrates use of pdfrw with reportlab.

'''

import sys
import os

from reportlab.pdfgen.canvas import Canvas

import find_pdfrw
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


def go(inpfn, firstpage, lastpage):
    firstpage, lastpage = int(firstpage), int(lastpage)
    outfn = 'subset_%s_to_%s.%s' % (firstpage, lastpage, os.path.basename(inpfn))

    pages = PdfReader(inpfn, decompress=False).pages
    pages = [pagexobj(x) for x in pages[firstpage-1:lastpage]]
    canvas = Canvas(outfn)

    for page in pages:
        canvas.setPageSize(tuple(page.BBox[2:]))
        canvas.doForm(makerl(canvas, page))
        canvas.showPage()

    canvas.save()

if __name__ == '__main__':
    inpfn, firstpage, lastpage = sys.argv[1:]
    go(inpfn, firstpage, lastpage)
