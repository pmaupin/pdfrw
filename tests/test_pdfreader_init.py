#! /usr/bin/env python
import static_pdfs

from pdfrw import PdfReader

try:
    import unittest2 as unittest
except ImportError:
    import unittest


class TestPdfReaderInit(unittest.TestCase):

    def test_fname_binary_filelike(self):
        with open(static_pdfs.pdffiles[0][0], 'rb') as pdf_file:
            PdfReader(pdf_file)

    def test_fdata_binary(self):
        with open(static_pdfs.pdffiles[0][0], 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
            PdfReader(fdata=pdf_bytes)


def main():
    unittest.main()

if __name__ == '__main__':
    main()
