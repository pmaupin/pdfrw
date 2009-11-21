#!/usr/bin/env python

'''
usage:   print_booklet.py my.pdf

Creates print_booklet.my.pdf

Pages organized in a form suitable for booklet printing.

Works on some PDFs generated from OO.

Not thoroughly tested.  Expect some dictionary resource merging
might be required for general PDF usage.
'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfArray

def fixpage(page1, page2):
    # For demo purposes, just go with the MediaBox and toast the others
    box = [float(x) for x in page1.MediaBox]
    box2 = [float(x) for x in page2.MediaBox]
    assert box == box2
    assert box[0] == box[1] == 0, "demo won't work on this PDF"

    for page in page1, page2:
        for key, value in sorted(page.iteritems()):
            if 'box' in key.lower():
                del page[key]

    startsize = tuple(box[2:])
    finalsize = 2 * box[2], box[3]
    page1.MediaBox = PdfArray((0, 0) + finalsize)

    contents = page.Contents
    assert contents.Filter is None, "Must decompress page first"

    offset = '1 0 0 1 %s %s cm\n' % (finalsize[0]/2, 0)

    stream2 = page2.Contents.stream
    stream1 = page1 is not page2 and page1.Contents.stream or ''
    stream = 'q\n%s\n%s\nQ\n%s' % (offset, stream2, stream1)
    page1.Contents.stream = stream
    return page1

inpfn, = sys.argv[1:]
outfn = 'print_booklet.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages

if len(pages) & 1:
    pages.append(pages[0])

bigpages = []
while len(pages) > 2:
    bigpages.append(fixpage(pages.pop(), pages.pop(0)))
    bigpages.append(fixpage(pages.pop(0), pages.pop()))

bigpages += pages

PdfWriter().addpages(bigpages).write(outfn)
