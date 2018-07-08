#! /usr/bin/env python
import unittest

import pdfrw_test_data

from pdfrw import PdfReader


class TestPdfReaderInit(unittest.TestCase):

    def test_fname_binary_filelike(self):
        with open(pdfrw_test_data.files[0], 'rb') as pdf_file:
            PdfReader(pdf_file)

    def test_fdata_binary(self):
        with open(pdfrw_test_data.files[0], 'rb') as pdf_file:
            pdf_bytes = pdf_file.read()
            PdfReader(fdata=pdf_bytes)
