# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
The PdfBuilder class builds new PDF structures to be
sent out to disk by a serializer.

PdfBuilder aims to know a bit about how the PDF is put
together, e.g. how pages are placed in the document.

A separate serializer should know how to send a PDF to a
file, but not know or care about how the pieces fit together.

PdfWriter instantiates the serializer and the builder,
and should not really know much about the internals
of either one.
'''

from .objects import (PdfName, PdfArray, PdfDict, IndirectPdfDict,
                      PdfObject, PdfString)
from .errors import PdfOutputError, log

class PdfBuilder(object):

    def __init__(self):
        pagearray = self.pagearray = PdfArray()
        pagedict = self.pagedict = IndirectPdfDict(
            Type=PdfName.Pages,
            Kids=pagearray,
            Count=0,
        )
        root = self.root = IndirectPdfDict(
            Type=PdfName.Catalog,
            Pages=pagedict,
        )
        trailer = self.trailer = PdfDict(
            Root=root
        )

    def addpage(self, page):
        if page.Type != PdfName.Page:
            raise PdfOutputError('Bad /Type:  Expected %s, found %s'
                                 % (PdfName.Page, page.Type))
        inheritable = page.inheritable  # searches for resources

        newpage = IndirectPdfDict(
            page,
            Resources=inheritable.Resources,
            MediaBox=inheritable.MediaBox,
            CropBox=inheritable.CropBox,
            Rotate=inheritable.Rotate,
        )
        # Unhook page from old hierarchy.
        if newpage.Parent:
            newpage.B = newpage.Annots = None
        self.pagearray.append(newpage)
        pagedict = self.pagedict
        newpage.Parent = pagedict
        pagedict.Count += 1

    addPage = addpage  # for compatibility with pyPdf

    def addpages(self, pagelist):
        for page in pagelist:
            self.addpage(page)

    def finalize(self):
        """ Override this in a subclass to finish up any required work before
            the document is serialized.
        """
