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

from pdfrw.objects import PdfName, PdfArray, PdfDict, IndirectPdfDict, PdfObject, PdfString
from pdfrw.compress import compress as do_compress
from pdfrw.errors import PdfOutputError, log

NullObject = PdfObject('null')
NullObject.indirect = True
NullObject.Type = 'Null object'

def FormatObjects(f, trailer, version='1.3', compress=True, killobj=(),
        id=id, isinstance=isinstance, getattr=getattr,len=len,
        sum=sum, set=set, str=str, basestring=basestring,
        hasattr=hasattr, repr=repr, enumerate=enumerate,
        list=list, dict=dict, tuple=tuple,
        do_compress=do_compress, PdfArray=PdfArray,
        PdfDict=PdfDict, PdfObject=PdfObject, encode=PdfString.encode):
    ''' FormatObjects performs the actual formatting and disk write.
        Should be a class, was a class, turned into nested functions
        for performace (to reduce attribute lookups).
    '''

    def add(obj):
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
            if objid in visited:
                log.warning('Replicating direct %s object, should be indirect for optimal file size' % type(obj))
                obj = type(obj)(obj)
                objid = id(obj)
            visiting(objid)
            result = format_obj(obj)
            leaving(objid)
            return result

        objnum = indirect_dict_get(objid)

        # If we haven't seen the object yet, we need to
        # add it to the indirect object list.
        if objnum is None:
            swapped = swapobj(objid)
            if swapped is not None:
                old_id = objid
                obj = swapped
                objid = id(obj)
                objnum = indirect_dict_get(objid)
                if objnum is not None:
                    indirect_dict[old_id] = objnum
                    return '%s 0 R' % objnum
            objnum = len(objlist) + 1
            objlist_append(None)
            indirect_dict[objid] = objnum
            deferred.append((objnum-1, obj))
        return '%s 0 R' % objnum

    def format_array(myarray, formatter):
        # Format array data into semi-readable ASCII
        if sum([len(x) for x in myarray]) <= 70:
            return formatter % space_join(myarray)
        return format_big(myarray, formatter)

    def format_big(myarray, formatter):
        bigarray = []
        count = 1000000
        for x in myarray:
            lenx = len(x) + 1
            count += lenx
            if count > 71:
                subarray = []
                bigarray.append(subarray)
                count = lenx
            subarray.append(x)
        return formatter % lf_join([space_join(x) for x in bigarray])

    def format_obj(obj):
        ''' format PDF object data into semi-readable ASCII.
            May mutually recurse with add() -- add() will
            return references for indirect objects, and add
            the indirect object to the list.
        '''
        while 1:
            if isinstance(obj, (list, dict, tuple)):
                if isinstance(obj, PdfArray):
                    myarray = [add(x) for x in obj]
                    return format_array(myarray, '[%s]')
                elif isinstance(obj, PdfDict):
                    if compress and obj.stream:
                        do_compress([obj])
                    myarray = []
                    dictkeys = [str(x) for x in obj.keys()]
                    dictkeys.sort()
                    for key in dictkeys:
                        myarray.append(key)
                        myarray.append(add(obj[key]))
                    result = format_array(myarray, '<<%s>>')
                    stream = obj.stream
                    if stream is not None:
                        result = '%s\nstream\n%s\nendstream' % (result, stream)
                    return result
                obj = (PdfArray, PdfDict)[isinstance(obj, dict)](obj)
                continue

            if not hasattr(obj, 'indirect') and isinstance(obj, basestring):
                return encode(obj)
            return str(getattr(obj, 'encoded', obj))

    def format_deferred():
        while deferred:
            index, obj = deferred.pop()
            objlist[index] = format_obj(obj)


    indirect_dict = {}
    indirect_dict_get = indirect_dict.get
    objlist = []
    objlist_append = objlist.append
    visited = set()
    visiting = visited.add
    leaving = visited.remove
    space_join = ' '.join
    lf_join = '\n  '.join
    f_write = f.write

    deferred = []

    # Don't reference old catalog or pages objects -- swap references to new ones.
    swapobj = {PdfName.Catalog:trailer.Root, PdfName.Pages:trailer.Root.Pages, None:trailer}.get
    swapobj = [(objid, swapobj(obj.Type)) for objid, obj in killobj.iteritems()]
    swapobj = dict((objid, obj is None and NullObject or obj) for objid, obj in swapobj).get

    for objid in killobj:
        assert swapobj(objid) is not None

    # The first format of trailer gets all the information,
    # but we throw away the actual trailer formatting.
    format_obj(trailer)
    # Keep formatting until we're done.
    # (Used to recurse inside format_obj for this, but
    #  hit system limit.)
    format_deferred()
    # Now we know the size, so we update the trailer dict
    # and get the formatted data.
    trailer.Size = PdfObject(len(objlist) + 1)
    trailer = format_obj(trailer)

    # Now we have all the pieces to write out to the file.
    # Keep careful track of the counts while we do it so
    # we can correctly build the cross-reference.

    header = '%%PDF-%s\n%%\xe2\xe3\xcf\xd3\n' % version
    f_write(header)
    offset = len(header)
    offsets = [(0, 65535, 'f')]
    offsets_append = offsets.append

    for i, x in enumerate(objlist):
        objstr = '%s 0 obj\n%s\nendobj\n' % (i + 1, x)
        offsets_append((offset, 0, 'n'))
        offset += len(objstr)
        f_write(objstr)

    f_write('xref\n0 %s\n' % len(offsets))
    for x in offsets:
        f_write('%010d %05d %s\r\n' % x)
    f_write('trailer\n\n%s\nstartxref\n%s\n%%%%EOF\n' % (trailer, offset))

class PdfWriter(object):

    _trailer = None

    def __init__(self, version='1.3', compress=False):
        self.pagearray = PdfArray()
        self.compress = compress
        self.version = version
        self.killobj = {}

    def addpage(self, page):
        self._trailer = None
        if page.Type != PdfName.Page:
            raise PdfOutputError('Bad /Type:  Expected %s, found %s'
                                  % (PdfName.Page, page.Type))
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

        # Add parents in the hierarchy to objects we
        # don't want to output
        killobj = self.killobj
        obj = page.Parent
        while obj is not None:
            objid = id(obj)
            if objid in killobj:
                break
            killobj[objid] = obj
            obj = obj.Parent
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
        FormatObjects(f, trailer, self.version, self.compress, self.killobj)
        if not preexisting:
            f.close()

if __name__ == '__main__':
    import logging
    log.setLevel(logging.DEBUG)
    import pdfreader
    x = pdfreader.PdfReader('source.pdf')
    y = PdfWriter()
    for i, page in enumerate(x.pages):
        print '  Adding page', i+1, '\r',
        y.addpage(page)
    print
    y.write('result.pdf')
    print
