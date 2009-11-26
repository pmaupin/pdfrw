# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''

Reference for syntax: "Parameters for opening PDF files" from SDK 8.1

        http://www.adobe.com/devnet/acrobat/pdfs/pdf_open_parameters.pdf

        supported 'page=xxx', 'viewrect=<left>,<top>,<width>,<height>'

        Units are in points

Reference for content:   Adobe PDF reference, sixth edition, version 1.7

        http://www.adobe.com/devnet/acrobat/pdfs/pdf_reference_1-7.pdf

        Form xobjects discussed chapter 4.9, page 355
'''

from pdfobjects import PdfDict, PdfArray, PdfName
from pdfreader import PdfReader

class ViewInfo(object):
    ''' Instantiate ViewInfo with a uri, and it will parse out
        the filename, page, and viewrect into object attributes.
    '''
    doc = None
    docname = None
    page = None
    viewrect = None

    def __init__(self, pageinfo):
        pageinfo=pageinfo.split('#',1)
        if len(pageinfo) == 2:
            pageinfo[1:] = pageinfo[1].replace('&', '#').split('#')
        for key in 'page viewrect'.split():
            if pageinfo[0].startswith(key+'='):
                break
        else:
            self.docname = pageinfo.pop(0)
        for item in pageinfo:
            key, value = item.split('=')
            key = key.strip()
            value = value.replace(',', ' ').split()
            if key == 'page':
                assert len(value) == 1
                setattr(self, key, int(value[0]))
            elif key == 'viewrect':
                assert len(value) == 4
                setattr(self, key, [float(x) for x in value])
            else:
                log.error('Unknown option: %s', key)

def xobj(pageinfo, doc=None, allow_compressed=True):
    ''' xobj creates and returns an actual Form XObject.
        Can work standalone, or in conjunction with
        the CacheXObj class (below).
    '''
    if not isinstance(pageinfo, ViewInfo):
        pageinfo = ViewInfo(pageinfo)

    # If we're explicitly passed a document,
    # make sure we don't have one implicitly as well.
    # If no implicit or explicit doc, then read one in
    # from the filename.
    if doc is not None:
        assert pageinfo.doc is None
        pageinfo.doc = doc
    elif pageinfo.doc is not None:
        doc = pageinfo.doc
    else:
        doc = pageinfo.doc = PdfReader(pageinfo.docname)
    assert isinstance(doc, PdfReader)

    sourcepage = doc.pages[(pageinfo.page or 1) - 1]
    sourceinfo = sourcepage.search

    result = PdfDict(sourcepage.Contents)
    # Make sure the only attribute is length
    # All the filters must have been executed
    assert int(result.Length) == len(result.stream)
    if not allow_compressed:
        assert len([x for x in result.iteritems()]) == 1
    result.Type = PdfName.XObject
    result.Subtype = PdfName.Form
    result.FormType = 1
    result.Resources = sourceinfo.Resources

    mbox = sourceinfo.MediaBox
    vrect = pageinfo.viewrect
    if vrect is None:
        cbox = [float(x) for x in sourceinfo.CropBox or mbox]
    else:
        mleft, mbot, mright, mtop = [float(x) for x in mbox]
        x, y, w, h = vrect
        cleft = mleft + x
        ctop = mtop - y
        cright = cleft + w
        cbot = ctop - h
        cbox = max(mleft, cleft), max(mbot, cbot), min(mright, cright), min(mtop, ctop)
    result.BBox = PdfArray(cbox)
    return result


class CacheXObj(object):
    ''' Use to keep from reparsing files over and over,
        and to keep from making the output too much
        bigger than it ought to be by replicating
        unnecessary object copies.
    '''
    def __init__(self, decompress=False):
        ''' Set decompress true if you need
            the Form XObjects to be decompressed.
            Will decompress what it can and scream
            about the rest.
        '''
        self.cached_pdfs = {}
        self.cached_xobjs = {}
        self.decompress = decompress

    def load(self, sourcename):
        ''' Load a Form XObject from a uri
        '''
        xcache = self.cached_xobjs
        result = xcache.get(sourcename)
        if result is not None:
            return result

        info = ViewInfo(sourcename)
        fname = info.docname

        pcache = self.cached_pdfs
        doc = pcache.get(fname)
        if doc is None:
            doc = pcache[fname] = PdfReader(fname, decompress=self.decompress)

        result = xcache[sourcename] = xobj(info, doc,
                                        allow_compressed=not self.decompress)
        return result
