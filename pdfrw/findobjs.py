# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

''' This module contains a function to find all the XObjects
    in a document, and another function that will wrap them
    in page objects.
'''

from .objects import PdfDict, PdfArray, PdfName


def find_objects(source, valid_types=(PdfName.XObject, None),
                 valid_subtypes=(PdfName.Form, PdfName.Image),
                 no_follow=(PdfName.Parent,),
                 isinstance=isinstance, id=id, sorted=sorted,
                 reversed=reversed, PdfDict=PdfDict):
    '''
        Find all the objects of a particular kind in a document
        or array.  Defaults to looking for Form and Image XObjects.

        This could be done recursively, but some PDFs
        are quite deeply nested, so we do it without
        recursion.

        Note that we don't know exactly where things appear on pages,
        but we aim for a sort order that is (a) mostly in document order,
        and (b) reproducible.  For arrays, objects are processed in
        array order, and for dicts, they are processed in key order.
    '''
    container = (PdfDict, PdfArray)

    # Allow passing a list of pages, or a dict
    if isinstance(source, PdfDict):
        source = [source]
    else:
        source = list(source)

    visited = set()
    source.reverse()
    while source:
        obj = source.pop()
        if not isinstance(obj, container):
            continue
        myid = id(obj)
        if myid in visited:
            continue
        visited.add(myid)
        if isinstance(obj, PdfDict):
            if obj.Type in valid_types and obj.Subtype in valid_subtypes:
                yield obj
            obj = [y for (x, y) in sorted(obj.iteritems())
                   if x not in no_follow]
        else:
            # TODO: This forces resolution of any indirect objects in
            # the array.  It may not be necessary.  Don't know if
            # reversed() does any voodoo underneath the hood.
            # It's cheap enough for now, but might be removeable.
            obj and obj[0]
        source.extend(reversed(obj))


def wrap_object(obj, width, margin):
    ''' Wrap an xobj in its own page object.
    '''
    fmt = 'q %s 0 0 %s %s %s cm /MyImage Do Q'
    contents = PdfDict(indirect=True)
    subtype = obj.Subtype
    if subtype == PdfName.Form:
        contents._stream = obj.stream
        contents.Length = obj.Length
        contents.Filter = obj.Filter
        contents.DecodeParms = obj.DecodeParms
        resources = obj.Resources
        mbox = obj.BBox
    elif subtype == PdfName.Image:  # Image
        xoffset = margin[0]
        yoffset = margin[1]
        cw = width - margin[0] - margin[2]
        iw, ih = float(obj.Width), float(obj.Height)
        ch = 1.0 * cw / iw * ih
        height = ch + margin[1] + margin[3]
        p = tuple(('%.9f' % x).rstrip('0').rstrip('.') for x in (cw, ch, xoffset, yoffset))
        contents.stream = fmt % p
        resources = PdfDict(XObject=PdfDict(MyImage=obj))
        mbox = PdfArray((0, 0, width, height))
    else:
        raise TypeError("Expected Form or Image XObject")

    return PdfDict(
        indirect=True,
        Type=PdfName.Page,
        MediaBox=mbox,
        Resources=resources,
        Contents=contents,
        )


def trivial_xobjs(maxignore=300):
    ''' Ignore XObjects that trivially contain other XObjects.
    '''
    ignore = set('q Q cm Do'.split())
    Image = PdfName.Image

    def check(obj):
        if obj.Subtype == Image:
            return False
        s = obj.stream
        if len(s) < maxignore:
            s = (x for x in s.split() if not x.startswith('/') and
                 x not in ignore)
            s = (x.replace('.', '').replace('-', '') for x in s)
            if not [x for x in s if not x.isdigit()]:
                return True
    return check


def page_per_xobj(xobj_iter, width=8.5 * 72, margin=0.0 * 72,
                  image_only=False, ignore=trivial_xobjs(),
                  wrap_object=wrap_object):
    ''' page_per_xobj wraps every XObj found
        in its own page object.
        width and margin are used to set image sizes.
    '''
    try:
        iter(margin)
    except:
        margin = [margin]
    while len(margin) < 4:
        margin *= 2

    if isinstance(xobj_iter, (list, dict)):
        xobj_iter = find_objects(xobj_iter)
    for obj in xobj_iter:
        if not ignore(obj):
            if not image_only or obj.Subtype == PdfName.IMage:
                yield wrap_object(obj, width, margin)
