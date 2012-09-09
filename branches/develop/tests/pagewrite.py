#!/usr/bin/env python


import sys
import os
import traceback
import time
import gc
import hashlib

#gc.disable()

sys.path.insert(0, '../../PyPDF2/')

import PyPDF2
import find_pdfrw
import pdfrw

from PyPDF2 import PdfFileReader, PdfFileWriter

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfParseError


allfiles = (x.split('#',1)[0] for x in open('data/allpdfs.txt').read().splitlines())
allfiles = [x for x in allfiles if x]

badfiles = []
goodfiles = []
times = []

sys.setrecursionlimit(20000)

outdir = 'testout'
if not os.path.exists(outdir):
    os.mkdir(outdir)

if 0:
    reader, writer = PyPDF2.PdfFileReader, PyPDF2.PdfFileWriter
else:
    reader, writer = pdfrw.PdfReader, pdfrw.PdfWriter
pdferr = pdfrw.PdfParseError

def test_pdf(pdfname):
    outfn = os.path.join(outdir, hashlib.md5(pdfname).hexdigest() + '.pdf')
    pdf_in = reader(open(pdfname))
    pdf_out = writer()
    for pg_num in range(pdf_in.numPages):
        pdf_out.addPage(pdf_in.getPage(pg_num))
    out_stream = open(outfn, "wb")
    pdf_out.write(out_stream)
    out_stream.close()

try:
    for fname in allfiles:
        #print >> sys.stderr, "File name", fname
        print "File name", fname
        sys.stdout.flush()
        start = time.time()
        try:
            test_pdf(fname)
        except Exception, s:
            sys.stderr.flush()
            ok = False
            if isinstance(s, PdfParseError):
                print '[ERROR]', s
            else:
                print traceback.format_exc()[-2000:]
            #raise
        else:
            sys.stderr.flush()
            ok = True
        elapsed = time.time() - start

        print ok and "[OK]" or "[FAIL]"
        print
        (badfiles, goodfiles)[ok].append(fname)
        times.append((elapsed, fname))
except KeyboardInterrupt:
    raise
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
