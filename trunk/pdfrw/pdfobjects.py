# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
Objects that can occur in PDF files.  The most important
objects are arrays and dicts.  Either of these can be
indirect or not, and dicts could have an associated
stream.
'''
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
    unescape_dict = {'\\b':'\b', '\\f':'\f', '\\n':'\n',
                     '\\r':'\r', '\\t':'\t',
                     '\\\r\n': '', '\\\r':'', '\\\n':'',
                     '\\\\':'\\', '\\':'',
                    }
    unescape_pattern = '(\\b|\\f|\\n|\\r|\\t|\\\r\n|\\\r||\\\n|\\\\|\\[0-9]*)'
    unescape_func = re.compile(unescape_pattern).split

    hex_pattern = '([a-fA-F0-9][a-fA-F0-9])'
    hex_func = re.compile(hex_pattern).split

    indirect = False

    def decode_regular(self):
        source = self.re_func(self)
        assert mylist.pop(0) == '(' and mylist.pop() == ')'
        result = []
        unescape = self.unescape_dict.get
        for chunk in mylist:
            chunk = unescape(chunk, chunk)
            if chunk.startswith('\\') and len(chunk) > 1:
                chunk = chr(int(chunk[1:], 8))
            if chunk:
                result.append(chunk)
        return ''.join(result)

    def decode_hex(self):
        data = self
        if len(data) & 1:
            data = data[:-1] + '0' + data[-1]
        data = self.hex_func.split(self)
        chars = data[1::2]
        other = data[0::2]
        assert other[0] == '<' and other[-1] == '>' and ''.join(other) == '<>', self
        return ''.join(chr(int(x, 16)) for x in data)

    def decode(self):
        if self.startswith('('):
            return self.decode_regular()

        else:
            return self.decode_hex()

class PdfDict(dict):
    indirect = False
    stream = None

    _special = dict(indirect = ('indirect', False),
                    stream = ('stream', True),
                    _stream = ('stream', False),
                   )

    def __init__(self, *args, **kw):
        for key, value in kw.iteritems():
            setattr(self, key, value)
        if args:
            if len(args) == 1:
                args = args[0]
            self.update(args)

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

class IndirectPdfDict(PdfDict):
    indirect = True
