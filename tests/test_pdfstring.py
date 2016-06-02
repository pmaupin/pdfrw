#! /usr/bin/env python
# encoding: utf-8

'''
Run from the directory above like so:
python -m tests.test_pdfstring
'''


import pdfrw
import unittest


class TestEncoding(unittest.TestCase):

    @staticmethod
    def decode(value):
        return pdfrw.objects.PdfString(value).decode()

    @staticmethod
    def encode(value):
        return pdfrw.objects.PdfString.encode(value)

    @classmethod
    def encode_decode(cls, value):
        return cls.decode(cls.encode(value))

    def roundtrip(self, value):
        self.assertEqual(value, self.encode_decode(value))

    def test_doubleslash(self):
        self.roundtrip('\\')

    def test_pdfdocencoding(self):
        # These chars are in PdfDocEncoding
        self.roundtrip(u'PDF™©®')
    
    def test_unicode(self):
        # These chars are not in PdfDocEncoding
        self.roundtrip(u'δΩσ')

    def test_constructor(self):
        obj = pdfrw.objects.PdfString('hello')

    def test_continuation(self):
        test_string = "Here is a line"
        continuation = "(%s\\\n%s)" % (test_string,test_string)
        decoded = self.decode(continuation)
        self.assertEqual(test_string * 2, decoded)

    def test_unicode_escaped(self):
        # Some PDF producers happily put unicode strings in PdfDocEncoding,
        # because the Unicode BOM and \0 are valid code points
        decoded = self.decode('(\xfe\xff\0h\0e\0l\0l\0o)')
        self.assertEqual(decoded, "hello")


def main():
    unittest.main()


if __name__ == '__main__':
    main()
