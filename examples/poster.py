#!/usr/bin/env python

'''
usage:   poster.py my.pdf

Shows how to change the size on a PDF.

Motivation:

My daughter needed to create a 48" x 36" poster, but her Mac
version of Powerpoint only wanted to output 8.5" x 11" for
some reason.

So she did an 8.5x11" output with 0.5" margin all around
(actual size of useful area 7.5x10") and we scaled it
up by 4.8.

We also copy the Info dict to the new PDF.

'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge, IndirectPdfDict


def adjust(page, margin=36, scale=4.8):
    info = PageMerge().add(page)
    x1, y1, x2, y2 = info.xobj_box
    viewrect = (margin, margin, x2 - x1 - 2 * margin, y2 - y1 - 2 * margin)
    page = PageMerge().add(page, viewrect=viewrect)
    page[0].scale(scale)
    return page.render()


inpfn, = sys.argv[1:]
outfn = 'poster.' + os.path.basename(inpfn)
reader = PdfReader(inpfn)
writer = PdfWriter()
writer.addpage(adjust(reader.pages[0]))
writer.trailer.Info = IndirectPdfDict(reader.Info or {})
writer.write(outfn)
