#!/usr/bin/env python


import sys
import os
import traceback
import time
import gc
import hashlib

from sys import stderr

#gc.disable()

args = sys.argv[1:]
if args:
    sys.path.insert(0, args[0])

try:
    import pdfrw
except ImportError:
    import find_pdfrw

import pdfrw

from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, IndirectPdfDict, PdfArray, PdfParseError

allfiles = (x.split('#',1)[0] for x in open('data/allpdfs.txt').read().splitlines())
allfiles = [x for x in allfiles if x]

badfiles = []
goodfiles = []
times = []

outdir = 'testout'
if not os.path.exists(outdir):
    os.mkdir(outdir)

def test_pdf(pdfname):
    outfn = os.path.join(outdir, hashlib.md5(pdfname).hexdigest() + '.pdf')
    print >> stderr, '             ->', outfn
    trailer = PdfReader(pdfname, decompress=False)
    try:
        trailer.Info.OriginalFileName = pdfname
    except AttributeError:
        trailer.OriginalFileName = pdfname
    writer = PdfWriter()
    writer.trailer = trailer
    writer.write(outfn)

try:
    first_start_time = time.time()
    for fname in allfiles:
        #print >> sys.stderr, "File name", fname
        print >> stderr, "File name", fname
        sys.stdout.flush()
        start = time.time()
        try:
            test_pdf(fname)
        except Exception, s:
            stderr.flush()
            ok = False
            if isinstance(s, PdfParseError):
                print >> stderr, '[ERROR]', s
            else:
                print >> stderr, traceback.format_exc()[-2000:]
            #raise
        else:
            stderr.flush()
            ok = True
        elapsed = time.time() - start

        print >> stderr,  ok and "[OK]" or "[FAIL]"
        print
        (badfiles, goodfiles)[ok].append(fname)
        times.append((elapsed, fname))
except KeyboardInterrupt:
    pass

print "Total = %s, good = %s, bad = %s" % (len(times), len(goodfiles), len(badfiles))
print "Execution time = %0.2f" % (time.time() - first_start_time)

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
