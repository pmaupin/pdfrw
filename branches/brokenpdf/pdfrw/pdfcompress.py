# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Currently, this sad little file only knows how to decompress
using the flate (zlib) algorithm.  Maybe more later, but it's
not a priority for me...
'''

from __future__ import generators

try:
    set
except NameError:
    from sets import Set as set

import zlib
from pdfobjects import PdfDict, PdfName


def streamobjects(mylist):
    for obj in mylist:
        if isinstance(obj, PdfDict) and obj.stream is not None:
            yield obj

def uncompress(mylist, warnings=set()):
    flate = PdfName.FlateDecode
    for obj in streamobjects(mylist):
        ftype = obj.Filter
        if ftype is None:
            continue
        if isinstance(ftype, list) and len(ftype) == 1:
            # todo: multiple filters
            ftype = ftype[0]
        parms = obj.DecodeParms
        if ftype != flate or parms is not None:
            msg = 'Not decompressing: cannot use filter %s with parameters %s' % (repr(ftype), repr(parms))
            if msg not in warnings:
                warnings.add(msg)
                print msg
        else:
            obj.stream = zlib.decompress(obj.stream)
            obj.Filter = None

def compress(mylist):
    flate = PdfName.FlateDecode
    for obj in streamobjects(mylist):
        ftype = obj.Filter
        if ftype is not None:
            continue
        oldstr = obj.stream
        newstr = zlib.compress(oldstr)
        if len(newstr) < len(oldstr) + 30:
            obj.stream = newstr
            obj.Filter = flate
            obj.DecodeParms = None
