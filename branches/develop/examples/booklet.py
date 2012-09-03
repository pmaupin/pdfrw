#!/usr/bin/env python

'''
usage:   booklet.py my.pdf

Creates booklet.my.pdf

Pages organized in a form suitable for booklet printing.

'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfArray, PdfName, IndirectPdfDict
from pdfrw.buildxobj import pagexobj

def fixpage(*pages):
    pages = [pagexobj(x) for x in pages]

    class PageStuff(tuple):
        pass

    x = y = 0
    for i, page in enumerate(pages):
        index = '/P%s' % i
        shift_right = x and '1 0 0 1 %s 0 cm ' % x or ''
        stuff = PageStuff((index, page))
        stuff.stream = 'q %s%s Do Q\n' % (shift_right, index)
        x += page.BBox[2]
        y = max(y, page.BBox[3])
        pages[i] = stuff

    # Multiple copies of first page used as a placeholder to
    # get blank page on back.
    for p1, p2 in zip(pages, pages[1:]):
        if p1[1] is p2[1]:
            pages.remove(p1)

    return IndirectPdfDict(
        Type = PdfName.Page,
        Contents = PdfDict(stream=''.join(page.stream for page in pages)),
        MediaBox = PdfArray([0, 0, x, y]),
        Resources = PdfDict(
            XObject = PdfDict(pages),
        ),
    )

inpfn, = sys.argv[1:]
outfn = 'booklet.' + os.path.basename(inpfn)
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
