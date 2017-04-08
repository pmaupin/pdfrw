#! /usr/bin/env python2
"""
Put old (good) results in ramdisk/reference,
then generate new (unknown) test results in ramdisk/tmp_results,
THEN SWITCH BACK TO KNOWN GOOD SYSTEM, and finally:

run this to update any checksums in expected.txt where both versions
parse to same PDFs.
"""

import os
import hashlib
from pdfrw import PdfReader, PdfWriter, PdfArray, PdfDict, PdfObject


def make_canonical(trailer):
    ''' Canonicalizes a PDF.  Assumes everything
        is a Pdf object already.
    '''
    visited = set()
    workitems = list(trailer.values())
    while workitems:
        obj = workitems.pop()
        objid = id(obj)
        if objid in visited:
            continue
        visited.add(objid)
        obj.indirect = True
        if isinstance(obj, (PdfArray, PdfDict)):
            if isinstance(obj, PdfArray):
                workitems += obj
            else:
                workitems += obj.values()
    return trailer

with open('expected.txt', 'rb') as f:
    expected = f.read()

def get_digest(fname):
        with open(fname, 'rb') as f:
            data = f.read()
        if data:
            return hashlib.md5(data).hexdigest()

tmp = '_temp.pdf'
count = 0
goodcount = 0

changes = []
for (srcpath, _, filenames) in os.walk('ramdisk/reference'):
    for name in filenames:
        if not name.endswith('.pdf'):
            continue
        src = os.path.join(srcpath, name)
        dst = src.replace('/reference/', '/tmp_results/')
        if not os.path.exists(dst):
            continue
        src_digest = get_digest(src)
        if not src_digest or src_digest not in expected:
            continue
        print src
        count += 1
        trailer = make_canonical(PdfReader(src))
        out = PdfWriter(tmp)
        out.write(trailer=trailer)
        match_digest = get_digest(tmp)
        if not match_digest:
            continue
        trailer = make_canonical(PdfReader(dst))
        out = PdfWriter(tmp)
        out.write(trailer=trailer)
        if get_digest(tmp) != match_digest:
            continue
        goodcount += 1
        print "OK"
        changes.append((src_digest, get_digest(dst)))

print count, goodcount

for stuff in changes:
    expected = expected.replace(*stuff)

with open('expected.txt', 'wb') as f:
    f.write(expected)
