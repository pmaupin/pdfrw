#!/usr/bin/env python

'''
usage:   print_two.py my.pdf

Creates print_two.my.pdf

Take a look and see what you get.
'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfArray

def fixpage(page, count=[0]):
    count[0] += 1
    evenpage = not (count[0] & 1)

    # For demo purposes, just go with the MediaBox and toast the others
    box = [float(x) for x in page.MediaBox]
    assert box[0] == box[1] == 0, "demo won't work on this PDF"

    for key, value in sorted(page.iteritems()):
        if 'box' in key.lower():
            del page[key]

    startsize = tuple(box[2:])
    finalsize = box[3], 2 * box[2]
    page.MediaBox = PdfArray((0, 0) + finalsize)
    page.Rotate = (int(page.Rotate or 0) + 90) % 360

    contents = page.Contents
    assert contents.Filter is None, "Must decompress page first"

    stream = contents.stream
    stream = '0 1 -1 0 %s %s cm\n%s' % (finalsize[0], 0, stream)

    if evenpage:
        stream = '1 0 0 1 %s %s cm\n%s' % (0, finalsize[1]/2, stream)

    stream = 'q\n-1 0 0 -1 %s %s cm\n%s\nQ\n%s' % (finalsize + (stream,stream))
    contents.stream = stream
    return page


inpfn, = sys.argv[1:]
outfn = 'print_two.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages

PdfWriter().addpages(fixpage(x) for x in pages).write(outfn)
