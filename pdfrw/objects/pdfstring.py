# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

import re


class PdfString(str):
    ''' A PdfString is an encoded string.  It has a decode
        method to get the actual string data out, and there
        is an encode class method to create such a string.
        Like any PDF object, it could be indirect, but it
        defaults to being a direct object.
    '''
    indirect = False
    unescape_dict = {'\\b': '\b', '\\f': '\f', '\\n': '\n',
                     '\\r': '\r', '\\t': '\t',
                     '\\\r\n': '', '\\\r': '', '\\\n': '',
                     '\\\\': '\\', '\\': '', '\\(': '(', '\\)': ')'
                     }
    unescape_pattern = (r'(\\\\|\\b|\\f|\\n|\\r|\\t'
                        r'|\\\r\n|\\\r|\\\n|\\[0-9]{3}|\\)')
    unescape_func = re.compile(unescape_pattern).split

    hex_pattern = '([a-fA-F0-9][a-fA-F0-9]|[a-fA-F0-9])'
    hex_func = re.compile(hex_pattern).split

    hex_pattern2 = ('([a-fA-F0-9][a-fA-F0-9][a-fA-F0-9][a-fA-F0-9]|'
                    '[a-fA-F0-9][a-fA-F0-9]|[a-fA-F0-9])')
    hex_func2 = re.compile(hex_pattern2).split

    hex_funcs = hex_func, hex_func2

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
                if value > 255:
                    value = 255
                chunk = remap(value)
            if chunk:
                result.append(chunk)
        return ''.join(result)

    def decode_hex(self, remap=chr, twobytes=False):
        data = ''.join(self.split())
        data = self.hex_funcs[twobytes](data)
        chars = data[1::2]
        other = data[0::2]
        assert (other[0] == '<' and
                other[-1] == '>' and
                ''.join(other) == '<>'), self
        return ''.join([remap(int(x, 16)) for x in chars])

    def decode(self, remap=chr, twobytes=False):
        if self.startswith('('):
            return self.decode_regular(remap)

        else:
            return self.decode_hex(remap, twobytes)

    def encode(cls, source, usehex=False):
        assert not usehex, "Not supported yet"
        source = source.replace('\\', '\\\\')
        source = source.replace('(', '\\(')
        source = source.replace(')', '\\)')
        return cls('(' + source + ')')
    encode = classmethod(encode)
