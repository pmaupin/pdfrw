#!/usr/bin/env python


import sys
import os
import traceback
import time

args = sys.argv[1:]
if args:
    sys.path.insert(0, args[0])

try:
    import pdfrw
except ImportError:
    import find_pdfrw

import pdfrw

from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, IndirectPdfDict, PdfArray

allfiles = (x.split('#',1)[0] for x in open('data/allpdfs.txt').read().splitlines())
allfiles = [x for x in allfiles if x]

def test_pdf(pdfname):
    PdfReader(pdfname, decompress=False)
    return '%0.2f' % (time.time() - start)

badfiles = []
goodfiles = []
times = []

try:
    for fname in allfiles:
        print fname
        start = time.time()
        try:
            test_pdf(fname)
        except Exception:
            ok = False
            #print traceback.format_exc()[:2000]
            #raise
        else:
            ok = True
        elapsed = time.time() - start

        print ok and "OK" or "Failed miserably."
        print
        (badfiles, goodfiles)[ok].append(fname)
        times.append((elapsed, fname))
except KeyboardInterrupt:
    pass

print "Total = %s, good = %s, bad = %s" % (len(times), len(goodfiles), len(badfiles))

times.sort()
times.reverse()

f = open('log.txt', 'a')
print >> f, '\n\n\n\n\n\n***************************************************************************\n\n\n'
for fname in goodfiles:
    print >> f, 'good', fname
print >> f
for fname in badfiles:
    print >> f, 'bad', fname
print >> f
for stuff in times:
    print >> f, '%0.2f %s' % stuff
f.close()

print pdfrw.__file__
