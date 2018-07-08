#!/usr/bin/env python
"""
usage:   alter.py my.pdf

Creates alter.my.pdf

Demonstrates making a slight alteration to a preexisting PDF file.
"""
import sys
import os

from pdfrw import PdfReader, PdfWriter


def alter(inpfn):
    outfn = 'alter.' + os.path.basename(inpfn)

    trailer = PdfReader(inpfn)
    trailer.Info.Title = 'My New Title Goes Here'
    PdfWriter(outfn, trailer=trailer).write()


if __name__ == '__main__':
    inpfn, = sys.argv[1:]
    alter(inpfn)
