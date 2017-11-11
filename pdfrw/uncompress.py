# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# Copyright (C) 2012-2015 Nerijus Mika
# MIT license -- See LICENSE.txt for details
# Copyright (c) 2006, Mathieu Fenniak
# BSD license -- see LICENSE.txt for details
'''
A small subset of decompression filters.  Should add more later.

I believe, after looking at the code, that portions of the flate
PNG predictor were originally transcribed from PyPDF2, which is
probably an excellent source of additional filters.
'''
import array
from .objects import PdfDict, PdfName, PdfArray
from .errors import log
from .py23_diffs import zlib, xrange, from_array, convert_load, convert_store
import math

def streamobjects(mylist, isinstance=isinstance, PdfDict=PdfDict):
    for obj in mylist:
        if isinstance(obj, PdfDict) and obj.stream is not None:
            yield obj

# Hack so we can import if zlib not available
decompressobj = zlib if zlib is None else zlib.decompressobj


def uncompress(mylist, leave_raw=False, warnings=set(),
               flate=PdfName.FlateDecode, decompress=decompressobj,
               isinstance=isinstance, list=list, len=len):
    log.error("uncompress leave_raw: %s" % leave_raw)
    ok = True
    for obj in streamobjects(mylist):
        ftype = obj.Filter
        if ftype is None:
            continue
        if isinstance(ftype, list) and len(ftype) == 1:
            # todo: multiple filters
            ftype = ftype[0]
        parms = obj.DecodeParms or obj.DP
        if ftype != flate:
            msg = ('Not decompressing: cannot use filter %s'
                   ' with parameters %s') % (repr(ftype), repr(parms))
            if msg not in warnings:
                warnings.add(msg)
                log.warning(msg)
            ok = False
        else:
            dco = decompress()
            try:
                data = dco.decompress(convert_store(obj.stream))
            except Exception as s:
                error = str(s)
            else:
                error = None
                if isinstance(parms, PdfArray):
                    oldparms = parms
                    parms = PdfDict()
                    for x in oldparms:
                        parms.update(x)
                if parms:
                    predictor = int(parms.Predictor or 1)
                    columns = int(parms.Columns or 1)
                    colors = int(parms.Colors or 1)
                    bpc = int(parms.BitsPerComponent or 8)
                    l0 = len(data)
                    if 10 <= predictor <= 15:
                        data, error = flate_png(data, predictor, columns, colors, bpc)
                        try:
                            l1 = len(data)
                            assert l1 == l0, "Mismatch len %d vs %d" % (l0, l1)
                            assert error == None
                        except Exception as e:
                            log.exception("Exception after flate_png")
                            pass
                    elif predictor != 1:
                        error = ('Unsupported flatedecode predictor %s' %
                                 repr(predictor))
            if error is None:
                assert not dco.unconsumed_tail
                if dco.unused_data.strip():
                    error = ('Unconsumed compression data: %s' %
                             repr(dco.unused_data[:20]))
            if error is None:
                obj.Filter = None
                obj.stream = data if leave_raw else convert_load(data)
            else:
                log.error('%s %s' % (error, repr(obj.indirect)))
                ok = False
    return ok

