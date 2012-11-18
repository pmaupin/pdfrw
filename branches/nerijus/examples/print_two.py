#!/usr/bin/env python

'''
usage:   print_two.py my.pdf

Creates print_two.my.pdf

This is only useful when you can cut down sheets of paper to make two
small documents.  Works for double-sided only right now.

'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfArray, IndirectPdfDict

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
    if contents is None:
        return page
    contents = isinstance(contents, dict) and [contents] or contents

    prefix = '0 1 -1 0 %s %s cm\n' % (finalsize[0], 0)
    if evenpage:
        prefix = '1 0 0 1 %s %s cm\n' % (0, finalsize[1]/2) +  prefix
    first_prefix = 'q\n-1 0 0 -1 %s %s cm\n' % finalsize + prefix
    second_prefix = '\nQ\n' + prefix
    first_prefix = IndirectPdfDict(stream=first_prefix)
    second_prefix = IndirectPdfDict(stream=second_prefix)
    contents = PdfArray(([second_prefix] + contents) * 2)
    contents[0] = first_prefix
    page.Contents = contents
    return page


inpfn, = sys.argv[1:]
outfn = 'print_two.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages

PdfWriter().addpages(fixpage(x) for x in pages).write(outfn)
