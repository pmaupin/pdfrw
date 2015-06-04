#! /usr/bin/env python

'''
Run from the directory above like so:

   python -m tests.test_roundtrip

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


'''
import os
import unittest
import hashlib
import pdfrw
import static_pdfs
import expected

from pdfrw.py23_diffs import convert_store

class TestOnePdf(unittest.TestCase):

    def roundtrip(self, testname, basename, srcf, decompress=False,
                  compress=False, repaginate=False):
        dstd = os.path.join(expected.result_dir, testname)
        if not os.path.exists(dstd):
            os.makedirs(dstd)
        dstf = os.path.join(dstd, basename)
        hashfile = os.path.join(expected.result_dir, 'hashes.txt')
        hashkey = '%s/%s' % (testname, basename)
        hash = '------no-file-generated---------'
        expects = expected.results[hashkey]

        # If the test has been deliberately skipped,
        # we are done.  Otherwise, execute it even
        # if we don't know about it yet, so we have
        # results to compare.

        if 'skip' in expects:
            return self.skipTest('skip requested')
        elif 'xfail' in expects:
            return self.fail('xfail requested')

        exists = os.path.exists(dstf)
        try:
            if expects or not exists:
                if exists:
                    os.remove(dstf)
                trailer = pdfrw.PdfReader(srcf, decompress=decompress)
                writer = pdfrw.PdfWriter(compress=compress)
                if repaginate:
                    writer.addpages(trailer.pages)
                    trailer = None
                writer.write(dstf, trailer)
            with open(dstf, 'rb') as f:
                data = f.read()
            hash = hashlib.md5(data).hexdigest()
            if expects:
                if len(expects) == 1:
                    expects, = expects
                    self.assertEqual(hash, expects)
                else:
                    self.assertIn(hash, expects)
            else:
                self.skipTest('No hash available')
        finally:
            result = '%s %s\n' % (hashkey, hash)
            with open(hashfile, 'ab') as f:
                f.write(convert_store(result))


def build_tests():
    def test_closure(*args, **kw):
        def test(self):
            self.roundtrip(*args, **kw)
        return test
    for mytest, repaginate in (
        ('simple', False),
        ('repaginate', True)
        ):
        for srcf in static_pdfs.pdffiles[0]:
            basename = os.path.basename(srcf)
            test_name = 'test_%s_%s' % (mytest, basename)
            test = test_closure(mytest, basename, srcf,
                                repaginate=repaginate)
            setattr(TestOnePdf, test_name, test)
build_tests()


def main():
    unittest.main()

if __name__ == '__main__':
    main()
