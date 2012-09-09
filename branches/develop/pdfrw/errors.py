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
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class PdfParseError(PdfError):
    "Error thrown by parser/tokenizer"

class PdfOutputError(PdfError):
    "Error thrown by PDF writer"
