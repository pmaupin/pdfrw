# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Converts pdfrw objects into reportlab objects.

Designed for and tested with rl 2.3.

Knows too much about reportlab internals.
What can you do?

The interface to this function is through the makerl() function.

Parameters:
        canv       - a reportlab "canvas" (also accepts a "document")
        pdfobj      - a pdfrw PDF object

Returns:
        A corresponding reportlab object, or if the
        object is a PDF Form XObject, the name to
        use with reportlab for the object.

        Will recursively convert all necessary objects.
        Be careful when converting a page -- if /Parent is set,
        will recursively convert all pages!

Notes:
    1) Original objects are annotated with a
        derived_rl_obj attribute which points to the
        reportlab object.  This keeps multiple reportlab
        objects from being generated for the same pdfobj
        via repeated calls to makerl.  This is great for
        not putting too many objects into the
        new PDF, but not so good if you are modifying
        objects for different pages.  Then you
        need to do your own deep copying (of circular
        structures).  You're on your own.

    2) ReportLab seems weird about FormXObjects.
       They pass around a partial name instead of the
       object or a reference to it.  So we have to
       reach into reportlab and get a number for
       a unique name.  I guess this is to make it
       where you can combine page streams with
       impunity, but that's just a guess.

    3) Updated 1/23/2010 to handle multipass documents
       (e.g. with a table of contents).  These have
       a different doc object on every pass.

'''

from reportlab.pdfbase import pdfdoc as rldocmodule
from .objects import PdfDict, PdfArray, PdfName
from .py23_diffs import convert_store

RLStream = rldocmodule.PDFStream
RLDict = rldocmodule.PDFDictionary
RLArray = rldocmodule.PDFArray


def _makedict(rldoc, pdfobj):
    rlobj = rldict = RLDict()
    if pdfobj.indirect:
        rlobj.__RefOnly__ = 1
        rlobj = rldoc.Reference(rlobj)
    pdfobj.derived_rl_obj[rldoc] = rlobj, None

    for key, value in pdfobj.iteritems():
        rldict[key[1:]] = makerl_recurse(rldoc, value)

    return rlobj


def _makestream(rldoc, pdfobj, xobjtype=PdfName.XObject):
    rldict = RLDict()
    rlobj = RLStream(rldict, convert_store(pdfobj.stream))

    if pdfobj.Type == xobjtype:
        shortname = 'pdfrw_%s' % (rldoc.objectcounter + 1)
        fullname = rldoc.getXObjectName(shortname)
    else:
        shortname = fullname = None
    result = rldoc.Reference(rlobj, fullname)
    pdfobj.derived_rl_obj[rldoc] = result, shortname

    for key, value in pdfobj.iteritems():
        rldict[key[1:]] = makerl_recurse(rldoc, value)

    return result


def _makearray(rldoc, pdfobj):
    rlobj = rlarray = RLArray([])
    if pdfobj.indirect:
        rlobj.__RefOnly__ = 1
        rlobj = rldoc.Reference(rlobj)
    pdfobj.derived_rl_obj[rldoc] = rlobj, None

    mylist = rlarray.sequence
    for value in pdfobj:
        mylist.append(makerl_recurse(rldoc, value))

    return rlobj


def _makestr(rldoc, pdfobj):
    assert isinstance(pdfobj, (float, int, str)), repr(pdfobj)
    # TODO: Add fix for float like in pdfwriter
    return str(getattr(pdfobj, 'encoded', None) or pdfobj)


def makerl_recurse(rldoc, pdfobj):
    docdict = getattr(pdfobj, 'derived_rl_obj', None)
    if docdict is not None:
        value = docdict.get(rldoc)
        if value is not None:
            return value[0]
    if isinstance(pdfobj, PdfDict):
        if pdfobj.stream is not None:
            func = _makestream
        else:
            func = _makedict
        if docdict is None:
            pdfobj.private.derived_rl_obj = {}
    elif isinstance(pdfobj, PdfArray):
        func = _makearray
        if docdict is None:
            pdfobj.derived_rl_obj = {}
    else:
        func = _makestr
    return func(rldoc, pdfobj)


def makerl(canv, pdfobj):
    try:
        rldoc = canv._doc
    except AttributeError:
        rldoc = canv
    rlobj = makerl_recurse(rldoc, pdfobj)
    try:
        name = pdfobj.derived_rl_obj[rldoc][1]
    except AttributeError:
        name = None
    return name or rlobj
