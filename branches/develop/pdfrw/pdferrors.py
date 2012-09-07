# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
PDF Exceptions and error handling
'''

import logging
from exceptions import Exception


logging.basicConfig(
    format='[%(levelname)s] %(filename)s:%(lineno)d %(message)s',
    level=logging.WARNING)

log = logging.getLogger('pdfrw')


class PdfError(Exception):
    "Abstract base class of exceptions thrown by this module"
    pass

class PdfParseError(PdfError):
    "Error thrown by parser/tokenizer"

###########################################################
# Deprecating rest of module as being too specific.
# These errors are most likely not recoverable.  Any
# recovery would have to be really smart, and could parse
# the error text quite easily.

PDF_ERROR_CONTEXT = 10

class PdfInputError(PdfError):
    "Base class for PDF input errors"
    def __init__(self, fdata, loc, msg=''):
        self.fdata = fdata
        self.loc = loc
        self.msg = ''
    def __str__(self):
        fdata = self.fdata
        loc = self.loc
        show = repr(fdata[loc-PDF_ERROR_CONTEXT:loc+PDF_ERROR_CONTEXT])
        sep = ' ' if self.msg else ''
        line = fdata.count('\n', 0, loc) + 1
        line += fdata.count('\r', 0, loc) - fdata.count('\r\n', 0, loc)
        return "%s%snear byte %d (line %d), after %s: %s" % (self.msg, sep, loc, line,
            repr(fdata[loc-PDF_ERROR_CONTEXT:loc]),
            repr(fdata[loc:loc+PDF_ERROR_CONTEXT]))

class PdfStructureError(PdfInputError):
    def __init__(self, fdata, loc, msg, what):
        PdfInputError.__init__(self, fdata, loc, msg + ': ' + repr(what))
        self.msg = msg
        self.what = what

class PdfInvalidCharacterError(PdfInputError):
    def __init__(self, fdata, loc, chars):
        PdfInputError.__init__(self, fdata, loc, 'Char(s): %s' % chars)
        self.chars = chars

class PdfUnexpectedTokenError(PdfInputError):
    def __init__(self, fdata, loc, token):
        PdfInputError.__init__(self, fdata, loc, 'Token: %s' % token)
        self.token = token

class PdfUnexpectedEOFError(PdfInputError):
    def __init__(self, fdata):
        PdfInputError.__init__(self, fdata, len(fdata))

class PdfOutputError(PdfError):
    "Base class for PDF output errors"
    def __init__(self, msg):
        self.msg = ''
    def __str__(self):
        return self.msg

class PdfCircularReferenceError(PdfOutputError):
    def __init__(self, obj):
        PdfOutputError.__init__(self,
            'Circular reference encountered in non-indirect object %s' % repr(obj))
        self.obj = obj

