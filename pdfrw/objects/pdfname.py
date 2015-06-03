# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

from .pdfobject import PdfObject


class PdfName(object):
    ''' PdfName is a simple way to get a PDF name from a string:

                PdfName.FooBar == PdfObject('/FooBar')
    '''
    def __getattr__(self, name):
        return self(name)

    def __call__(self, name, PdfObject=PdfObject):
        return PdfObject('/' + name)

PdfName = PdfName()
