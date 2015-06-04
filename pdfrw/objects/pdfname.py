# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

from .pdfobject import PdfObject



class PdfName(object):
    ''' PdfName is a simple way to get a PDF name from a string:

                PdfName.FooBar == PdfObject('/FooBar')
    '''

    whitespace = '\x00 \t\f'
    delimiters = r'()<>{}[\]/%'
    forbidden = whitespace + delimiters

    def __getattr__(self, name):
        return self(name)

    def __call__(self, name, PdfObject=PdfObject):
        obj = PdfObject('/' + name)
        # whitespace and delimiters in the name object should be encoded
        if any((c in self.forbidden) for c in name[1:]):
            encoded = ['/']
            for c in name:
                if c in self.forbidden:
                    encoded.append('#')
                    c = c.encode('hex')
                encoded.append(c)
            obj.encoded = ''.join(encoded)
        return obj

PdfName = PdfName()
