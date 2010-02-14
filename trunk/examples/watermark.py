#!/usr/bin/env python

'''
Simple example of watermarking using form xobjects.

usage:   watermark.py my.pdf single_page.pdf

Creates watermark.my.pdf, with every page overlaid with
first page from single_page.pdf
'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, IndirectPdfDict, PdfArray
from pdfrw.buildxobj import pagexobj

def fixpage(page, watermark):

    # Find the page's resource dictionary. Create if none
    resources = page.inheritable.Resources
    if resources is None:
        resources = page.Resources = PdfDict()

    # Find or create the parent's xobject dictionary
    xobjdict = resources.XObject
    if xobjdict is None:
        xobjdict = resources.XObject = PdfDict()

    # Allow for an infinite number of cascaded watermarks
    index = 0
    while 1:
        watermark_name = '/Watermark.%d' % index
        if watermark_name not in xobjdict:
            break
        index += 1
    xobjdict[watermark_name] = watermark

    # Turn the contents into an array if it is not already one
    contents = page.Contents
    if not isinstance(contents, PdfArray):
        contents = page.Contents = PdfArray([contents])

    # Save initial state before executing page
    contents.insert(0, IndirectPdfDict(stream='q\n'))

    # Restore initial state and append the watermark
    contents.append(IndirectPdfDict(stream='Q %s Do\n' % watermark_name))
    return page

try:
    inpfn, waterfn = sys.argv[1:]
except:
    raise SystemExit('Usage:  watermark.py <input.pdf> <single_page.pdf>')

watermark = pagexobj(PdfReader(waterfn, decompress=False).pages[0])
outfn = 'watermark.' + os.path.basename(inpfn)
pages = PdfReader(inpfn, decompress=False).pages

PdfWriter().addpages([fixpage(x, watermark) for x in pages]).write(outfn)
