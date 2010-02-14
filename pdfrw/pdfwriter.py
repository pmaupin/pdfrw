#!/usr/bin/env python

# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
The PdfWriter class writes an entire PDF file out to disk.

The writing process is not at all optimized or organized.

An instance of the PdfWriter class has two methods:
    addpage(page)
and
    write(fname)

addpage() assumes that the pages are part of a valid
tree/forest of PDF objects.
'''

try:
    set
except NameError:
    from sets import Set as set

from pdfobjects import PdfName, PdfArray, PdfDict, IndirectPdfDict, PdfObject, PdfString
from pdfcompress import compress

debug = False

class FormatObjects(object):
    ''' FormatObjects performs the actual formatting and disk write.
    '''

    def add(self, obj, visited):
        ''' Add an object to our list, if it's an indirect
            object.  Just format it if not.
        '''
        # Can't hash dicts, so just hash the object ID
        objid = id(obj)

        # Automatically set stream objects to indirect
        if isinstance(obj, PdfDict):
            indirect = obj.indirect or (obj.stream is not None)
        else:
            indirect = getattr(obj, 'indirect', False)

        if not indirect:
            assert objid not in visited, \
                'Circular reference encountered in non-indirect object %s' % repr(obj)
            visited.add(objid)
            result = self.format_obj(obj, visited)
            visited.remove(objid)
            return result

        objnum = self.indirect_dict.get(objid)

        # If we haven't seen the object yet, we need to
        # add it to the indirect object list.
        if objnum is None:
            objlist = self.objlist
            objnum = len(objlist) + 1
            if debug:
                print '  Object', objnum, '\r',
            objlist.append(None)
            self.indirect_dict[objid] = objnum
            objlist[objnum-1] = self.format_obj(obj)
        return '%s 0 R' % objnum

    def format_array(myarray, formatter):
        # Format array data into semi-readable ASCII
        if sum([len(x) for x in myarray]) <= 70:
            return formatter % ' '.join(myarray)
        bigarray = []
        count = 1000000
        for x in myarray:
            lenx = len(x)
            if lenx + count > 70:
                subarray = []
                bigarray.append(subarray)
                count = 0
            count += lenx + 1
            subarray.append(x)
        return formatter % '\n  '.join([' '.join(x) for x in bigarray])
    format_array = staticmethod(format_array)

    def format_obj(self, obj, visited=None):
        ''' format PDF object data into semi-readable ASCII.
            May mutually recurse with add() -- add() will
            return references for indirect objects, and add
            the indirect object to the list.
        '''
        if visited is None:
            visited = set()
        if isinstance(obj, PdfArray):
            myarray = [self.add(x, visited) for x in obj]
            return self.format_array(myarray, '[%s]')
        elif isinstance(obj, PdfDict):
            if self.compress and obj.stream:
                compress([obj])
            myarray = []
            # Jython 2.2.1 has a bug which segfaults when
            # sorting subclassed strings, so we un-subclass them.
            dictkeys = [str(x) for x in obj.iterkeys()]
            dictkeys.sort()
            for key in dictkeys:
                myarray.append(key)
                myarray.append(self.add(obj[key], visited))
            result = self.format_array(myarray, '<<%s>>')
            stream = obj.stream
            if stream is not None:
                result = '%s\nstream\n%s\nendstream' % (result, stream)
            return result
        elif isinstance(obj, basestring) and not hasattr(obj, 'indirect'):
            return PdfString.encode(obj)
        else:
            return str(obj)

    def dump(cls, f, trailer, version='1.3', compress=True):
        self = cls()
        self.compress = compress
        self.indirect_dict = {}
        self.objlist = []

        # The first format of trailer gets all the information,
        # but we throw away the actual trailer formatting.
        self.format_obj(trailer)
        # Now we know the size, so we update the trailer dict
        # and get the formatted data.
        trailer.Size = PdfObject(len(self.objlist) + 1)
        trailer = self.format_obj(trailer)

        # Now we have all the pieces to write out to the file.
        # Keep careful track of the counts while we do it so
        # we can correctly build the cross-reference.

        header = '%%PDF-%s\n%%\xe2\xe3\xcf\xd3\n' % version
        f.write(header)
        offset = len(header)
        offsets = [(0, 65535, 'f')]

        for i, x in enumerate(self.objlist):
            objstr = '%s 0 obj\n%s\nendobj\n' % (i + 1, x)
            offsets.append((offset, 0, 'n'))
            offset += len(objstr)
            f.write(objstr)

        f.write('xref\n0 %s\n' % len(offsets))
        for x in offsets:
            f.write('%010d %05d %s\r\n' % x)
        f.write('trailer\n\n%s\nstartxref\n%s\n%%%%EOF\n' % (trailer, offset))
    dump = classmethod(dump)

class PdfWriter(object):

    _trailer = None

    def __init__(self, version='1.3', compress=True):
        self.pagearray = PdfArray()
        self.compress = compress
        self.version = version

    def addpage(self, page):
        self._trailer = None
        assert page.Type == PdfName.Page
        inheritable = page.inheritable # searches for resources
        self.pagearray.append(
            IndirectPdfDict(
                page,
                Resources = inheritable.Resources,
                MediaBox = inheritable.MediaBox,
                CropBox = inheritable.CropBox,
                Rotate = inheritable.Rotate,
            )
        )
        return self

    addPage = addpage  # for compatibility with pyPdf

    def addpages(self, pagelist):
        for page in pagelist:
            self.addpage(page)
        return self

    def _get_trailer(self):
        trailer = self._trailer
        if trailer is not None:
            return trailer

        # Create the basic object structure of the PDF file
        trailer = PdfDict(
            Root = IndirectPdfDict(
                Type = PdfName.Catalog,
                Pages = IndirectPdfDict(
                    Type = PdfName.Pages,
                    Count = PdfObject(len(self.pagearray)),
                    Kids = self.pagearray
                )
            )
        )
        # Make all the pages point back to the page dictionary
        pagedict = trailer.Root.Pages
        for page in pagedict.Kids:
            page.Parent = pagedict
        self._trailer = trailer
        return trailer

    def _set_trailer(self, trailer):
        self._trailer = trailer

    trailer = property(_get_trailer, _set_trailer)

    def write(self, fname, trailer=None):
        trailer = trailer or self.trailer

        # Dump the data.  We either have a filename or a preexisting
        # file object.
        preexisting = hasattr(fname, 'write')
        f = preexisting and fname or open(fname, 'wb')
        FormatObjects.dump(f, trailer, self.version, self.compress)
        if not preexisting:
            f.close()

if __name__ == '__main__':
    debug = True
    import pdfreader
    x = pdfreader.PdfReader('source.pdf')
    y = PdfWriter()
    for i, page in enumerate(x.pages):
        print '  Adding page', i+1, '\r',
        y.addpage(page)
    print
    y.write('result.pdf')
    print
