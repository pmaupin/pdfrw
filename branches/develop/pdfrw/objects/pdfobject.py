# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2012 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

class PdfObject(str):
    ''' A PdfObject is a textual representation of any PDF file object
        other than an array, dict or string. It has an indirect attribute
        which defaults to False.
    '''
    indirect = False
