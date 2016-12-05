#!/usr/bin/env python

'''
usage:   subset_booklet.py my.pdf

Creates subset_booklet.my.pdf

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
num_of_iter, iters_left = divmod(len(allipages), BOOKLET_SIZE)

print 'Making '+str(num_of_iter)+' subbooklets of '+str(BOOKLET_SIZE)+' pages each.'
opages = []
for iteration in range(0,num_of_iter):
    ipages = allipages[iteration*BOOKLET_SIZE:(iteration+1)*BOOKLET_SIZE]
    while len(ipages) > 2:
        opages.append(fixpage(ipages.pop(), ipages.pop(0)))
        opages.append(fixpage(ipages.pop(0), ipages.pop()))

# Making one more subbooklet with the left pages
ipages = allipages[len(allipages)-iters_left:len(allipages)]
while len(ipages) > 2:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))
    opages.append(fixpage(ipages.pop(0), ipages.pop()))
if len(ipages) >=1:
    opages.append(fixpage(ipages.pop(), ipages.pop(0)))

PdfWriter().addpages(opages).write(outfn)
print 'It took '+ str(round(time.time()-start,2))+' seconds to make the pdf subbooklets changes.' 
