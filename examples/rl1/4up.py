#!/usr/bin/env python

'''
usage:   4up.py my.pdf


Uses Form XObjects and reportlab to create 4up.my.pdf.

Demonstrates use of pdfrw with reportlab.

'''

import sys
import os

from reportlab.pdfgen.canvas import Canvas

from pdfrw import PdfReader
from pdfrw.buildxobj import pagexobj
from pdfrw.toreportlab import makerl


def addpage(canvas, allpages):
    pages = allpages[:4]
    del allpages[:4]

    x_max = max(page.BBox[2] for page in pages)
    y_max = max(page.BBox[3] for page in pages)

    canvas.setPageSize((x_max, y_max))

    for index, page in enumerate(pages):
        x = x_max * (index & 1) / 2.0
        y = y_max * (index <= 1) / 2.0
        canvas.saveState()
        canvas.translate(x, y)
        canvas.scale(0.5, 0.5)
        canvas.doForm(makerl(canvas, page))
        canvas.restoreState()
    canvas.showPage()


def go(argv):
    inpfn, = argv
    outfn = '4up.' + os.path.basename(inpfn)

    pages = PdfReader(inpfn).pages
    pages = [pagexobj(x) for x in pages]
    canvas = Canvas(outfn)

    while pages:
        addpage(canvas, pages)
    canvas.save()

if __name__ == '__main__':
    go(sys.argv[1:])
