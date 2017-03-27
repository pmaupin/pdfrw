# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
#                    2016 James Laird-Wah, Sydney, Australia
# MIT license -- See LICENSE.txt for details

import re
import codecs
import binascii

__all__ = ['PdfString']

# Unicode point for each PdfDocEncoding value (or -1 if undefined)
pde_points = [
        0x0000,     -1,     -1,     -1,     -1,     -1,     -1,     -1,
            -1, 0x0009, 0x000a,     -1, 0x000c, 0x000d,     -1,     -1,
            -1,     -1,     -1,     -1,     -1,     -1,     -1,     -1,
        0x02d8, 0x02c7, 0x02c6, 0x02d9, 0x02dd, 0x02db, 0x02da, 0x02dc,
        0x0020, 0x0021, 0x0022, 0x0023, 0x0024, 0x0025, 0x0026, 0x0027,
        0x0028, 0x0029, 0x002a, 0x002b, 0x002c, 0x002d, 0x002e, 0x002f,
        0x0030, 0x0031, 0x0032, 0x0033, 0x0034, 0x0035, 0x0036, 0x0037,
        0x0038, 0x0039, 0x003a, 0x003b, 0x003c, 0x003d, 0x003e, 0x003f,
        0x0040, 0x0041, 0x0042, 0x0043, 0x0044, 0x0045, 0x0046, 0x0047,
        0x0048, 0x0049, 0x004a, 0x004b, 0x004c, 0x004d, 0x004e, 0x004f,
        0x0050, 0x0051, 0x0052, 0x0053, 0x0054, 0x0055, 0x0056, 0x0057,
        0x0058, 0x0059, 0x005a, 0x005b, 0x005c, 0x005d, 0x005e, 0x005f,
        0x0060, 0x0061, 0x0062, 0x0063, 0x0064, 0x0065, 0x0066, 0x0067,
        0x0068, 0x0069, 0x006a, 0x006b, 0x006c, 0x006d, 0x006e, 0x006f,
        0x0070, 0x0071, 0x0072, 0x0073, 0x0074, 0x0075, 0x0076, 0x0077,
        0x0078, 0x0079, 0x007a, 0x007b, 0x007c, 0x007d, 0x007e,     -1,
        0x2022, 0x2020, 0x2021, 0x2026, 0x2014, 0x2013, 0x0192, 0x2044,
        0x2039, 0x203a, 0x2212, 0x2030, 0x201e, 0x201c, 0x201d, 0x2018,
        0x2019, 0x201a, 0x2122, 0xfb01, 0xfb02, 0x0141, 0x0152, 0x0160,
        0x0178, 0x017d, 0x0131, 0x0142, 0x0153, 0x0161, 0x017e,     -1,
        0x20ac, 0x00a1, 0x00a2, 0x00a3, 0x00a4, 0x00a5, 0x00a6, 0x00a7,
        0x00a8, 0x00a9, 0x00aa, 0x00ab, 0x00ac,     -1, 0x00ae, 0x00af,
        0x00b0, 0x00b1, 0x00b2, 0x00b3, 0x00b4, 0x00b5, 0x00b6, 0x00b7,
        0x00b8, 0x00b9, 0x00ba, 0x00bb, 0x00bc, 0x00bd, 0x00be, 0x00bf,
        0x00c0, 0x00c1, 0x00c2, 0x00c3, 0x00c4, 0x00c5, 0x00c6, 0x00c7,
        0x00c8, 0x00c9, 0x00ca, 0x00cb, 0x00cc, 0x00cd, 0x00ce, 0x00cf,
        0x00d0, 0x00d1, 0x00d2, 0x00d3, 0x00d4, 0x00d5, 0x00d6, 0x00d7,
        0x00d8, 0x00d9, 0x00da, 0x00db, 0x00dc, 0x00dd, 0x00de, 0x00df,
        0x00e0, 0x00e1, 0x00e2, 0x00e3, 0x00e4, 0x00e5, 0x00e6, 0x00e7,
        0x00e8, 0x00e9, 0x00ea, 0x00eb, 0x00ec, 0x00ed, 0x00ee, 0x00ef,
        0x00f0, 0x00f1, 0x00f2, 0x00f3, 0x00f4, 0x00f5, 0x00f6, 0x00f7,
        0x00f8, 0x00f9, 0x00fa, 0x00fb, 0x00fc, 0x00fd, 0x00fe, 0x00ff
    ]

