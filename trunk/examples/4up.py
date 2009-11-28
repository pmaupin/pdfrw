#!/usr/bin/env python

'''
usage:   4up.py my.pdf firstpage lastpage

Creates 4up.my.pdf

'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfArray
from pdfrw.buildxobj import pagexobj

def get4(allpages):
    # Pull a maximum of 4 pages off the list
    pages = [pagexobj(x) for x in allpages[:4]]
    del allpages[:4]

    x_inc = max(page.BBox[2] for page in pages)
    y_inc = max(page.BBox[3] for page in pages)

    stream = []
    xobjdict = PdfDict()
    for index, page in enumerate(pages):
        x = x_inc * (index & 1)
        y = y_inc * (index <= 1)
        index = '/P%s' % index
        stream.append('q 1 0 0 1 %s %s cm %s Do Q\n' % (x, y, index))
        xobjdict[index] = page

    return PdfDict(
        Type = PdfName.Page,
        Contents = PdfDict(stream=''.join(stream)),
        MediaBox = PdfArray([0, 0, x_inc * 2, y_inc * 2]),
        Resources = PdfDict(XObject = xobjdict),
    )

def go(inpfn, outfn):
    pages = PdfReader(inpfn, decompress=False).pages
    writer = PdfWriter()
    while pages:
        writer.addpage(get4(pages))
    writer.write(outfn)

if __name__ == '__main__':
    inpfn, = sys.argv[1:]
    outfn = '4up.' + os.path.basename(inpfn)
    go(inpfn, outfn)
