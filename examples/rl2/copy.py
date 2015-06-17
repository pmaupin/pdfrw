#!/usr/bin/env python

'''
usage:   copy.py my.pdf

Creates copy.my.pdf

Uses somewhat-functional parser.  For better results
for most things, see the Form XObject-based method.

'''

import sys
import os

from reportlab.pdfgen.canvas import Canvas

from decodegraphics import parsepage
from pdfrw import PdfReader, PdfWriter, PdfArray

inpfn, = sys.argv[1:]
outfn = 'copy.' + os.path.basename(inpfn)
pages = PdfReader(inpfn, decompress=True).pages
canvas = Canvas(outfn, pageCompression=0)

for page in pages:
    box = [float(x) for x in page.MediaBox]
    assert box[0] == box[1] == 0, "demo won't work on this PDF"
    canvas.setPageSize(box[2:])
    parsepage(page, canvas)
    canvas.showPage()
canvas.save()
