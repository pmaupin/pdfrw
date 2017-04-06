# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

import re

from ..errors import log

warn = log.warning


class BasePdfName(str):
    ''' A PdfName is an identifier that starts with
        a slash.

        If a PdfName has illegal space or delimiter characters,
        then it will be decorated with an "encoded" attribute that
        has those characters properly escaped as #<hex><hex>

        The "encoded" attribute is what is sent out to a PDF file,
        the non-encoded main object is what is compared for equality
        in a PDF dictionary.
    '''

    indirect = False
    encoded = None

    whitespace = '\x00 \t\f\r\n'
    delimiters = '()<>{}[]/%'
    forbidden = list(whitespace) + list('\\' + x for x in delimiters)
    remap = dict((x, '#%02X' % ord(x)) for x in (whitespace + delimiters))
    split_to_encode = re.compile('(%s)' % '|'.join(forbidden)).split
    split_to_decode = re.compile(r'\#([0-9A-Fa-f]{2})').split

    def __new__(cls, name, pre_encoded=True, remap=remap,
                join=''.join, new=str.__new__, chr=chr, int=int,
                split_to_encode=split_to_encode,
                split_to_decode=split_to_decode,
                ):
        ''' We can build a PdfName from scratch, or from
            a pre-encoded name (e.g. coming in from a file).
        '''
        # Optimization for normal case
        if name[1:].isalnum():
            return new(cls, name)
        encoded = name
        if pre_encoded:
            if '#' in name:
                substrs = split_to_decode(name)
                substrs[1::2] = (chr(int(x, 16)) for x in substrs[1::2])
                name = join(substrs)
        else:
            encoded = split_to_encode(encoded)
            encoded[3::2] = (remap[x] for x in encoded[3::2])
            encoded = join(encoded)
        self = new(cls, name)
        if encoded != name:
            self.encoded = encoded
        return self


# We could have used a metaclass, but this matches what
# we were doing historically.

class PdfName(object):
    ''' Two simple ways to get a PDF name from a string:

                x = PdfName.FooBar
                x = pdfName('FooBar')

        Either technique will return "/FooBar"

    '''

    def __getattr__(self, name, BasePdfName=BasePdfName):
        return BasePdfName('/' + name, False)

    def __call__(self, name, BasePdfName=BasePdfName):
        return BasePdfName('/' + name, False)

PdfName = PdfName()
