# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2012 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Objects that can occur in PDF files.  The most important
objects are arrays and dicts.  Either of these can be
indirect or not, and dicts could have an associated
stream.
'''
from pdfrw.objects.pdfname import PdfName
from pdfrw.objects.pdfdict import PdfDict, IndirectPdfDict
from pdfrw.objects.pdfarray import PdfArray
from pdfrw.objects.pdfobject import PdfObject
from pdfrw.objects.pdfstring import PdfString
from pdfrw.objects.pdfindirect import PdfIndirect
