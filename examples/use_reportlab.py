#!/usr/bin/env python

'''
usage:   use_reportlab.py my.pdf

Creates use_reportlab.my.pdf

Take a look and see what you get.
'''

import sys
import os

from reportlab.pdfgen.canvas import Canvas

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfArray
from pdfrw.decodegraphics import parsepage

inpfn, = sys.argv[1:]
outfn = 'use_reportlab.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages
canvas = Canvas(outfn, pageCompression=0)

for page in pages:
    box = [float(x) for x in page.MediaBox]
    assert box[0] == box[1] == 0, "demo won't work on this PDF"
    canvas.setPageSize(box[2:])
    parsepage(page, canvas)
    canvas.showPage()
canvas.save()
