# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Objects that can occur in PDF files.  The most important
objects are arrays and dicts.  Either of these can be
indirect or not, and dicts could have an associated
stream.
'''
from .pdfname import PdfName
from .pdfdict import PdfDict, IndirectPdfDict
from .pdfarray import PdfArray
from .pdfobject import PdfObject
from .pdfstring import PdfString
from .pdfindirect import PdfIndirect

__all__ = """PdfName PdfDict IndirectPdfDict PdfArray
             PdfObject PdfString PdfIndirect""".split()
