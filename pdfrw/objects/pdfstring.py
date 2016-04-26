# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

import re
import codecs
import binascii


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
    escapes = [('\\', '\\\\'), ('(', '\\('), (')', '\\)'),
                    ('\n', '\\n'), ('\t', '\\t')]

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
            return binascii.unhexlify(self[5:-1]).decode('utf-16-be')

    def decode(self, remap=chr):
        if self.startswith('('):
            return self.decode_regular(remap)

        elif self.upper().startswith('<FEFF') and self.endswith('>'):
            return self.decode_hex()

        else:
            raise ValueError('Invalid PDF string "%s"' % repr(self))

    @classmethod
    def encode(cls, source):
        try:
            asc = source.encode('ascii')
            for a, b in cls.escapes:
                source = source.replace(a, b)
            return cls('(' + source + ')')

        except UnicodeEncodeError:
            encoded = codecs.BOM_UTF16_BE + source.encode('utf-16-be')
            return '<' + binascii.hexlify(encoded).upper() + '>'
