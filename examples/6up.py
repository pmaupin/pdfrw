#!/usr/bin/env python

'''
usage:   6up.py my.pdf

Note: Tested with Python3.12

Creates 6up.my.pdf with a single output page for every
6 input pages.
'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge

def get6(srcpages):
    scale = 0.333333
    srcpages = PageMerge() + srcpages
    x_increment, y_increment = (scale * i for i in srcpages.xobj_box[2:])

    for i, page in enumerate(srcpages):
        page.scale(scale)

        if i%2 == 0: page.x=0
        else: page.x=x_increment

        if i%6 <  2: page.y=2*y_increment
        elif i%6 <  4: page.y=y_increment
        else:          page.y=0
    return srcpages.render()


inpfn, = sys.argv[1:]
outfn = '6up.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages
writer = PdfWriter(outfn)
for index in range(0, len(pages), 6):
    writer.addpage(get6(pages[index:index + 6]))
writer.write()

print()
os.system(f"ls -al {outfn}")
