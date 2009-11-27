#!/usr/bin/env python

'''
usage:   booklet.py my.pdf


Uses Form XObjects and reportlab to create booklet.my.pdf.

Demonstrates use of pdfrw with reportlab.

'''

import sys
import os

from reportlab.pdfgen.canvas import Canvas

import find_pdfrw
from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


def read_and_double(inpfn):
    pages = PdfReader(inpfn, decompress=False).pages
    pages = [pagexobj(x) for x in pages]
    if len(pages) & 1:
        pages.append(pages[0])  # Sentinel -- get same size for back as front

    xobjs = []
    while len(pages) > 2:
        xobjs.append((pages.pop(), pages.pop(0)))
        xobjs.append((pages.pop(0), pages.pop()))
    xobjs += [(x,) for x in pages]
    return xobjs


def make_pdf(outfn, xobjpairs):
    canvas = Canvas(outfn)
    for xobjlist in xobjpairs:
        x = y = 0
        for xobj in xobjlist:
            makerl(canvas, xobj)
            x += xobj.BBox[2]
            y = max(y, xobj.BBox[3])

        canvas.setPageSize((x,y))

        # Handle blank back page
        if len(xobjlist) > 1 and xobjlist[0] == xobjlist[-1]:
            xobjlist = xobjlist[:1]
            x = xobjlist[0].BBox[2]
        else:
            x = 0
        y = 0

        for xobj in xobjlist:
            canvas.saveState()
            canvas.translate(x, y)
            canvas.doForm(xobj.rl_xobj_name)
            canvas.restoreState()
            x += xobj.BBox[2]
        canvas.showPage()
    canvas.save()


inpfn, = sys.argv[1:]
outfn = 'booklet.' + os.path.basename(inpfn)

make_pdf(outfn, read_and_double(inpfn))
