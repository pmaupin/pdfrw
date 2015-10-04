#!/usr/bin/env python

'''
usage:   subsetBooklet.py my.pdf

Creates subsetBooklet.my.pdf

Pages organized in a form suitable for booklet printing, e.g.
to print 4 8.5x11 pages using a single 11x17 sheet (double-sided).
'''

import sys
import os
import time
from pdfrw import PdfReader, PdfWriter, PageMerge

bookletSize = 20
start = time.time()

def fixpage(*pages):
    result = PageMerge() + (x for x in pages if x is not None)
    result[-1].x += result[0].w
    return result.render()

inpfn, = sys.argv[1:]
outfn = 'booklet.' + os.path.basename(inpfn)
allipages = PdfReader(inpfn).pages
print 'The pdf file '+str(inpfn)+' has '+str(len(allipages))+' pages.'

#Make sure we have an even number
if len(allipages) & 1:
   allipages.append(None)
   print 'Inserting one more blank page to make pages number even.'
numOfIter, leftIter = divmod(len(allipages), bookletSize)

print 'Making '+str(numOfIter)+' subbooklets of '+str(bookletSize)+' pages each.'
opages = []
for iteration in range(0,numOfIter):
	ipages = allipages[iteration*bookletSize:(iteration+1)*bookletSize]
	while len(ipages) > 2:
	    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
	    opages.append(fixpage(ipages.pop(0), ipages.pop()))

# Making one more subbooklet with the left pages
ipages = allipages[len(allipages)-leftIter:len(allipages)]
while len(ipages) > 2:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
    opages.append(fixpage(ipages.pop(0), ipages.pop()))
if len(ipages) >=1:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))

PdfWriter().addpages(opages).write(outfn)
print 'It took '+ str(round(time.time()-start,2))+' seconds to make the pdf subbooklets changes.' 
