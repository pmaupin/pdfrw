# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2012 Patrick Maupin, Austin, Texas
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
    ''' A PdfObject is a textual representation of any PDF file object
        other than an array, dict or string. It has an indirect attribute
        which defaults to False.
    '''
    indirect = False

class PdfArray(list):
    ''' A PdfArray maps the PDF file array object into a Python list.
        It has an indirect attribute which defaults to False.
    '''
    indirect = False

class PdfName(object):
    ''' PdfName is a simple way to get a PDF name from a string:

                PdfName.FooBar == PdfObject('/FooBar')
    '''
    def __getattr__(self, name):
        return self(name)
    def __call__(self, name, PdfObject=PdfObject):
        return PdfObject('/' + name)
PdfName = PdfName()

class PdfString(str):
    ''' A PdfString is an encoded string.  It has a decode
        method to get the actual string data out, and there
        is an encode class method to create such a string.
        Like any PDF object, it could be indirect, but it
        defaults to being a direct object.
    '''
    indirect = False
    unescape_dict = {'\\b':'\b', '\\f':'\f', '\\n':'\n',
                     '\\r':'\r', '\\t':'\t',
                     '\\\r\n': '', '\\\r':'', '\\\n':'',
                     '\\\\':'\\', '\\':'',
                    }
    unescape_pattern = r'(\\\\|\\b|\\f|\\n|\\r|\\t|\\\r\n|\\\r|\\\n|\\[0-9]+|\\)'
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
    ''' PdfDict objects are subclassed dictionaries with the following features:

        - Every key in the dictionary starts with "/"

        - A dictionary item can be deleted by assigning it to None

        - Keys that (after the initial "/") conform to Python naming conventions
          can also be accessed (set and retrieved) as attributes of the dictionary.
          E.g.  mydict.Page is the same thing as mydict['/Page']

        - Private attributes (not in the PDF space) can be set on the dictionary
          object attribute dictionary by using the private attribute:

                mydict.private.foo = 3
                mydict.foo = 5
                x = mydict.foo       # x will now contain 3
                y = mydict['/foo']   # y will now contain 5

          Most standard adobe dictionary keys start with an upper case letter,
          so to avoid conflicts, it is best to start private attributes with
          lower case letters.

        - PdfDicts have the following read-only properties:

            - private -- as discussed above, provides write access to dictionary's
                         attributes
            - inheritable -- this creates and returns a "view" attribute that
                         will search through the object hierarchy for any desired
                         attribute, such as /Rotate or /MediaBox

        - PdfDicts also have the following special attributes:
            - indirect is not stored in the PDF dictionary, but in the object's
              attribute dictionary
            - stream is also stored in the object's attribute dictionary
              and will also update the stream length.
            - _stream will store in the object's attribute dictionary without
              updating the stream length.

            It is possible, for example, to have a PDF name such as "/indirect"
            or "/stream", but you cannot access such a name as an attribute:

                mydict.indirect -- accesses object's attribute dictionary
                mydict["/indirect"] -- accesses actual PDF dictionary
    '''
    indirect = False
    stream = None

    _special = dict(indirect = ('indirect', False),
                    stream = ('stream', True),
                    _stream = ('stream', False),
                   )

    def __setitem__(self, name, value, setter=dict.__setitem__):
        assert name.startswith('/'), name
        if value is not None:
            setter(self, name, value)
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

    def __getattr__(self, name, PdfName=PdfName):
        return self.get(PdfName(name))

    def __setattr__(self, name, value, special=_special.get, PdfName=PdfName, vars=vars):
        info = special(name)
        if info is None:
            self[PdfName(name)] = value
        else:
            name, setlen = info
            vars(self)[name] = value
            if setlen:
                notnone = value is not None
                self.Length = notnone and PdfObject(len(value)) or None

    def iteritems(self, dictiter=dict.iteritems):
        for key, value in dictiter(self):
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
    ''' IndirectPdfDict is a convenience class.  You could
        create a direct PdfDict and then set indirect = True on it,
        or you could just create an IndirectPdfDict.
    '''
    indirect = True
