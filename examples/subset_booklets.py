#!/usr/bin/env python

'''
usage: subset_booklets.py my.pdf

Creates subset_booklets.my.pdf

Pages organized in a form suitable for booklet printing, e.g.
to print 4 8.5x11 pages using a single 11x17 sheet (double-sided).
Instead of a large booklet, the pdf is divided into several mini
booklets. The reason is: professional printing works this way:
    - Print all of several mini booklets(subsets of booklet);
    - Saw each mini booklet individually;
    - glue them all together;
    - Insert the cover.

    Take a look at http://www.wikihow.com/Bind-a-Book
'''

import sys
import os
import time
from pdfrw import PdfReader, PdfWriter, PageMerge

BOOKLET_SIZE = 20
START = time.time()

def fixpage(*pages):
    result = PageMerge() + (x for x in pages if x is not None)
    result[-1].x += result[0].w
    return result.render()

INPFN, = sys.argv[1:]
OUTFN = 'booklet.' + os.path.basename(INPFN)
ALL_IPAGES = PdfReader(INPFN).pages
print 'The pdf file '+str(INPFN)+' has '+str(len(ALL_IPAGES))+' pages.'

#Make sure we have an even number
if len(ALL_IPAGES) & 1:
    ALL_IPAGES.append(None)
    print 'Inserting one more blank page to make pages number even.'
NUM_OF_ITER, ITERS_LEFT = divmod(len(ALL_IPAGES), BOOKLET_SIZE)

print 'Making '+str(NUM_OF_ITER)+' subbooklets of '+str(BOOKLET_SIZE)+' pages each.'
opages = []
for iteration in range(0, NUM_OF_ITER):
    ipages = ALL_IPAGES[iteration*BOOKLET_SIZE:(iteration+1)*BOOKLET_SIZE]
    while len(ipages) > 2:
        opages.append(fixpage(ipages.pop(), ipages.pop(0)))
        opages.append(fixpage(ipages.pop(0), ipages.pop()))

# Making one more subbooklet with the left pages
ipages = ALL_IPAGES[len(ALL_IPAGES)-ITERS_LEFT:len(ALL_IPAGES)]
while len(ipages) > 2:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
    opages.append(fixpage(ipages.pop(0), ipages.pop()))
if len(ipages) >= 1:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))

PdfWriter(OUTFN).addpages(opages).write()
print 'It took '+ str(round(time.time()-START, 2))+' seconds to make the pdf subbooklets changes.'
