#!/usr/bin/env python

'''
usage:   booklet.py [-p] my.pdf

Creates booklet.my.pdf

Pages organized in a form suitable for booklet printing, e.g.
to print 4 8.5x11 pages using a single 11x17 sheet (double-sided).

The output would be using the same type of sheet
and you can get up to 3 blank sides if -p is enabled.

Otherwise the two sides in the middle will be in original page size
and you can have 1 blank sides at most.

'''

import os
import argparse

from pdfrw import PdfReader, PdfWriter, PageMerge


def fixpage(*pages):
    result = PageMerge() + (x for x in pages if x is not None)
    result[-1].x += result[0].w
    return result.render()


parser = argparse.ArgumentParser()
parser.add_argument("input", help="Input pdf file name")
parser.add_argument("-p", "--padding", action = "store_true",
                    help="Padding the document so that all pages use the same type of sheet")
args = parser.parse_args()

inpfn = args.input
outfn = 'booklet.' + os.path.basename(inpfn)
ipages = PdfReader(inpfn).pages

if args.padding:
    pad_to = 4
else:
    pad_to = 2

# Make sure we have a correct number of sides
ipages += [None]*(-len(ipages)%pad_to)

opages = []
while len(ipages) > 2:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
    opages.append(fixpage(ipages.pop(0), ipages.pop()))

opages += ipages

PdfWriter(outfn).addpages(opages).write()
