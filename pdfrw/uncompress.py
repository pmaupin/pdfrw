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
                    if 10 <= predictor <= 15:
                        data, error = flate_png(data, predictor, columns, colors, bpc)
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

def flate_png_impl(data, predictor=1, columns=1, colors=1, bpc=8):

    # http://www.libpng.org/pub/png/spec/1.2/PNG-Filters.html
    # https://www.w3.org/TR/2003/REC-PNG-20031110/#9Filters
    # Reconstruction functions
    # x: the byte being filtered;
    # a: the byte corresponding to x in the pixel immediately before the pixel containing x (or the byte immediately before x, when the bit depth is less than 8);
    # b: the byte corresponding to x in the previous scanline;
    # c: the byte corresponding to b in the pixel immediately before the pixel containing b (or the byte immediately before b, when the bit depth is less than 8).

    def subfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 1: Sub
        # Recon(x) = Filt(x) + Recon(a)
        for i in xrange(pixel_size, length):
            left = data[start + i - pixel_size]
            data[start + i] = (data[start + i] + left) % 256

    def upfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 2: Up
        # Recon(x) = Filt(x) + Recon(b)
        for i in xrange(length):
            up = prior_row_data[i]
            data[start + i] = (data[start + i] + up) % 256

    def avgfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 3: Avg
        # Recon(x) = Filt(x) + floor((Recon(a) + Recon(b)) / 2)
        for i in xrange(length):
            left = data[start + i - pixel_size] if i >= pixel_size else 0
            up = prior_row_data[i]
            floor = math.floor((left + up) / 2)
            data[start + i] = (data[start + i] + int(floor)) % 256

    def paethfilter(data, prior_row_data, start, length, pixel_size):
        # filter type 4: Paeth
        # Recon(x) = Filt(x) + PaethPredictor(Recon(a), Recon(b), Recon(c))
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
        for i in xrange(length):
            left = data[start + i - pixel_size] if i >= pixel_size else 0
            up = prior_row_data[i]
            up_left = prior_row_data[i - pixel_size] if i >= pixel_size else 0
            data[start + i] = (data[start + i] + paeth_predictor(left, up, up_left)) % 256

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

        prior_row_data = data[row_index + 1 : row_index + 1 + columnbytes] # without filter_type

    for row_index in reversed(rows):
        data.pop(row_index)

    return data, None

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
    d, e = flate_png_impl(data, predictor, columns, colors, bpc)
    if d is not None:
        d = from_array(d)
    return d, e

