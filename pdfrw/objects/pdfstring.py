# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

import re
import codecs


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

    def decode_hex(self):
        data = ''.join(self.split())
        assert data[0] == '<' and data[-1] == '>', self

        # ASCII encoded hex
        content_hex = data[1:-1]
        content_bytes = codecs.decode(content_hex, 'hex')
        return codecs.decode(content_bytes, 'utf-16')

    def decode(self, remap=chr):
        if self.startswith('('):
            return self.decode_regular(remap)
        else:
            return self.decode_hex(remap)

    def encode(cls, source, usehex=True):
        try:
            source.encode('ascii')
        except (UnicodeEncodeError, TypeError) as e:
            if not usehex:
                raise e
            # Encode a Unicode string as UTF-16 big endian, in bytes
            utf16_bytes = source.encode('utf-16be')
            # Prepend byte order mark and encode bytes as hexadecimal
            ascii_hex_bytes = codecs.encode(b'\xfe\xff' + utf16_bytes, 'hex')
            # Decode hexadecimal bytes to ASCII
            ascii_hex_str = ascii_hex_bytes.decode('ascii').lower()
            return cls('<' + ascii_hex_str + '>')

        source = source.replace('\\', '\\\\')
        source = source.replace('(', '\\(')
        source = source.replace(')', '\\)')
        return cls('(' + source + ')')
    encode = classmethod(encode)
