#!/usr/bin/env python

'''
usage:   unspread.py my.pdf

Creates unspread.my.pdf

Chops each page in half.

'''

import sys
import os

from pdfrw import (PdfReader, PdfWriter, PdfDict,
                   PdfArray, PdfName, IndirectPdfDict)
from pdfrw.buildxobj import pagexobj

class MyView(object):
    ''' Adobe has a user-friendly concept of a view
        rectangle for their web interface stuff.
        The interface to pagexobj reuses this.
    '''
    rotate = 0
    def __init__(self, x, y, w, h):
        self.viewrect = x, y, w, h

def splitpage(src):
    ''' Split a page into two (left and right)
    '''
    # Figure out the page extents and insure
    # that the page starts at 0,0 (lower left)
    l, b, r, t = pagexobj(src).BBox
    assert l == b == 0, (l, b)

    # Yield a result for each half of the page
    m = (l + r) / 2
    for start in (0, m):
        # If it's the right half, we need to shift it left
        # to make it viewable.
        shift_left = start and '1 0 0 1 %s 0 cm ' % -start or ''

        # For cleanliness, save and restore the context, then
        # do the shift (if required) and access a portion of
        # the original page as a FormXObject.
        stream = 'q %s /SrcPage Do Q\n' % shift_left

        # Build the page dictionary, with our FormXObj as a resource.
        yield IndirectPdfDict(
            Type=PdfName.Page,
            Contents=PdfDict(stream=stream),
            MediaBox=PdfArray([0, 0, m, t]),
            Resources=PdfDict(
                XObject=PdfDict(
                    SrcPage=pagexobj(src, MyView(start, 0, m, t))
                ),
            ),
        )

inpfn, = sys.argv[1:]
outfn = 'unspread.' + os.path.basename(inpfn)

writer = PdfWriter()
for page in PdfReader(inpfn).pages:
    writer.addpages(splitpage(page))
writer.write(outfn)
