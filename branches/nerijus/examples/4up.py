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

    x_max = max(page.BBox[2] for page in pages)
    y_max = max(page.BBox[3] for page in pages)

    stream = []
    xobjdict = PdfDict()
    for index, page in enumerate(pages):
        x = x_max * (index & 1) / 2.0
        y = y_max * (index <= 1) / 2.0
        index = '/P%s' % index
        stream.append('q 0.5 0 0 0.5 %s %s cm %s Do Q\n' % (x, y, index))
        xobjdict[index] = page

    return PdfDict(
        Type = PdfName.Page,
        Contents = PdfDict(stream=''.join(stream)),
        MediaBox = PdfArray([0, 0, x_max, y_max]),
        Resources = PdfDict(XObject = xobjdict),
    )

def go(inpfn, outfn):
    pages = PdfReader(inpfn).pages
    writer = PdfWriter()
    while pages:
        writer.addpage(get4(pages))
    writer.write(outfn)

if __name__ == '__main__':
    inpfn, = sys.argv[1:]
    outfn = '4up.' + os.path.basename(inpfn)
    go(inpfn, outfn)
