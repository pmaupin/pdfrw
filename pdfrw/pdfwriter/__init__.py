# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

"""
The PdfWriter class writes an entire PDF file out to a file
or a file-like object.

It is a thin wrapper on top of a builder class that has functions
to help client code set up the data structures for a PDF, and
a serializer class that knows how to send the structures to
a file.

Client code can either pass it a trailer and let it serialize it,
or can use it to invoke the PdfBuilder to help put together the
PDF before serialization.

This file is being refactored; currently it supports an old serializer,
but it will soon be able to choose between a new serializer and the old
one.  The old one will be chosen if the user has specified user_fmt to
the write function.

The old user_fmt functionality is supported, but the old
canonicalize functionality is not -- that made larger PDFs for
comparison testing and it is unlikely any users used it.  (But
if they did, it is easy enough to recreate in user code with
the new version.)
"""

import gc

from .serializer13 import Serialize13
from .streamer import StreamWriter
from .formatter import FormatHandlers
from .old_serializer import old_serializer, user_fmt
from .pdfbuilder import PdfBuilder

from ..errors import PdfOutputError
from ..py23_diffs import iteritems


class PdfWriter(object):
    """
        This class is instantiated, and then is used to
        pass through commands to a builder class, and then
        the write() function is called to serialize the
        data out to the disk.

        It is currently being refactored to be able to support
        a new serializer.
    """

    # These could be overridden before instantiation, or by
    # passing new functions to init.
    Builder = PdfBuilder
    Serializer = Serialize13
    StreamWriter = StreamWriter
    Formatter = FormatHandlers
    old_user_fmt = staticmethod(user_fmt)

    _trailer = None
    _builder = None

    def __init__(self, fname=None, version='1.3', compress=False, **kwargs):
        """
            Parameters:
                fname -- Output file name, or file-like binary object
                         with a write method
                version -- PDF version to target.  Currently only 1.3
                           supported.
                compress -- True to do compression on output.  Currently
                            compresses stream objects.

                **kwargs -- allows class attributes to be overridden without
                            writing a subclass.
        """

        # Legacy support:  fname is new, was added in front
        if fname is not None:
            try:
                float(fname)
            except (ValueError, TypeError):
                pass
            else:
                if version != '1.3':
                    assert compress == False
                    compress = version
                version = fname
                fname = None

        self.fname = fname
        self.version = version
        self.compress = compress

        if kwargs:
            for name, value in iteritems(kwargs):
                if name not in self.replaceable:
                    raise ValueError("Cannot set attribute %s "
                                     "on PdfWriter instance" % name)
                setattr(self, name, value)


    def __getattr__(self, name):
        """
            We pass through most attribute requests to the builder.
        """
        _builder = self._builder
        if not _builder:
            if self._trailer:
                raise PdfOutputError('Cannot set trailer and access builder')
            _builder = self._builder = self.Builder()
        attr = getattr(_builder, name)

        if callable(attr):
            def wrapper(*args):
                attr(*args)
                return self
        else:
            wrapper = attr
        setattr(self, name, wrapper)
        return wrapper

    # The trailer is special.  Client code can set it directly if it
    # doesn't want to use a builder, but we make the client code choose:
    # either the builder helps or it doesn't.

    @property
    def trailer(self):
        return self._trailer or self.__getattr__('trailer')
    @trailer.setter
    def trailer(self, trailer):
        if self._builder and self._builder.trailer is not trailer:
            raise PdfOutputError('Cannot set trailer after starting to build')
        self._trailer = trailer

    def write(self, fname=None, trailer=None, user_fmt=None,
              disable_gc=True):
        """
            This function lets the builder cleanup (if we have a builder),
            and then calls the serializer to send the data to a file or
            file-like object.
        """

        # Support fname for legacy applications
        if (fname is not None) == (self.fname is not None):
            raise PdfOutputError(
                "PdfWriter fname must be specified exactly once")

        fname = fname or self.fname


        _builder = self._builder
        _trailer = self._trailer or (_builder and _builder.trailer)

        if trailer is not None and _trailer is not None:
            raise PdfOutputError('Cannot set trailer after starting to build'
                                if _builder else
                                'Cannot set trailer after starting to build'
                                if trailer else 'Nothing to do!')

        if _builder:
            _builder.finalize()

        if disable_gc:
            gc.disable()

        # Dump the data.  We either have a filename or a preexisting
        # file object.
        preexisting = hasattr(fname, 'write')
        f = preexisting and fname or open(fname, 'wb')

        try:
            if user_fmt:
                old_serializer(f, trailer or _trailer, self.version,
                            self.compress, user_fmt=user_fmt)
            else:
                serializer = self.Serializer(f, self.version, self.compress,
                            self.Formatter, self.StreamWriter)
                serializer.write(trailer or _trailer)
        finally:
            if not preexisting:
                f.close()
            if disable_gc:
                gc.enable()

    # Attributes can be aliased on initialization
    replaceable = set(vars())
