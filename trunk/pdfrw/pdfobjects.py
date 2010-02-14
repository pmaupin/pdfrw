# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Objects that can occur in PDF files.  The most important
objects are arrays and dicts.  Either of these can be
indirect or not, and dicts could have an associated
stream.
'''
from __future__ import generators

try:
    set
except NameError:
    from sets import Set as set

import re

class PdfObject(str):
    indirect = False

class PdfArray(list):
    indirect = False

class PdfName(object):
    def __getattr__(self, name):
        return self(name)
    def __call__(self, name):
        return PdfObject('/' + name)

PdfName = PdfName()

class PdfString(str):
    indirect = False
    unescape_dict = {'\\b':'\b', '\\f':'\f', '\\n':'\n',
                     '\\r':'\r', '\\t':'\t',
                     '\\\r\n': '', '\\\r':'', '\\\n':'',
                     '\\\\':'\\', '\\':'',
                    }
    unescape_pattern = r'(\\b|\\f|\\n|\\r|\\t|\\\r\n|\\\r|\\\n|\\[0-9]+|\\)'
    unescape_func = re.compile(unescape_pattern).split

    hex_pattern = '([a-fA-F0-9][a-fA-F0-9]|[a-fA-F0-9])'
    hex_func = re.compile(hex_pattern).split

    hex_pattern2 = '([a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]|[a-fA-F0-9][a-fA-F0-9]|[a-fA-F0-9])'
    hex_func2 = re.compile(hex_pattern2).split

    hex_funcs = hex_func, hex_func2

    indirect = False

    def decode_regular(self, remap=chr):
        assert self[0] == '(' and self[-1] == ')'
        mylist = self.unescape_func(self[1:-1])
        result = []
        unescape = self.unescape_dict.get
        for chunk in mylist:
            chunk = unescape(chunk, chunk)
            if chunk.startswith('\\') and len(chunk) > 1:
                value = int(chunk[1:], 8)
                # FIXME: TODO: Handle unicode here
                if value > 127:
                    value = 127
                chunk = remap(value)
            if chunk:
                result.append(chunk)
        return ''.join(result)

    def decode_hex(self, remap=chr, twobytes=False):
        data = ''.join(self.split())
        data = self.hex_funcs[twobytes](data)
        chars = data[1::2]
        other = data[0::2]
        assert other[0] == '<' and other[-1] == '>' and ''.join(other) == '<>', self
        return ''.join([remap(int(x, 16)) for x in chars])

    def decode(self, remap=chr, twobytes=False):
        if self.startswith('('):
            return self.decode_regular(remap)

        else:
            return self.decode_hex(remap, twobytes)

    def encode(cls, source, usehex=False):
        assert not usehex, "Not supported yet"
        if isinstance(source, unicode):
            source = source.encode('utf-8')
        else:
            source = str(source)
        source = source.replace('\\', '\\\\')
        source = source.replace('(', '\\(')
        source = source.replace(')', '\\)')
        return cls('(' +source + ')')
    encode = classmethod(encode)

class PdfDict(dict):
    indirect = False
    stream = None

    _special = dict(indirect = ('indirect', False),
                    stream = ('stream', True),
                    _stream = ('stream', False),
                   )

    def __setitem__(self, name, value):
        assert name.startswith('/'), name
        if value is not None:
            dict.__setitem__(self, name, value)
        elif name in self:
            del self[name]

    def __init__(self, *args, **kw):
        if args:
            if len(args) == 1:
                args = args[0]
            self.update(args)
            if isinstance(args, PdfDict):
                self.indirect = args.indirect
                self._stream = args.stream
        for key, value in kw.iteritems():
            setattr(self, key, value)

    def __getattr__(self, name):
        return self.get(PdfName(name))

    def __setattr__(self, name, value):
        info = self._special.get(name)
        if info is None:
            self[PdfName(name)] = value
        else:
            name, setlen = info
            self.__dict__[name] = value
            if setlen:
                notnone = value is not None
                self.Length = notnone and PdfObject(len(value)) or None

    def iteritems(self):
        for key, value in dict.iteritems(self):
            if value is not None:
                assert key.startswith('/'), (key, value)
                yield key, value

    def inheritable(self):
        ''' Search through ancestors as needed for inheritable
            dictionary items
        '''
        class Search(object):
            def __init__(self, basedict):
                self.basedict = basedict
            def __getattr__(self, name):
                return self[name]
            def __getitem__(self, name):
                visited = set()
                mydict = self.basedict
                while 1:
                    value = getattr(mydict, name)
                    if value is not None:
                        return value
                    myid = id(mydict)
                    assert myid not in visited
                    visited.add(myid)
                    mydict = mydict.Parent
                    if mydict is None:
                        return
        return Search(self)
    inheritable = property(inheritable)

    def private(self):
        ''' Allows setting private metadata for use in
            processing (not sent to PDF file)
        '''
        class Private(object):
            pass

        result = Private()
        result.__dict__ = self.__dict__
        return result
    private = property(private)

class IndirectPdfDict(PdfDict):
    indirect = True
