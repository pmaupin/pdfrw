# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Currently, this sad little file only knows how to decompress
using the flate (zlib) algorithm.  Maybe more later, but it's
not a priority for me...
'''
from .objects import PdfDict, PdfName
from .errors import log
from .py23_diffs import zlib

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def streamobjects(mylist, isinstance=isinstance, PdfDict=PdfDict):
    for obj in mylist:
        if isinstance(obj, PdfDict) and obj.stream is not None:
            yield obj

# Hack so we can import if zlib not available
decompressobj = zlib if zlib is None else zlib.decompressobj


def uncompress(mylist, warnings=set(), flate=PdfName.FlateDecode,
               decompress=decompressobj, isinstance=isinstance,
               list=list, len=len):
    ok = True
    for obj in streamobjects(mylist):
        ftype = obj.Filter
        if ftype is None:
            continue
        if isinstance(ftype, list) and len(ftype) == 1:
            # todo: multiple filters
            ftype = ftype[0]
        parms = obj.DecodeParms
        if ftype != flate:
            msg = ('Not decompressing: cannot use filter %s'
                  ' with parameters %s') % (repr(ftype), repr(parms))
            if msg not in warnings:
                warnings.add(msg)
                log.warning(msg)
            ok = False
        else:
            dco = decompress()
            error = None
            try:
                data = dco.decompress(obj.stream)

                if parms:
                    # try png predictor
                    predictor = int(parms['/Predictor']) or 1
                    # predictor 1 == no predictor
                    if predictor != 1:
                        columns = int(parms['/Columns'])
                        # PNG prediction:
                        if predictor >= 10 and predictor <= 15:
                            output = StringIO()
                            # PNG prediction can vary from row to row
                            rowlen = columns + 1
                            assert len(data) % rowlen == 0
                            prev_rowdata = (0,) * rowlen
                            for row in xrange(len(data) / rowlen):
                                rowdata = [ord(x) for x in
                                    data[(row * rowlen):((row + 1) * rowlen)]]
                                filter_byte = rowdata[0]
                                if filter_byte == 0:
                                    pass
                                elif filter_byte == 1:
                                    for i in xrange(2, rowlen):
                                        rowdata[i] = (rowdata[i] +
                                                      rowdata[i - 1]) % 256
                                elif filter_byte == 2:
                                    for i in xrange(1, rowlen):
                                        rowdata[i] = (rowdata[i] +
                                                      prev_rowdata[i]) % 256
                                else:
                                    # unsupported PNG filter
                                    raise Exception(('Unsupported PNG '
                                                    'filter %r') % filter_byte)
                                prev_rowdata = rowdata
                                output.write(''.join([chr(x) for x in
                                                      rowdata[1:]]))
                            data = output.getvalue()
                        else:
                            # unsupported predictor
                            raise Exception(('Unsupported flatedecode'
                                            ' predictor %r') % predictor)

            except Exception as s:
                error = str(s)
            if error is None:
                assert not dco.unconsumed_tail
                if dco.unused_data.strip():
                    error = ('Unconsumed compression data: %s' %
                             repr(dco.unused_data[:20]))
            if error is None:
                obj.Filter = None
                obj.stream = data
            else:
                log.error('%s %s' % (error, repr(obj.indirect)))
    return ok
