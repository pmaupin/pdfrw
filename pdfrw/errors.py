# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
PDF Exceptions and error handling
'''

import logging


logging.basicConfig(
    format='[%(levelname)s] %(filename)s:%(lineno)d %(message)s',
           level=logging.WARNING)

log = logging.getLogger('pdfrw')


class PdfError(Exception):
    "Abstract base class of exceptions thrown by this module"

    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


class PdfParseError(PdfError):
    "Error thrown by parser/tokenizer"


class PdfOutputError(PdfError):
    "Error thrown by PDF writer"


class PdfNotImplementedError(PdfError):
    "Error thrown on missing features"