def flate_png(data, predictor=1, columns=1, colors=1, bpc=8):
    ''' PNG prediction is used to make certain kinds of data
        more compressible.  Before the compression, each data
        byte is either left the same, or is set to be a delta
        from the previous byte, or is set to be a delta from
        the previous row.  This selection is done on a per-row
        basis, and is indicated by a compression type byte
        prepended to each row of data.

        Within more recent PDF files, it is normal to use
        this technique for Xref stream objects, which are
        quite regular.
    '''

    # http://www.libpng.org/pub/png/spec/1.2/PNG-Filters.html
    # Reverse filter functions

    def subfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 1: Sub
        end = start + length
        for index in xrange(start + pixel_size, end):
            data[index] = (data[index] + data[index - pixel_size]) % 256

    def upfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 2: Up
        end = start + length
        for index, i in zip(xrange(start, end), xrange(length)):
            data[index] = (data[index] + prior_row_data[i]) % 256

    def avgfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 3: Avg
        end = start + length
        for index, i in zip(xrange(start, end), xrange(length)):
            left = data[index - pixel_size] if index != start else 0
            floor = math.floor((left + prior_row_data[i]) / 2)
            data[index] = (data[index] + int(floor)) % 256

    def paethfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 4: Paeth
        def paeth_predictor(a, b, c):
            p = a + b - c
            pa = abs(p - a)
            pb = abs(p - b)
            pc = abs(p - c)
            if pa <= pb and pa <= pc:
                return a
            elif pb <= pc:
                return b
            else:
                return c
        end = start + length
        for index, i in zip(xrange(start, end), xrange(length)):
            left = data[index - pixel_size] if index != start else 0
            up = prior_row_data[i]
            up_left = prior_row_data[i - pixel_size] if i != 0 else 0
            data[index] = (data[index] + paeth_predictor(left, up, up_left)) % 256

    columnbytes = ((columns * colors * bpc) + 7) // 8
    pixel_size = (colors * bpc + 7) // 8
    data = array.array('B', data)
    rowlen = columnbytes + 1
    if predictor == 15:
        padding = (rowlen - len(data)) % rowlen
        data.extend([0] * padding)
    assert len(data) % rowlen == 0

    rows = xrange(0, len(data), rowlen)
    prior_row_data = [ 0 for i in xrange(columnbytes) ]
    for row_index in rows:

        filter_type = data[row_index]
        #row_data = data[row_index + 1 : row_index + 1 + columnbytes] # without filter_type

        if filter_type == 0: # None filter
            pass

        elif filter_type == 1: # Sub filter
            subfilter(data, prior_row_data, row_index + 1, columnbytes, pixel_size)

        elif filter_type == 2: # Up filter
            upfilter(data, prior_row_data, row_index + 1, columnbytes, pixel_size)

        elif filter_type == 3: # Average filter
            avgfilter(data, prior_row_data, row_index + 1, columnbytes, pixel_size)

        elif filter_type == 4: # Paeth filter
            paethfilter(data, prior_row_data, row_index + 1, columnbytes, pixel_size)

        else:
            return None, 'Unsupported PNG filter %d' % filter_type

        row_data = data[row_index + 1 : row_index + 1 + columnbytes] # without filter_type
        prior_row_data = row_data

    for row_index in reversed(rows):
        data.pop(row_index)

    return from_array(data), None

def flate_png_orig(data, predictor=1, columns=1, colors=1, bpc=8):
    ''' PNG prediction is used to make certain kinds of data
        more compressible.  Before the compression, each data
        byte is either left the same, or is set to be a delta
        from the previous byte, or is set to be a delta from
        the previous row.  This selection is done on a per-row
        basis, and is indicated by a compression type byte
        prepended to each row of data.

        Within more recent PDF files, it is normal to use
        this technique for Xref stream objects, which are
        quite regular.
    '''
    columnbytes = ((columns * colors * bpc) + 7) // 8
    data = array.array('B', data)
    rowlen = columnbytes + 1
    if predictor == 15:
        padding = (rowlen - len(data)) % rowlen
        data.extend([0] * padding)
    assert len(data) % rowlen == 0
    rows = xrange(0, len(data), rowlen)
    for row_index in rows:
        offset = data[row_index]
        if offset >= 2:
            if offset > 2:
                return None, 'Unsupported PNG filter %d' % offset
            offset = rowlen if row_index else 0
        if offset:
            for index in xrange(row_index + 1, row_index + rowlen):
                data[index] = (data[index] + data[index - offset]) % 256
    for row_index in reversed(rows):
        data.pop(row_index)
    return from_array(data), None

