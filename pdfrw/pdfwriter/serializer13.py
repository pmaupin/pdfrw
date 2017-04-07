# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

"""
This module contains a function to serialize a PDF data structure
out to a PDF version 1.3 file.
"""

from collections import defaultdict
from .obj_info import get_obj_info
from ..errors import PdfOutputError
from ..compress import compress as do_compress


class Serialize13(object):
    """
        Serializes a PDF file to a file or a file-like object.

        Serialize has the following user methods:

        write(*objs, **incremental=False)

            Returns a list of references to the objects if incremental
            is True.  If incremental is False, you must pass the trailer
            object.  Note that if incremental is True, it is up to the caller
            to fix up references to the written objects in objects that have
            not yet been written.  Otherwise, the serializer will happily
            write them out again.

        defer(*objs):
            Adds objects to the defer list (assigns object numbers and will
            not write out yet).  To undefer an object, either explicitly pass
            it to write later, or to undefer them all and finish up, call
            write without setting incremental.
    """

    def __init__(self, f, version, compress,
                 get_formatter, get_streamer):
        if version is None:
            version = '1.3'
        if compress and not callable(compress):
            compress = do_compress
        streamer = get_streamer(f)
        f_write = streamer.write
        stuff = get_obj_info(f_write, streamer.tell)
        (self.ObjInfo, self.DeferSize, self.write_xref) = stuff

        self.f_write = f_write
        self.flush = streamer.flush
        self.compress = compress
        self.obj_offsets = [None]  # Object numbering starts at 1
        self.deferrals = defaultdict(self.ObjInfo)
        get_formatter = getattr(get_formatter, 'get_formatter', get_formatter)
        self.typeinfo = self.get_typeinfo(get_formatter)
        self.f_write('%%PDF-%s\n%%\xe2\xe3\xcf\xd3\n' % version)
        self.deferred_order = -1


    def defer(self, *objs):
        """
            Use defer to pre-allocate object numbers for containers
            we do not yet want to output to the file.
        """
        for obj in objs:
            info = self.deferrals[id(obj)]
            if info.obj is not None:
                continue
            info.obj = obj
            info.flags = info.IS_DEFERRED
            info.obj_num = self.deferred_order
            self.deferred_order -= 1

    def get_typeinfo(self, get_formatter):
        handler_map = {dict:(self.ObjInfo.IS_DICT, self.dump_dict),
                       list:(self.ObjInfo.IS_ARRAY, self.dump_array)}.get

        leaf = self.ObjInfo.IS_LEAF

        class memodict(dict):
            def __missing__(self, obj_type):
                handler = get_formatter(obj_type)
                ret = self[obj_type] = handler_map(handler, (leaf, handler))
                return ret
        return memodict().__getitem__


    def dump_objects(self, objlist, type=type, id=id,
                    sorted=sorted, getattr=getattr):
        """
            dump_objects takes a list of objects, creates ObjInfo
            records for all those objects, and any objects they refer to,
            and then dumps all of the indirect objects that have not
            been marked deferred.

            Parameters:
                objlist is the list of top-level objects to start with

            Returns:
                infolist is a list of the info containers for each
                object in objlist.

            Operation:
                This function builds parallel ObjInfo arrays.  It does not
                alter the original objects unless the compress parameter is
                true, in which case, it will attempt to compress streams
                in situ.

                When building the new structure, objects are considered
                to be indirect in three cases:

                    - If they have an indirect attribute that evaluates to true.
                    - If they are non-leaf objects and are referenced by more
                      than one other object.  This is done to break cycles.
                    - If they are in the deferred dictionary and are not
                      in the passed objlist.
        """

        typeinfo = self.typeinfo
        compress = self.compress
        ObjInfo = self.ObjInfo

        IS_DEFERRED = ObjInfo.IS_DEFERRED
        IS_ARRAY = ObjInfo.IS_ARRAY
        IS_LEAF = ObjInfo.IS_LEAF
        IS_INDIRECT = ObjInfo.IS_INDIRECT

        obj_info_dict = defaultdict(ObjInfo, self.deferrals)

        def get_info(obj):
            """ get_info is used to map source objects to the new ObjInfo
                objects that we are building.  Not all source objects are
                hashable, so the obj_info_dict is indexed by object IDs.
            """
            info = obj_info_dict[id(obj)]
            if info.obj is None:
                info.obj = obj
            return info

        def add_container(info):
            # We have a container.
            containers.append(info)
            obj = info.obj
            if info.flags & IS_ARRAY:
                # Add an array sublist
                info.sublist = [get_info(x) for x in obj]
            else:
                # Add a dict sublist, but compress it first, because
                # compression can alter the items in the dict.
                if compress and getattr(obj, 'stream', None) is not None:
                    compress([obj])
                pairs = sorted((getattr(x, 'encoded', None) or x, y)
                            for (x, y) in obj.iteritems())
                info.sublist = [(x, get_info(y)) for (x, y) in pairs]

        # We simultaneously build containers out while we
        # are iterating on it.  Every object that is a container
        # is placed here, then processed in order it was found.
        containers = []
        wrappers = []
        indirect_objects = []

        for obj in objlist:
            info = get_info(obj)
            obj_kind, info.formatter = typeinfo(type(obj))
            info.flags, old_flags = obj_kind, info.flags
            if old_flags is not None:
                del self.deferrals[id(obj)]
                old_flags &= IS_INDIRECT
                info.flags |= old_flags
            if not old_flags and getattr(obj, 'indirect', None):
                info.make_indirect()
            if info.flags & IS_INDIRECT:
                indirect_objects.append(info)
            wrappers.append(info)
            if obj_kind != IS_LEAF:
                add_container(info)

        for c_info in containers:
            ## Get proper iterator for list or dict -- either every
            # ObjInfo in the sublist that parallels an array, or the
            # value ObjInfo of key/value pairs that parallels a dict

            c_values = (c_info.sublist if c_info.flags & IS_ARRAY
                        else (x[1] for x in c_info.sublist))
            for info in c_values:
                flags = info.flags
                if flags is not None:
                    # We've seen the object before.  If it's a
                    # container, force it to be indirect.
                    if flags < IS_LEAF:
                        info.make_indirect()
                        if not (flags & IS_DEFERRED):
                            indirect_objects.append(info)
                    continue

                # We're processing an object we haven't processed before.
                # First, figure out its type information
                obj = info.obj
                obj_kind, _ = info.flags, info.formatter = typeinfo(type(obj))

                if getattr(obj, 'indirect', None):
                    info.make_indirect()
                    indirect_objects.append(info)
                # If it's not a container, we're done
                if obj_kind != IS_LEAF:
                    add_container(info)

        for info in indirect_objects:
            info.dump()

        return wrappers

    def dump_dict(self, container):
        f_write = self.f_write
        f_write('<<')
        for key, info in container.sublist:
             f_write(key)
             info.write()
        f_write('>>')
        stream = getattr(container.obj, 'stream', None)
        if stream is not None:
            f_write('\nstream\n')
            if stream:
                f_write(stream)
            f_write('\nendstream')
        # Break cycles for our control structures
        container.sublist = None

    def dump_array(self, container):
        f_write = self.f_write
        f_write('[')
        for info in container.sublist:
             info.write()
        f_write(']')
        # Break cycles for our control structures
        container.sublist = None


    def write(self, *objects, **kwds):
        if not objects:
            raise TypeError("Serializer.write must be passed at least one object")
        if kwds:
            incremental = kwds.pop('incremental')
            if kwds:
                raise TypeError("Unknown keyword(s): %s" %
                                ', '.join(str(s) for s in kwds))
            if incremental:
                return [info.ref for info in self.dump_objects(objects)]

        # Final write

        try:
            trailer, = objects
        except ValueError:
            raise PdfOutputError("Serializer.write expects exactly one object (trailer)\n"+
                                    "  (if not writing incrementally)")
        if getattr(trailer, 'indirect', False):
            raise PdfOutputError("trailer object was declared indirect")

        trailer.Size = self.DeferSize()
        objlist = [trailer]
        if self.deferrals:
            objlist.extend(sorted(self.deferrals.values(), key=lambda x: x.obj_num))
        trailer, = self.dump_objects(objlist)[:1]
        if trailer.flags & trailer.IS_INDIRECT:
            raise PdfOutputError("trailer object was referenced circularly")
        xref_loc = self.write_xref()
        self.f_write('trailer\n\n')
        trailer.write()
        self.f_write('\nstartxref\n%s\n%%%%EOF\n' % xref_loc)
        self.flush()
        self.write = None  # Don't allow any more calls
