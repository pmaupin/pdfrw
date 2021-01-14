#! /usr/bin/env python
import hashlib, os

from pdfrw import PdfReader, PdfWriter
from pdfrw.objects import PdfName, PdfDict, IndirectPdfDict

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import static_pdfs


class TestAddPage(unittest.TestCase):

    def test_append_page(self):
        in_filepath = static_pdfs.pdffiles[0][5]  # global/0ae80b493bc21e6de99f2ff6bbb8bc2c.pdf
        out_filepath = "test_append_page.pdf"
        for new_page_index, expected_hash in (
            (0, "d76f5573918cba2070da93a10c19d062"),
            (1, "337677eae9528441f6c8aafef513c461"),
            (-1, "cf306bd87a3a094f506427a5c130c479"),
            (None, "cdd97f6794d78d7ef8be0ddf3101ff9d"),
        ):
            writer = PdfWriter(trailer=PdfReader(in_filepath))
            writer.addpage(new_page(), at_index=new_page_index)
            writer.write(out_filepath)
            self.assertEqual(file_hash(out_filepath), expected_hash)
        os.remove(out_filepath)

def new_page():
    contents = IndirectPdfDict()
    contents.stream = """2 J
0.57 w
BT /F1 36.00 Tf ET
BT 141.73 700.16 Td (Hello!) Tj ET"""
    return PdfDict(
        Type=PdfName.Page,
        Resources=IndirectPdfDict(
            Font=PdfDict(
                F1=IndirectPdfDict(
                    BaseFont=PdfName.Helvetica,
                    Encoding=PdfName.WinAnsiEncoding,
                    Subtype=PdfName.Type1,
                    Type=PdfName.Font,
                ),
            ),
        ),
        Contents=contents,
    )

def file_hash(file_path):
    with open(file_path, 'rb') as data:
        return hashlib.md5(data.read()).hexdigest()


if __name__ == '__main__':
    unittest.main()
