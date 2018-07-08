#!/usr/bin/env python
"""
usage:   rotate.py my.pdf rotation [page[range] ...]
         eg. rotate.py 270 1-3 5 7-9

        Rotation must be multiple of 90 degrees, clockwise.

Creates rotate.my.pdf with selected pages rotated.  Rotates all by default.
"""
import sys
import os

from pdfrw import PdfReader, PdfWriter


def rotate(inpfn, rotate_str, *ranges):
    rotate_deg = int(rotate_str)
    assert rotate_deg % 90 == 0

    ranges = [[int(y) for y in x.split('-')] for x in ranges]
    outfn = 'rotate.%s' % os.path.basename(inpfn)
    trailer = PdfReader(inpfn)
    pages = trailer.pages

    if not ranges:
        ranges = [[1, len(pages)]]

    for onerange in ranges:
        onerange = (onerange + onerange[-1:])[:2]
        for pagenum in range(onerange[0]-1, onerange[1]):
            pages[pagenum].Rotate = (int(pages[pagenum].inheritable.Rotate or
                                         0) + rotate_deg) % 360

    outdata = PdfWriter(outfn)
    outdata.trailer = trailer
    outdata.write()


if __name__ == '__main__':
    inpfn = sys.argv[1]
    rotate_str = sys.argv[2]
    ranges = sys.argv[3:]
    rotate(inpfn, rotate_str, *ranges) 
