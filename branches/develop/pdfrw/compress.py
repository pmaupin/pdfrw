# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Currently, this sad little file only knows how to decompress
using the flate (zlib) algorithm.  Maybe more later, but it's
not a priority for me...
'''
import zlib
from pdfrw.objects import PdfDict, PdfName
from pdfrw.errors import log
from pdfrw.uncompress import streamobjects

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
