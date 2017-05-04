# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

from .pdfindirect import PdfIndirect
from .pdfobject import PdfObject


def _resolved():
    pass


class PdfArray(list):
    ''' A PdfArray maps the PDF file array object into a Python list.
        It has an indirect attribute which defaults to False.
    '''
    indirect = False

    def __init__(self, source=[]):
        self._resolve = self._resolver
        self.extend(source)

    def _resolver(self, isinstance=isinstance, enumerate=enumerate,
                  listiter=list.__iter__, PdfIndirect=PdfIndirect,
                  resolved=_resolved, PdfNull=PdfObject('null')):
        for index, value in enumerate(list.__iter__(self)):
                if isinstance(value, PdfIndirect):
                    value = value.real_value()
                    if value is None:
                        value = PdfNull
                    self[index] = value
        self._resolve = resolved

    def __getitem__(self, index, listget=list.__getitem__):
        self._resolve()
        return listget(self, index)

    try:
        def __getslice__(self, i, j, listget=list.__getslice__):
            self._resolve()
            return listget(self, i, j)
    except AttributeError:
        pass

    def __iter__(self, listiter=list.__iter__):
        self._resolve()
        return listiter(self)

    def count(self, item):
        self._resolve()
        return list.count(self, item)

    def index(self, item):
        self._resolve()
        return list.index(self, item)

    def remove(self, item):
        self._resolve()
        return list.remove(self, item)

    def sort(self, *args, **kw):
        self._resolve()
        return list.sort(self, *args, **kw)

    def pop(self, *args):
        self._resolve()
        return list.pop(self, *args)

    def __reversed__(self):
        self._resolve()
        return list.__reversed__(self)