decoding_map = dict()
for pde, uni in enumerate(pde_points):
    if uni != -1:
        decoding_map[pde] = uni

encoding_map = codecs.make_encoding_map(decoding_map)

class PdfDocEncoding(codecs.Codec):
    def encode(self, input, errors='strict'):
        return codecs.charmap_encode(input, errors, encoding_map)

    def decode(self, input, errors='strict'):
        return codecs.charmap_decode(input, errors, decoding_map)

def find_pdfdocencoding(encoding):
    if encoding == 'pdfdocencoding':
        return codecs.CodecInfo(
                name='pdfdocencoding',
                encode=PdfDocEncoding().encode,
                decode=PdfDocEncoding().decode,
        )

codecs.register(find_pdfdocencoding)

class PdfString(str):
    ''' A PdfString is an encoded string.  It has a decode
        method to get the actual string data out, and there
        is an encode class method to create such a string.
        Like any PDF object, it could be indirect, but it
        defaults to being a direct object.
    '''
    indirect = False
    escapes = {
        b'\n': b'\\n',
        b'\r': b'\\r',
        b'\t': b'\\t',
        b'\b': b'\\b',
        b'\f': b'\\f',
        b'(' : b'\\(',
        b')' : b'\\)',
        b'\\': b'\\\\'
    }

    unescapes = {v[1]: k for k, v in escapes.items()}

    # Possible string escapes from the spec:
    # 1. \[nrtbf\()]: simple escapes
    # 2. \\d{1,3}: octal. Must be zero-padded to 3 digits if followed by digit
    # 3. \<end of line>: line continuation. We don't know the EOL marker
    # used in the PDF, so accept \r, \n, and \r\n.
    unescape_re = re.compile(br'\\(([nrtbf\(\)\\])|(\d{1,3})|(\r|\r\n|\n))')

    def decode_escaped(self):
        def handle_escape(m):
            if m.group(2):  # direct escape
                return self.unescapes[m.group(2).decode('ascii')]
            if m.group(3):  # octal
                value = int(m.group(3).decode('ascii'), 8)
                return bytes(bytearray([value]))
            if m.group(4):  # line continuation
                return b''
            # The PDF spec says that if the backslash doesn't form a valid
            # escape, the backslash is ignored.
            return m.group(1)

        return self.unescape_re.sub(handle_escape, bytearray(self[1:-1]))

    def decode_bytes(self, bytestr):
        if bytestr[:2] == codecs.BOM_UTF16_BE:
            return bytestr[2:].decode('utf-16-be')
        else:
            return bytestr.decode('pdfdocencoding')

    def decode_hex(self):
        hexstr = self[1:-1]
        if len(hexstr) % 1: # odd number of chars indicates a truncated 0
            hexstr += '0'
        return binascii.unhexlify(hexstr)

    def decode(self):
        if self.startswith('(') and self.endswith(')'):
            raw = self.decode_escaped()

        elif self.startswith('<') and self.endswith('>'):
            raw = self.decode_hex()

        else:
            raise ValueError('Invalid PDF string "%s"' % repr(self))

        return self.decode_bytes(raw)

    escape_re = re.compile(br'(([^\x20-\x7e])|([\n\r\t\b\f\(\)\\]))')

    @classmethod
    def encode(cls, source):
        def handle_char(m):
            if m.group(1):  # unprintables
                return ('\\%03o' % ord(m.group(1))).encode()
            if m.group(2):  # simple escapes
                return escapes[m.group(2)].encode()

        try:
            raw = source.encode('pdfdocencoding')
            escaped = cls.escape_re.sub(handle_char, raw)

            return cls('(' + escaped.decode('ascii') + ')')

        except ValueError:
            encoded = codecs.BOM_UTF16_BE + source.encode('utf-16-be')
            # The spec does not mandate uppercase, but it seems to be the convention.
            hexstr = codecs.decode(binascii.hexlify(encoded), 'ascii').upper()
            return cls('<' + hexstr + '>')
