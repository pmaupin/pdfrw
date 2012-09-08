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

def streamobjects(mylist, isinstance, PdfDict=PdfDict):
    for obj in mylist:
        if isinstance(obj, PdfDict) and obj.stream is not None:
            yield obj

def uncompress(mylist, warnings=set(), flate = PdfName.FlateDecode,
                    decompress=zlib.decompressobj, isinstance=isinstance, list=list, len=len):
    ok = True
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
                log.warning(msg)
            ok = False
        else:
            dco = decompress()
            obj.stream = dco.decompress(obj.stream)
            assert not dco.unused_data and not dco.unconsumed_tail
            obj.Filter = None
    return ok
