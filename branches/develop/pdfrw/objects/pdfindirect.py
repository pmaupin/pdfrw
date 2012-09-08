# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2012 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

class PdfIndirect(tuple):
    ''' A placeholder for an object that hasn't been read in yet.
        The object itself is the (object number, generation number) tuple.
        The attributes include information about where the object is
        referenced from and the file object to retrieve the real object from.
    '''

    def __init__(self, reader):
        self.reader = reader

    def real_value(self):
        return reader(self)
