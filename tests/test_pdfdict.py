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


from pdfrw import PdfDict, PdfName
from pdfrw.objects import PdfIndirect

import unittest


class TestPdfDicts(unittest.TestCase):
    
    def test_indirect_set_get(self):
        io = PdfIndirect((1,2,3))
        io.value = 42
        d = PdfDict()
        d.Name = io
        test, = (x for x in dict.values(d))
        self.assertEqual(test, io)
        v = d['/Name']
        self.assertEqual(v, io.value)
        test, = d
        self.assertEqual(type(test), type(PdfName.Name))

def main():
    unittest.main()


if __name__ == '__main__':
    main()
