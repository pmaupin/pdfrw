#! /usr/bin/env python

'''
Run from the directory above like so:

python -m tests.test_roundtrip

NB:

These tests are incomplete, but they allow us to try
out various PDFs.  There is a collection of difficult
PDFs available on github.

In order to use them:

  1) Insure that github.com/pmaupin/static_pdfs is on your path.

  2) Use the imagemagick compare program to look at differences
     between the static_pdfs/global directory and the tmp_results
     directory after you run this.

TODO: Automate true pass/fail reporting!!!

Thoughts on this:  Collect good MD5s for passing results, and
save the good MD5s in a file for comparison.  Modify tests
to assume failure unless MD5s match.

'''
import os
import unittest
import pdfrw

from static_pdfs import pdffiles

result_dir = 'tmp_results'

from pdfrw.pdfreader import PdfReader
from pdfrw.pdfwriter import PdfWriter
from pdfrw import IndirectPdfDict


class TestOnePdf(unittest.TestCase):

    def roundtrip(self, srcf):
        dstf = os.path.join(result_dir, os.path.basename(srcf))
        if os.path.exists(dstf):
            os.remove(dstf)
        trailer = PdfReader(srcf, decompress=False)
        writer = PdfWriter(compress=False)
        writer.write(dstf, trailer)


def test_generator(fname):
    def test(self):
        self.roundtrip(fname)
    return test


def build_tests():
    if not os.path.exists(result_dir):
        os.mkdir(result_dir)
    for fname in pdffiles[0]:
        test_name = 'test_%s' % os.path.basename(fname)
        test = test_generator(fname)
        setattr(TestOnePdf, test_name, test)


def main():
    unittest.main()


build_tests()

if __name__ == '__main__':
    main()
