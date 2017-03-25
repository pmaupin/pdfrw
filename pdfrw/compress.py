# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Currently, this sad little file only knows how to compress
using the flate (zlib) algorithm.  Maybe more later, but it's
not a priority for me...
'''

from .objects import PdfName
from .uncompress import streamobjects
from .py23_diffs import zlib, convert_load, convert_store


def compress(mylist):
    flate = PdfName.FlateDecode
    for obj in streamobjects(mylist):
        ftype = obj.Filter
        if ftype is not None:
            continue
        oldstr = obj.stream
        newstr = convert_load(zlib.compress(convert_store(oldstr)))
        if len(newstr) < len(oldstr) + 30:
            obj.stream = newstr
            obj.Filter = flate
            obj.DecodeParms = None
