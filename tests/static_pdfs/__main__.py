#! /usr/bin/env python

'''
Static PDFs are maintained by MD5

You may have local-only PDFs in the
local subdirectory, or global PDFs in
the global subdirectory.  Only the
global ones are stored at github.

Part of github.com/pmaupin/static_pdfs.

'''

import sys
import os
import collections
import hashlib
import static_pdfs

params = sys.argv[1:]

destroy = params == ['destroy']
if params and not destroy:
    raise SystemExit('''

usage: static_pdfs [destroy]

Without the parameter, static_pdfs will only report on the
state of the files in the global and local subdirectories.

With the destroy parameter, static_pdfs will de-duplicate
and rename files so that the filename of the PDF is its
md5.
''')


found = collections.defaultdict(list)

sys.stdout.write('\n\nReading PDFs:\n\n')

for filelist in static_pdfs.pdffiles:
    for fname in filelist:
        sys.stdout.write('  %s\r' % fname)
        with open(fname, 'rb') as f:
            data = f.read()
        hexname = hashlib.md5(data).hexdigest()
        found[hexname].append(fname)
sys.stdout.write('\n\n')

for key, values in found.items():
    if len(values) > 1:
        sys.stdout.write('\n\nDuplicates%s:\n    %s' % (
            ' (destroying)' if destroy else '', '\n    '.join(values)))
        if destroy:
            while len(values) > 1:
                os.remove(values.pop())
    key = os.path.join(os.path.dirname(values[0]), key + '.pdf')
    if values[0] != key:
        sys.stdout.write('\n\nBad name for %s%s:\n    %s' % (
            key, ' (renaming)' if destroy else '', values[0]))
        if destroy:
            os.rename(values[0], key)
sys.stdout.write('\n\n')
