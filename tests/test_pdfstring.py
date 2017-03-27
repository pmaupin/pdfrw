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
        return str(pdfrw.objects.PdfString.encode(value))

    @classmethod
    def encode_decode(cls, value):
        return cls.decode(cls.encode(value))

    def roundtrip(self, value):
        self.assertEqual(value, self.encode_decode(value))

    def test_doubleslash(self):
        self.roundtrip('\\')

    def test_unicode(self):
        ustr = u'PDF™©®'

        self.roundtrip(ustr)

        self.assertEqual("<FEFF005000440046212200A900AE>", self.encode(ustr))


def main():
    unittest.main()


if __name__ == '__main__':
    main()
