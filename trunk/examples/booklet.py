#!/usr/bin/env python

'''
usage:   print_booklet.py my.pdf

Creates print_booklet.my.pdf

Pages organized in a form suitable for booklet printing.

'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfArray, PdfName, IndirectPdfDict
from pdfrw.buildxobj import pagexobj

def fixpage(*pages):
    pages = [pagexobj(x) for x in pages]

    stream = []
    x = y = 0
    for i, page in enumerate(pages):
        stream.append('q 1 0 0 1 %s 0 cm /P%s Do Q\n' % (x, i))
        x += page.BBox[2]
        y = max(y, page.BBox[3])

    # Multiple copies of first page used as a placeholder to
    # get blank page on back.
    while pages[-1] is pages[0]:
        pages.pop()
        stream.pop()

    return IndirectPdfDict(
        Type = PdfName.Page,
        Contents = PdfDict(stream=''.join(stream)),
        MediaBox = PdfArray([0, 0, x, y]),
        Resources = PdfDict(
            XObject = PdfDict(
                ('/P%s' % i, page) for (i, page) in enumerate(pages)),
        ),
    )

inpfn, = sys.argv[1:]
outfn = 'print_booklet.' + os.path.basename(inpfn)
pages = PdfReader(inpfn, decompress=False).pages

# Use page1 as a marker to print a blank at the end
if len(pages) & 1:
    pages.append(pages[0])

bigpages = []
while len(pages) > 2:
    bigpages.append(fixpage(pages.pop(), pages.pop(0)))
    bigpages.append(fixpage(pages.pop(0), pages.pop()))

bigpages += pages

PdfWriter().addpages(bigpages).write(outfn)
