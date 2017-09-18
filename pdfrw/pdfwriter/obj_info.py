# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

"""
This module contains code to track object information
(such as indirect object numbers) for the serializer.
"""

from ..objects import PdfObject


def get_obj_info(f_write, f_tell):
    """
        Parameters:
            f_write is the function to call to stream data out.
            f_tell is the function to call to get stream position

        Returns:

            ObjInfo, DeferredSize, write_xref

            ObjInfo is a wrapper around PDF objects used for reference tracking
            and formatting.

            DeferredLength is a PDF object used to dump the number of indirect
            objects.

            write_xref will write the cross-reference table.
    """

    obj_offsets = [None]  # Object numbering starts at 1
    next_num = obj_offsets.__len__
    add_offset = obj_offsets.append


    class ObjInfo(object):
        """
            Serialize builds parallel data structures to aid in serialization.

            For each PDF object, it creates an ObjInfo object.  This
            ObjInfo instance has the following attributes:

                obj = original object

                flags = number:
                        - bit 0 -- true if array,
                        - bit 1 -- true if leaf (not array or dict)
                        - bit 2 -- true if indirect

                NOTE: flags is reused for the file offset for indirect objects

                obj_num = reference number for indirect object,
                           ordering information for direct deferred objects.

                formatter = object-type-specific output formatting function

                sublist =  None for leaf objects (not containers);
                        list of ObjInfo instances for array objects;
                        list of tuples of key/ObjInfo instance pairs
                        for dict objects.
        """
        __slots__ = 'obj flags obj_num formatter sublist'.split()


        # NOTE:  Flag values were chosen such that
        #        indirect > leaf > array > deferred > dict
        IS_DICT = 0
        IS_DEFERRED = 1
        IS_ARRAY = 2
        IS_LEAF = 4
        IS_INDIRECT = 8


        def __init__(self):
            self.obj = self.flags = self.sublist = None

        def make_indirect(self, IS_INDIRECT=IS_INDIRECT):
            assert not (self.flags & IS_INDIRECT)
            self.obj_num = next_num()
            add_offset(None)
            self.flags |= IS_INDIRECT

        def write(self, IS_INDIRECT=IS_INDIRECT):
            """
                Writes the object, or a reference to it.
            """
            if self.flags & IS_INDIRECT:
                return f_write('%d 0 R' % self.obj_num)
            if self.sublist is None:
                return f_write(self.formatter(self.obj))
            return self.formatter(self)

        @property
        def ref(self, IS_INDIRECT=IS_INDIRECT):
            """
                Return a reference, if we have one.
                Otherwise, return the object.
            """
            if self.flags & IS_INDIRECT:
                return PdfObject('%d 0 R' % self.obj_num)
            return self.obj


        def dump(self):
            obj_num = self.obj_num
            assert obj_offsets[obj_num] is None
            obj_offsets[obj_num] = f_tell()
            f_write('%s 0 obj\n' % obj_num)
            self.write(0)
            f_write('\nendobj\n')


    # We need a size in the trailer dict, but we don't know it yet.
    class DeferSize(object):
        @property
        def encoded(self):
            return str(next_num())


    def write_xref():
        xref_loc = f_tell()
        fmt = '%010d %05d %s\r\n'
        f_write('xref\n0 %s\n' % next_num())
        f_write(fmt % (0, 65535, 'f'))
        iterator = iter(obj_offsets)
        next(iterator)
        for offset in iterator:
            f_write(fmt % (offset, 0, 'n'))
        return xref_loc

    return ObjInfo, DeferSize, write_xref
