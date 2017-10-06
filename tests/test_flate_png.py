#! /usr/bin/env python
# encoding: utf-8
# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
#                    2017 Henddher Pedroza, Illinois
# MIT license -- See LICENSE.txt for details

'''
Run from the directory above like so:
python -m tests.test_pdfstring
'''


from pdfrw.uncompress import flate_png, flate_png_orig

import unittest
import base64
import array

def create_data(nc=1, nr=1, bpc=8, ncolors=1, filter_type=0):
    pixel_size = (bpc * ncolors + 7) // 8
    data = []
    for r in xrange(nr):
        data.append(filter_type if r > 0 else 0) # filter byte
        for c in xrange(nc * pixel_size):
            data.append(r * nc * pixel_size + c * pixel_size)
    data = array.array('B', data)
    return data, nc, nr, bpc, ncolors

class TestFlatePNG(unittest.TestCase):
    
    def test_flate_png(self):
        b64 = 'AAAAAAD//wACAAA2AAAAAQAADwAAAgEAACcAAQL/AAAzAP8AAgAANgACAAEAAO8AAAABAAF1AAAAAgAANgADAAEAAfsAAAACAAA2AAQCAAAAAAABAgAAAAAAAQIAAAAAAAECAAAAAAABAgAAAAAAAQIAAAAAAAECAAAAAAABAQECBXx8AAIAAAGHAAAAAgAANgAMAAEDCcMAAAACAAA2AA0CAAAAAAABAgAAAAAAAQIAAAAAAAECAAAAAAABAgAAAAAAAQIAAAAAAAECAAAAAAABAgAAAAAAAQABBxI2AAAEAfn5AAAWAgAAAAAAAQIAAAAAAAECAAAAAAABAgAAAAAAAQIAAAAAAAECAAAAAAABAgAAAAAAAQIAAAAAAAEAAQ6fJgAAAAIAADYAHwIAAAAAAAECAAAAAAABAgAAAAAAAQIAAAAAAAECAAAAAAABAgAAAAAAAQABESDsAAAAAgAANgAmAAAAAAD//wIAAAAAAAACARp0hgEBAgAA/eAAAA=='
        predictor, columns, colors, bpc = (12, 6, 1, 8)
        print predictor, columns, colors, bpc

        data = base64.b64decode(b64)
        print len(data)
        d1, error1 = flate_png_orig(data, predictor, columns, colors, bpc)
        print error1

        data = base64.b64decode(b64)
        print len(data)
        d2, error2 = flate_png(data, predictor, columns, colors, bpc)
        print error2

        assert d1 == d2 

    def test_flate_png_filter_0(self):
        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4)
        d1, error1 = flate_png_orig(data, 12, nc, ncolors, bpc) 
        print error1

        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4)
        d2, error2 = flate_png(data, 12, nc, ncolors, bpc)
        print error2

        assert d1 == d2 

    def test_flate_png_filter_1(self):
        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=1)
        d1, error1 = flate_png_orig(data, 12, nc, ncolors, bpc) 
        print error1

        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=1)
        d2, error2 = flate_png(data, 12, nc, ncolors, bpc)
        print error2

        assert d1 == d2 

    def test_flate_png_filter_2(self):
        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=2)
        d1, error1 = flate_png_orig(data, 12, nc, ncolors, bpc) 
        print error1

        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=2)
        d2, error2 = flate_png(data, 12, nc, ncolors, bpc)
        print error2

        assert d1 == d2 

    def test_flate_png_filter_3(self):
        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=3)
        d1, error1 = flate_png_orig(data, 12, nc, ncolors, bpc) 
        print error1

        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=3)
        d2, error2 = flate_png(data, 12, nc, ncolors, bpc)
        print error2

        assert d1 == d2 

    def test_flate_png_filter_4(self):
        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=4)
        d1, error1 = flate_png_orig(data, 12, nc, ncolors, bpc) 
        print error1

        data, nc, nr, bpc, ncolors = create_data(nc=4, nr=6, bpc=8, ncolors=4, filter_type=4)
        d2, error2 = flate_png(data, 12, nc, ncolors, bpc)
        print error2

        assert d1 == d2 


def main():
    unittest.main()


if __name__ == '__main__':
    main()
