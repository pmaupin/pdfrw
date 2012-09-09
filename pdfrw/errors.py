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

