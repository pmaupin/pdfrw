# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details


class _NotLoaded(object):
    pass


class PdfIndirect(tuple):
    ''' A placeholder for an object that hasn't been read in yet.
        The object itself is the (object number, generation number) tuple.
        The attributes include information about where the object is
        referenced from and the file object to retrieve the real object from.
    '''
    value = _NotLoaded

    def real_value(self, NotLoaded=_NotLoaded):
        value = self.value
        if value is NotLoaded:
            value = self.value = self._loader(self)
        return value
