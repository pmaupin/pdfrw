#!/usr/bin/env python

'''
usage:   9up.py my.pdf

Note: Tested with Python3.12

Creates 9up.my.pdf with a single output page for every
9 input pages.
'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge

def get9(srcpages):
    scale = 0.333333
    srcpages = PageMerge() + srcpages
    x_increment, y_increment = (scale * i for i in srcpages.xobj_box[2:])
    for i, page in enumerate(srcpages):
        page.scale(scale)

        if i%3 == 0: page.x=0
        elif i%3 == 1: page.x=x_increment
        elif i%3 == 2: page.x=2*x_increment

        if i%9 <  3: page.y=2*y_increment
        elif i%9 <  6: page.y=y_increment
        else:          page.y=0
    return srcpages.render()


inpfn, = sys.argv[1:]
outfn = '9up.' + os.path.basename(inpfn)
pages = PdfReader(inpfn).pages
writer = PdfWriter(outfn)
for index in range(0, len(pages), 9):
    writer.addpage(get9(pages[index:index + 9]))
writer.write()

print()
os.system(f"ls -al {outfn}")
