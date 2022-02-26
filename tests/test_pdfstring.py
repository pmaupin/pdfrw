#! /usr/bin/env python
# encoding: utf-8
# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
#                    2016 James Laird-Wah, Sydney, Australia
# MIT license -- See LICENSE.txt for details

'''
Run from the directory above like so:
python -m tests.test_pdfstring
'''


from pdfrw import PdfString
from pdfrw.py23_diffs import convert_store

import unittest


class TestBaseEncoding(unittest.TestCase):

    def encode(self, value):
        x = PdfString.encode(value)
        if isinstance(value, type(u'')):
            y = PdfString.from_unicode(value)
        else:
            y = PdfString.from_bytes(value)
        self.assertEqual(x, y)
        return x

    def decode(self, value):
        s = PdfString(value)
        x = s.to_unicode()
        y = s.decode()
        self.assertEqual(x, y)
        return x

    def decode_bytes(self, decode_this, expected):
        """ Decode to bytes"""
        self.assertEqual(PdfString(decode_this).to_bytes(),
                         convert_store(expected))

    def roundtrip(self, value, expected=None):
        result = self.encode(value)
        self.assertEqual(value, self.decode(result))
        if expected is not None:
            self.assertEqual(result, expected)
        return result

    def test_doubleslash(self):
        self.roundtrip('\\')
        self.roundtrip(r'\\')

    def test_unicode_encoding(self):
        # These chars are in PdfDocEncoding
        self.assertEqual(self.roundtrip(u'PDF™©®')[0], '(')
        # These chars are not in PdfDocEncoding
        self.assertEqual(self.roundtrip(u'δΩσ')[0], '<')
        # Check that we're doing a reasonable encoding
        # Might want to change this later if we change the definition of reasonable
        self.roundtrip(u'(\n\u00FF', '(\\(\n\xff)')
        self.roundtrip(u'(\n\u0101', '<FEFF0028000A0101>')


    def test_constructor(self):
        obj = PdfString('hello')

    def test_continuation(self):
        # See PDF 1.7 ref section 3.2 page 55
        s1 = PdfString('(These two strings are the same.)')
        self.assertEqual(s1.decode(), s1[1:-1])
        s2 = PdfString('(These \\\ntwo strings \\\nare the same.)')
        self.assertEqual(s1.decode(), s2.decode())
        s2 = PdfString(s2.replace('\n', '\r'))
        self.assertEqual(s1.decode(), s2.decode())
        s2 = PdfString(s2.replace('\r', '\r\n'))
        self.assertEqual(s1.decode(), s2.decode())

    def test_hex_whitespace(self):
        # See PDF 1.7 ref section 3.2 page 56
        self.assertEqual(self.decode('<41 \n\r\t\f\v42>'), 'AB')

    def test_unicode_escaped_decode(self):
        # Some PDF producers happily put unicode strings in PdfDocEncoding,
        # because the Unicode BOM and \0 are valid code points
        decoded = self.decode('(\xfe\xff\0h\0e\0l\0l\0o)')
        self.assertEqual(decoded, "hello")


    def test_unescaping(self):
        self.decode_bytes(r'( \( \) \\ \n \t \f \r \r\n \\n)',
                           ' ( ) \\ \n \t \f \r \r\n \\n')

        self.decode_bytes(r'(\b\010\10)', '\b\b\b')
        self.decode_bytes('(\\n\n\\r\r\\t\t\\b\b\\f\f()\\1\\23\\0143)',
                          '\n\n\r\r\t\t\b\b\f\f()\001\023\f3')
        self.decode_bytes(r'(\\\nabc)', '\\\nabc')
        self.decode_bytes(r'(\ )', ' ')

    def test_BOM_variants(self):
        self.roundtrip(u'\ufeff', '<FEFFFEFF>')
        self.roundtrip(u'\ufffe', '<FEFFFFFE>')
        self.roundtrip(u'\xfe\xff', '<FEFF00FE00FF>')
        self.roundtrip(u'\xff\xfe', '(\xff\xfe)')
        self.assertRaises(UnicodeError, PdfString.from_unicode,
                          u'þÿ blah', text_encoding='pdfdocencoding')

    def test_byte_encode(self):
        self.assertEqual(self.encode(b'ABC'), '(ABC)')

    def test_nullstring(self):
        self.assertEqual(PdfString('<>').to_bytes(), b'')
        self.assertEqual(PdfString('()').to_bytes(), b'')

def main():
    unittest.main()


if __name__ == '__main__':
    main()
