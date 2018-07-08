# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details
"""
Run from the directory above like so:

   python -m tests.test_examples

A PDF that has been determined to be good or bad
should be added to expected.txt with either a good
checksum, or just the word "fail".

These tests are incomplete, but they allow us to try
out various PDFs.  There is a collection of difficult
PDFs available on github.

In order to use them:

  1) Insure that github.com/pmaupin/static_pdfs is on your path.

  2) Use the imagemagick compare program to look at differences
     between the static_pdfs/global directory and the tmp_results
     directory after you run this.
"""
import hashlib
import os
import subprocess
import sys
import unittest

import pdfrw_test_data

from . import expected
from pdfrw import PdfReader, PdfWriter
from pdfrw.py23_diffs import convert_store

from examples.alter import alter
from examples.booklet import booklet
from examples.cat import cat
from examples.extract import extract
from examples.get4 import get4
from examples.poster import poster
from examples.print_two import print_two
from examples.rotate import rotate
from examples.subset import subset
from examples.unspread import unspread
from examples.watermark import watermark
from examples.rl1.get4 import get4_reportlab
from examples.rl1.booklet import booklet_reportlab
from examples.rl1.platypus_pdf_template import platypus_template
from examples.rl1.subset import subset_reportlab


prog_dir = os.path.join(expected.root_dir, '..', 'pdfrw/examples', '%s.py')
prog_dir = os.path.abspath(prog_dir)
dstdir = os.path.join(expected.result_dir, 'examples')
hashfile = os.path.join(expected.result_dir, 'hashes.txt')

lookup = pdfrw_test_data.files
lookup = dict((os.path.basename(x)[:-4], x) for x in lookup)


class TestOnePdf(unittest.TestCase):

    def _do_test(self, function, params, prev_results=[''], scrub=False):
        params = params.split()
        hashkey = 'examples/%s' % '_'.join(params)
        params = [lookup.get(x, x) for x in params]
        progname = params[0]
        params[0] = prog_dir % progname
        srcf = params[1]
        subdir, progname = os.path.split(progname)
        subdir = os.path.join(dstdir, subdir)
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        os.chdir(subdir)
        dstf = '%s.%s' % (progname, os.path.basename(srcf))
        scrub = scrub and dstf
        dstf = dstf if not scrub else 'final.%s' % dstf
        hash = '------no-file-generated---------'
        expects = expected.results[hashkey]

        # If the test has been deliberately skipped, we are done. Otherwise,
        # execute it even if we don't know about it yet, so we have results to
        # compare.

        result = 'fail'
        size = 0
        try:
            if 'skip' in expects:
                result = 'skip requested'
                return self.skipTest(result)
            elif 'xfail' in expects:
                result = 'xfail requested'
                return self.fail(result)

            exists = os.path.exists(dstf)
            if expects or not exists:
                if exists:
                    os.remove(dstf)
                if scrub and os.path.exists(scrub):
                    os.remove(scrub)
                #import ipdb; ipdb.set_trace()
                function(*params[1:])
                if scrub:
                    PdfWriter(dstf).addpages(PdfReader(scrub).pages).write()
            with open(dstf, 'rb') as f:
                data = f.read()
            size = len(data)
            if data:
                hash = hashlib.md5(data).hexdigest()
                lookup[hash] = dstf
                prev_results[0] = hash
            else:
                os.remove(dstf)
            if expects:
                if len(expects) == 1:
                    expects, = expects
                    self.assertEqual(hash, expects)
                else:
                    self.assertIn(hash, expects)
                result = 'pass'
            else:
                result = 'skip'
                self.skipTest('No hash available')
        finally:
            result = '%8d %-20s %s %s\n' % (size, result, hashkey, hash)
            with open(hashfile, 'ab') as f:
                f.write(convert_store(result))

    def test_4up(self):
        self._do_test(get4, '4up b1c400de699af29ea3f1983bb26870ab')

    def test_booklet_unspread(self):
        prev = [None]
        self._do_test(booklet, 'booklet b1c400de699af29ea3f1983bb26870ab', prev)
        if prev[0] is not None:
            self._do_test(unspread, 'unspread ' + prev[0])
            self._do_test(extract, 'extract  ' + prev[0])

    def test_print_two(self):
        self._do_test(print_two, 'print_two b1c400de699af29ea3f1983bb26870ab')

    def test_watermarks(self):
        self._do_test(watermark, 'watermark b1c400de699af29ea3f1983bb26870ab '
                      '06c86654f9a77e82f9adaa0086fc391c')
        self._do_test(watermark, 'watermark b1c400de699af29ea3f1983bb26870ab '
                      '06c86654f9a77e82f9adaa0086fc391c True')

    def test_subset(self):
        self._do_test(subset, 'subset b1c400de699af29ea3f1983bb26870ab 1-3 5')

    def test_alter(self):
        self._do_test(alter, 'alter b1c400de699af29ea3f1983bb26870ab')

    def test_cat(self):
        self._do_test(cat, 'cat b1c400de699af29ea3f1983bb26870ab '
                      '06c86654f9a77e82f9adaa0086fc391c')

    def test_rotate(self):
        self._do_test(rotate, 'rotate 707e3e2d17cbe9ec2273414b3b63f333 '
                      '270 1-4 7-8 10-50 52-56')

    def test_poster(self):
        prev = [None]
        self._do_test(subset, 'subset 1975ef8db7355b1d691bc79d0749574b 21', prev)
        self._do_test(rotate, 'rotate %s 90 1' % prev[0], prev)
        self._do_test(poster, 'poster %s' % prev[0], prev)

    def test_extract(self):
        self._do_test(extract, 'extract 1975ef8db7355b1d691bc79d0749574b')
        self._do_test(extract, 'extract c5c895deecf7a7565393587e0d61be2b')

    def test_rl1_4up(self):
        self._do_test(
            get4_reportlab,
            'rl1/4up b1c400de699af29ea3f1983bb26870ab',
            scrub=True,
        )

    def test_rl1_booklet(self):
        self._do_test(
            booklet_reportlab,
            'rl1/booklet b1c400de699af29ea3f1983bb26870ab',
            scrub=True,
        )

    def test_rl1_subset(self):
        self._do_test(
            subset_reportlab,
            'rl1/subset b1c400de699af29ea3f1983bb26870ab 3 5',
            scrub=True,
        )

    def test_rl1_platypus(self):
        self._do_test(
            platypus_template,
            'rl1/platypus_pdf_template b1c400de699af29ea3f1983bb26870ab',
            scrub=True,
        )
