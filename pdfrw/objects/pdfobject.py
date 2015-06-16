# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details


class PdfObject(str):
    ''' A PdfObject is a textual representation of any PDF file object
        other than an array, dict or string. It has an indirect attribute
        which defaults to False.
    '''
    indirect = False
