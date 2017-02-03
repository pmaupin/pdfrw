# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''

This module contains code to build PDF "Form XObjects".

A Form XObject allows a fragment from one PDF file to be cleanly
included in another PDF file.

Reference for syntax: "Parameters for opening PDF files" from SDK 8.1

        http://www.adobe.com/devnet/acrobat/pdfs/pdf_open_parameters.pdf

        supported 'page=xxx', 'viewrect=<left>,<top>,<width>,<height>'

        Also supported by this, but not by Adobe:
            'rotate=xxx'  where xxx in [0, 90, 180, 270]

        Units are in points


Reference for content:   Adobe PDF reference, sixth edition, version 1.7

        http://www.adobe.com/devnet/acrobat/pdfs/pdf_reference_1-7.pdf

        Form xobjects discussed chapter 4.9, page 355
'''

from .objects import PdfDict, PdfArray, PdfName
from .pdfreader import PdfReader
from .errors import log, PdfNotImplementedError
from .py23_diffs import iteritems
from .uncompress import uncompress
from .compress import compress


class ViewInfo(object):
    ''' Instantiate ViewInfo with a uri, and it will parse out
        the filename, page, and viewrect into object attributes.

        Note 1:
            Viewrects follow the adobe definition.  (See reference
            above). They are arrays of 4 numbers:

            - Distance from left of document in points
            - Distance from top (NOT bottom) of document in points
            - Width of rectangle in points
            - Height of rectangle in points

        Note 2:
            For simplicity, Viewrects can also be specified
            in fractions of the document.  If every number in
            the viewrect is between 0 and 1 inclusive, then
            viewrect elements 0 and 2 are multiplied by the
            mediabox width before use, and viewrect elements
            1 and 3 are multiplied by the mediabox height before
            use.

        Note 3:
            By default, an XObject based on the view will be
            cacheable.  It should not be cacheable if the XObject
            will be subsequently modified.
    '''
    doc = None
    docname = None
    page = None
    viewrect = None
    rotate = None
    cacheable = True

    def __init__(self, pageinfo='', **kw):
        pageinfo = pageinfo.split('#', 1)
        if len(pageinfo) == 2:
            pageinfo[1:] = pageinfo[1].replace('&', '#').split('#')
        for key in 'page viewrect'.split():
            if pageinfo[0].startswith(key + '='):
                break
        else:
            self.docname = pageinfo.pop(0)
        for item in pageinfo:
            key, value = item.split('=')
            key = key.strip()
            value = value.replace(',', ' ').split()
            if key in ('page', 'rotate'):
                assert len(value) == 1
                setattr(self, key, int(value[0]))
            elif key == 'viewrect':
                assert len(value) == 4
                setattr(self, key, [float(x) for x in value])
            else:
                log.error('Unknown option: %s', key)
        for key, value in iteritems(kw):
            assert hasattr(self, key), key
            setattr(self, key, value)


def get_rotation(rotate):
    ''' Return clockwise rotation code:
          0 = unrotated
          1 = 90 degrees
          2 = 180 degrees
          3 = 270 degrees
    '''
    try:
        rotate = int(rotate)
    except (ValueError, TypeError):
        return 0
    if rotate % 90 != 0:
        return 0
    return rotate // 90


def rotate_point(point, rotation):
    ''' Rotate an (x,y) coordinate clockwise by a
        rotation code specifying a multiple of 90 degrees.
    '''
    if rotation & 1:
        point = point[1], -point[0]
    if rotation & 2:
        point = -point[0], -point[1]
    return point


def rotate_rect(rect, rotation):
    ''' Rotate both points within the rectangle, then normalize
        the rectangle by returning the new lower left, then new
        upper right.
    '''
    rect = rotate_point(rect[:2], rotation) + rotate_point(rect[2:], rotation)
    return (min(rect[0], rect[2]), min(rect[1], rect[3]),
            max(rect[0], rect[2]), max(rect[1], rect[3]))


def getrects(inheritable, pageinfo, rotation):
    ''' Given the inheritable attributes of a page and
        the desired pageinfo rectangle, return the page's
        media box and the calculated boundary (clip) box.
    '''
    mbox = tuple([float(x) for x in inheritable.MediaBox])
    cbox = tuple([float(x) for x in (inheritable.CropBox or mbox)])
    vrect = pageinfo.viewrect
    if vrect is not None:
        # Rotate the media box to match what the user sees,
        # figure out the clipping box, then rotate back
        mleft, mbot, mright, mtop = rotate_rect(cbox, rotation)
        x, y, w, h = vrect

        # Support operations in fractions of a page
        if 0 <= min(vrect) < max(vrect) <= 1:
            mw = mright - mleft
            mh = mtop - mbot
            x *= mw
            w *= mw
            y *= mh
            h *= mh

        cleft = mleft + x
        ctop = mtop - y
        cright = cleft + w
        cbot = ctop - h
        cbox = (max(mleft, cleft), max(mbot, cbot),
                min(mright, cright), min(mtop, ctop))
        cbox = rotate_rect(cbox, -rotation)
    return mbox, cbox


def _build_cache(contents, allow_compressed):
    ''' Build a new dictionary holding the stream,
        and save it along with private cache info.
        Assumes validity has been pre-checked if
        we have a non-None xobj_copy.

        Also, the spec says nothing about nested arrays,
        so we assume those don't exist until we see one
        in the wild.
    '''
    try:
        xobj_copy = contents.xobj_copy
    except AttributeError:
        # Should have a PdfArray here...
        array = contents
        private = contents
    else:
        # Should have a PdfDict here -- might or might not have cache copy
        if xobj_copy is not None:
            return xobj_copy
        array = [contents]
        private = contents.private

    # If we don't allow compressed objects, OR if we have multiple compressed
    # objects, we try to decompress them, and fail if we cannot do that.

    if not allow_compressed or len(array) > 1:
        keys = set(x[0] for cdict in array for x in iteritems(cdict))
        was_compressed = len(keys) > 1
        if was_compressed:
            # Make copies of the objects before we uncompress them.
            array = [PdfDict(x) for x in array]
            if not uncompress(array):
                raise PdfNotImplementedError(
                    'Xobjects with these compression parameters not supported: %s' %
                    keys)
    
    xobj_copy = PdfDict(array[0])
    xobj_copy.private.xobj_cachedict = {}
    private.xobj_copy = xobj_copy

    if len(array) > 1:
        newstream = '\n'.join(x.stream for x in array)
        newlength = sum(int(x.Length) for x in array) + len(array) - 1
        assert newlength == len(newstream)
        xobj_copy.stream = newstream
        if was_compressed and allow_compressed:
            compress(xobj_copy)

    return xobj_copy


def _cache_xobj(contents, resources, mbox, bbox, rotation, cacheable=True):
    ''' Return a cached Form XObject, or create a new one and cache it.
        Adds private members x, y, w, h
    '''
    cachedict = contents.xobj_cachedict
    cachekey = mbox, bbox, rotation
    result = cachedict.get(cachekey) if cacheable else None
    if result is None:
        # If we are not getting a full page, or if we are going to
        # modify the results, first retrieve an underlying Form XObject
        # that represents the entire page, so that we are not copying
        # the full page data into the new file multiple times
        func = (_get_fullpage, _get_subpage)[mbox != bbox or not cacheable]
        result = PdfDict(
            func(contents, resources, mbox),
            Type=PdfName.XObject,
            Subtype=PdfName.Form,
            FormType=1,
            BBox=PdfArray(bbox),
        )
        rect = bbox
        if rotation:
            matrix = (rotate_point((1, 0), rotation) +
                      rotate_point((0, 1), rotation))
            result.Matrix = PdfArray(matrix + (0, 0))
            rect = rotate_rect(rect, rotation)

        private = result.private
        private.x = rect[0]
        private.y = rect[1]
        private.w = rect[2] - rect[0]
        private.h = rect[3] - rect[1]
        if cacheable:
            cachedict[cachekey] = result
    return result


def _get_fullpage(contents, resources, mbox):
    ''' fullpage is easy.  Just copy the contents,
        set up the resources, and let _cache_xobj handle the
        rest.
    '''
    return PdfDict(contents, Resources=resources)


def _get_subpage(contents, resources, mbox):
    ''' subpages *could* be as easy as full pages, but we
        choose to complicate life by creating a Form XObject
        for the page, and then one that references it for
        the subpage, on the off-chance that we want multiple
        items from the page.
    '''
    return PdfDict(
        stream='/FullPage Do\n',
        Resources=PdfDict(
            XObject=PdfDict(
                FullPage=_cache_xobj(contents, resources, mbox, mbox, 0)
            )
        )
    )


def pagexobj(page, viewinfo=ViewInfo(), allow_compressed=True):
    ''' pagexobj creates and returns a Form XObject for
        a given view within a page (Defaults to entire page.)

        pagexobj is passed a page and a viewrect.
    '''
    inheritable = page.inheritable
    resources = inheritable.Resources
    rotation = get_rotation(inheritable.Rotate)
    mbox, bbox = getrects(inheritable, viewinfo, rotation)
    rotation += get_rotation(viewinfo.rotate)
    contents = _build_cache(page.Contents, allow_compressed)
    return _cache_xobj(contents, resources, mbox, bbox, rotation,
                       viewinfo.cacheable)


def docxobj(pageinfo, doc=None, allow_compressed=True):
    ''' docinfo reads a page out of a document and uses
        pagexobj to create the Form XObject based on
        the page.

        This is a convenience function for things like
        rst2pdf that want to be able to pass in textual
        filename/location descriptors and don't want to
        know about using PdfReader.

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
        doc = pageinfo.doc = PdfReader(pageinfo.docname,
                                       decompress=not allow_compressed)
    assert isinstance(doc, PdfReader)

    sourcepage = doc.pages[(pageinfo.page or 1) - 1]
    return pagexobj(sourcepage, pageinfo, allow_compressed)


class CacheXObj(object):
    ''' Use to keep from reparsing files over and over,
        and to keep from making the output too much
        bigger than it ought to be by replicating
        unnecessary object copies.

        This is a convenience function for things like
        rst2pdf that want to be able to pass in textual
        filename/location descriptors and don't want to
        know about using PdfReader.
    '''
    def __init__(self, decompress=False):
        ''' Set decompress true if you need
            the Form XObjects to be decompressed.
            Will decompress what it can and scream
            about the rest.
        '''
        self.cached_pdfs = {}
        self.decompress = decompress

    def load(self, sourcename):
        ''' Load a Form XObject from a uri
        '''
        info = ViewInfo(sourcename)
        fname = info.docname
        pcache = self.cached_pdfs
        doc = pcache.get(fname)
        if doc is None:
            doc = pcache[fname] = PdfReader(fname, decompress=self.decompress)
        return docxobj(info, doc, allow_compressed=not self.decompress)
