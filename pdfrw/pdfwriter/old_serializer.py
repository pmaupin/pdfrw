# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
This is the old PDF output serializer, backwards compatible
with pdfrw 0.3 for users who need the user_fmt function.

The new serializer will have similar functionality, but
implemented more efficiently, so this should not be used
by new code.

Either serializer should know how to send a PDF to a
file, but not know or care about how the pieces fit together.

A separate builder class, e.g. PdfBuilder, can build new PDF
structures to be sent out to disk by the serializer, or,
alternatively, user code can build it itself.

PdfWriter instantiates the serializer and the builder,
and should not really know much about the internals
of either one.
'''

from ..objects import PdfDict, PdfObject, PdfString, PdfArray
from ..compress import compress as do_compress
from ..errors import PdfOutputError
from ..py23_diffs import iteritems, convert_store

def user_fmt(obj, isinstance=isinstance, float=float, str=str,
             basestring=(type(u''), type(b'')), encode=PdfString.encode):
    ''' This function may be replaced by the user for
        specialized formatting requirements.
    '''

    if isinstance(obj, basestring):
        return encode(obj)

    # PDFs don't handle exponent notation
    if isinstance(obj, float):
            return ('%.9f' % obj).rstrip('0').rstrip('.')

    return str(obj)


def old_serializer(f, trailer, version='1.3', compress=True,
                  user_fmt=user_fmt, do_compress=do_compress,
                  convert_store=convert_store, iteritems=iteritems,
                  id=id, isinstance=isinstance, getattr=getattr, len=len,
                  sum=sum, set=set, str=str, hasattr=hasattr, repr=repr,
                  enumerate=enumerate, list=list, dict=dict, tuple=tuple,
                  PdfArray=PdfArray, PdfDict=PdfDict, PdfObject=PdfObject):
    ''' old_streamer performs the actual formatting and disk write.
        Should be a class, was a class, turned into nested functions
        for performace (to reduce attribute lookups).
    '''

    def f_write(s):
        f.write(convert_store(s))

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
                raise PdfOutputError('Object cycle detected -- break it by using indirect')
            visiting(objid)
            result = format_obj(obj)
            leaving(objid)
            return result

        objnum = indirect_dict_get(objid)

        # If we haven't seen the object yet, we need to
        # add it to the indirect object list.
        if objnum is None:
            objnum = len(objlist) + 1
            objlist_append(None)
            indirect_dict[objid] = objnum
            deferred.append((objnum - 1, obj))
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
                    pairs = sorted((x, y, getattr(x, 'encoded', x))
                                   for (x, y) in obj.iteritems())
                    myarray = []
                    for key, value, encoding in pairs:
                        myarray.append(encoding)
                        myarray.append(add(value))
                    result = format_array(myarray, '<<%s>>')
                    stream = obj.stream
                    if stream is not None:
                        result = ('%s\nstream\n%s\nendstream' %
                                  (result, stream))
                    return result
                obj = (PdfArray, PdfDict)[isinstance(obj, dict)](obj)
                continue

            # We assume that an object with an indirect
            # attribute knows how to represent itself to us.
            if hasattr(obj, 'indirect'):
                return str(getattr(obj, 'encoded', obj))
            return user_fmt(obj)

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

    deferred = []

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
