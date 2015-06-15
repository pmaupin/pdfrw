#!/usr/bin/env python

'''
usage:   getimages.py <some.pdf>

Locates images and image type within the PDF.

Need to add code to write them out.....

'''

import sys
import os

from pdfrw import PdfReader, PdfDict, PdfArray, PdfName


XObject = PdfName.XObject
Image = PdfName.Image


def find_images(obj, visited=set()):
    if not isinstance(obj, (PdfDict, PdfArray)):
        return

    # Don't get stuck in an infinite loop
    myid = id(obj)
    if myid in visited:
        return
    visited.add(myid)

    if isinstance(obj, PdfDict):
        if obj.Type == XObject and obj.Subtype == Image:
            yield obj
        obj = obj.itervalues()

    for item in obj:
        for result in find_images(item, visited):
            yield result


def show_image(image):
    print '******************'
    print
    print image
    print repr(image.stream[:200])
    print
    try:
        print image.Filter
        print int(image.Height)
        print int(image.Width)
        print int(image.Length)
        print image.ColorSpace
        print int(image.DecodeParms.Columns)
        print int(image.DecodeParms.K)
        print int(image.DecodeParms.Rows)
    except:
        pass

if __name__ == '__main__':
    inpfn, = sys.argv[1:]
    for image in find_images(PdfReader(inpfn)):
        show_image(image)
