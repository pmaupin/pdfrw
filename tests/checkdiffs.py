#! /usr/bin/env python2

import sys
import os
import subprocess
import hashlib

import expected
import static_pdfs

source_pdfs = static_pdfs.pdffiles[0]
source_pdfs = dict((os.path.basename(x), x) for x in source_pdfs)

result_dir = expected.result_dir

for subdir in sorted(os.listdir(result_dir)):
    dstd = os.path.join(result_dir, subdir)
    if not os.path.isdir(dstd):
        continue
    for pdffile in sorted(os.listdir(dstd)):
        testname = '%s/%s' % (subdir, pdffile)
        srcf = source_pdfs.get(pdffile)
        dstf = os.path.join(dstd, pdffile)
        if pdffile not in source_pdfs:
            print('\n Skipping %s -- source not found' % testname)
            continue

        with open(dstf, 'rb') as f:
            data = f.read()
        hash = hashlib.md5(data).hexdigest()
        skipset = set((hash, 'skip', 'xfail', 'fail', '!' + hash))
        if expected.results[testname] & skipset:
            print('\n Skipping %s -- marked done' % testname)
            continue
        if os.path.exists('foobar.pdf'):
            os.remove('foobar.pdf')
        builtdiff = False
        while 1:
            sys.stdout.write('''
                Test case %s

                c = compare using imagemagick and okular
                f = display foobar.pdf (result from comparison)
                o = display results with okular
                a = display results with acrobat

                s = mark 'skip' and go to next PDF
                g = mark as good and go to next PDF
                b = mark as bad and go to next PDF
                n = next pdf without marking
                q = quit
-->  ''' % testname)
            sel = raw_input()
            if sel == 'q':
                raise SystemExit(0)
            if sel == 'n':
                break
            if sel == 'c':
                subprocess.call(('compare', '-verbose', srcf, dstf,
                                 'foobar.pdf'))
                builtdiff = True
                continue
            if sel == 'f':
                subprocess.call(('okular', 'foobar.pdf'))
                continue
            if sel == 'o':
                subprocess.call(('okular', srcf, dstf))
                continue
            if sel == 'a':
                if builtdiff:
                    subprocess.call(('acroread', srcf, dstf, 'foobar.pdf'))
                else:
                    subprocess.call(('acroread', srcf, dstf))
                continue

            if sel in 'sgb':
                results = (hash if sel == 'g' else
                           '    skip' if sel == 's' else '!'+hash)
                with open(expected.expectedf, 'a') as f:
                    f.write('%s %s\n' % (testname, results))
                break
