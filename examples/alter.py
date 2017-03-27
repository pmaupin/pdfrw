#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
usage:   alter.py my.pdf

Creates alter.my.pdf

Demonstrates making a slight alteration to a preexisting PDF file.
Also demonstrates Unicode support.

'''

import sys
import os

from pdfrw import PdfReader, PdfWriter

inpfn, = sys.argv[1:]
outfn = 'alter.' + os.path.basename(inpfn)

trailer = PdfReader(inpfn)
trailer.Info.Title = 'My New Title Goes Here - 我的新名称在这儿'
writer = PdfWriter()
writer.trailer = trailer
writer.write(outfn)
