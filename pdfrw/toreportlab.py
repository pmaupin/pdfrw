# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
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

makerl(rldoc, pdfobj):

'''

from reportlab.pdfbase import pdfdoc as rldocmodule
from pdfobjects import PdfDict, PdfArray, PdfName

RLStream = rldocmodule.PDFStream
RLDict = rldocmodule.PDFDictionary
RLArray = rldocmodule.PDFArray


def _makedict(rldoc, pdfobj):
    assert isinstance(pdfobj, PdfDict)
    assert pdfobj.stream is None
    assert pdfobj.derived_rl_obj is None

    rlobj = rldict = RLDict()
    if pdfobj.indirect:
        rlobj.__RefOnly__ = 1
        rlobj = rldoc.Reference(rlobj)
    pdfobj.private.derived_rl_obj = rlobj

    for key, value in pdfobj.iteritems():
        rldict[key[1:]] = makerl_recurse(rldoc, value)

    return rlobj

def _makestream(rldoc, pdfobj, xobjtype=PdfName.XObject):
    assert isinstance(pdfobj, PdfDict)
    assert pdfobj.stream is not None
    assert pdfobj.derived_rl_obj is None

    rldict = RLDict()
    rlobj = RLStream(rldict, pdfobj.stream)

    if pdfobj.Type == xobjtype:
        name = 'pdfrw_%s' % (rldoc.objectcounter+1)
        pdfobj.private.rl_xobj_name = name
        name = rldoc.getXObjectName(name)
    else:
        name = None
    result = rldoc.Reference(rlobj, name)
    pdfobj.private.derived_rl_obj = result

    for key, value in pdfobj.iteritems():
        rldict[key[1:]] = makerl_recurse(rldoc, value)

    return result

def _makearray(rldoc, pdfobj):
    assert isinstance(pdfobj, PdfArray)
    assert not hasattr(pdfobj, 'derived_rl_obj')

    rlobj = rlarray = RLArray([])
    if pdfobj.indirect:
        rlobj.__RefOnly__ = 1
        rlobj = rldoc.Reference(rlobj)
    pdfobj.derived_rl_obj = rlobj

    mylist = rlobj.sequence
    for value in pdfobj:
        mylist.append(makerl_recurse(rldoc, value))

    return rlobj

def _makestr(rldoc, pdfobj):
    assert isinstance(pdfobj, (float, int, str)), repr(pdfobj)
    return pdfobj

def makerl_recurse(rldoc, pdfobj):
    value = getattr(pdfobj, 'derived_rl_obj', None)
    if value is not None:
        return value
    if isinstance(pdfobj, PdfDict):
        if pdfobj.stream is not None:
            func = _makestream
        else:
            func = _makedict
    elif isinstance(pdfobj, PdfArray):
        func = _makearray
    else:
        func = _makestr
    return func(rldoc, pdfobj)

def makerl(canv, pdfobj):
    try:
        doc = canv._doc
    except AttributeError:
        doc = canv
    rlobj = makerl_recurse(doc, pdfobj)
    name = pdfobj.rl_xobj_name
    return name or rlobj
