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
        rldoc       - a reportlab "document"
        pdfobj      - a top-level pdfrw PDF object

Returns:
        A corresponding reportlab object.

Notes:
    1) Original objects are annotated with a
        _rl_obj attribute which points to the
        reportlab object.  This is great for
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
    assert pdfobj._rl_obj is None

    rlobj = rldict = RLDict()
    if pdfobj.indirect:
        rlobj.__RefOnly__ = 1
        rlobj = rldoc.Reference(rlobj)
    pdfobj.private._rl_obj = rlobj

    for key, value in pdfobj.iteritems():
        rldict[key[1:]] = makerl(rldoc, value)

    return rlobj

def _makestream(rldoc, pdfobj, xobjtype=PdfName.XObject):
    assert isinstance(pdfobj, PdfDict)
    assert pdfobj.stream is not None
    assert pdfobj._rl_obj is None

    rldict = RLDict()
    rlobj = RLStream(rldict, pdfobj.stream)

    if pdfobj.Type == xobjtype:
        name = 'pdfrw_%s' % (rldoc.objectcounter+1)
        pdfobj.private.rl_xobj_name = name
        name = rldoc.getXObjectName(name)
    else:
        name = None
    result = rldoc.Reference(rlobj, name)
    pdfobj.private._rl_obj = result

    for key, value in pdfobj.iteritems():
        rldict[key[1:]] = makerl(rldoc, value)

    return result

def _makearray(rldoc, pdfobj):
    assert isinstance(pdfobj, PdfArray)
    assert not hasattr(pdfobj, '_rl_obj')

    rlobj = rlarray = RLArray([])
    if pdfobj.indirect:
        rlobj.__RefOnly__ = 1
        rlobj = rldoc.Reference(rlobj)
    pdfobj._rl_obj = rlobj

    mylist = rlobj.sequence
    for value in pdfobj:
        mylist.append(makerl(rldoc, value))

    return rlobj

def _makestr(rldoc, pdfobj):
    assert isinstance(pdfobj, (float, int, str)), repr(pdfobj)
    return pdfobj

def makerl(rldoc, pdfobj):
    value = getattr(pdfobj, '_rl_obj', None)
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
