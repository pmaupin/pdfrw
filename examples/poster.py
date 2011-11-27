#!/usr/bin/env python

'''
usage:   poster.py my.pdf

Shows how to change the size on a PDF.

Motivation:

My daughter needed to create a 48" x 36" poster, but her Mac version of Powerpoint
only wanted to output 8.5" x 11" for some reason.

'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfArray, IndirectPdfDict
from pdfrw.buildxobj import pagexobj

def adjust(page):
    page = pagexobj(page)
    assert page.BBox == [0, 0, 11 * 72, int(8.5 * 72)], page.BBox
    margin = 72 // 2
    old_x, old_y = page.BBox[2] - 2 * margin, page.BBox[3] - 2 * margin

    new_x, new_y = 48 * 72, 36 * 72
    ratio = 1.0 * new_x / old_x
    assert ratio == 1.0 * new_y / old_y

    index = '/BasePage'
    x = -margin * ratio
    y = -margin * ratio
    stream = 'q %0.2f 0 0 %0.2f %s %s cm %s Do Q\n' % (ratio, ratio, x, y, index)
    xobjdict = PdfDict()
    xobjdict[index] = page

    return PdfDict(
        Type = PdfName.Page,
        Contents = PdfDict(stream=stream),
        MediaBox = PdfArray([0, 0, new_x, new_y]),
        Resources = PdfDict(XObject = xobjdict),
    )

def go(inpfn, outfn):
    reader = PdfReader(inpfn, decompress=False)
    page, = reader.pages
    writer = PdfWriter()
    writer.addpage(adjust(page))
    writer.trailer.Info = IndirectPdfDict(reader.Info)
    writer.write(outfn)

if __name__ == '__main__':
    inpfn, = sys.argv[1:]
    outfn = 'poster.' + os.path.basename(inpfn)
    go(inpfn, outfn)
