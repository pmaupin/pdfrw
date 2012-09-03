#!/usr/bin/env python
'''
Scrape PDF db.

Must pass it a list of entries to get.

'''
import subprocess
import sys

dirs = sys.argv[1:]
if not dirs:
    raise SystemExit('''
Usage:

1) Go to http://www.stillhq.com/pdfdb/db.html
2) Copy the list of documents you want (e.g. under "all documents" at the bottom)
3) Paste that list onto the command line.
''')

files = []
for d in dirs:
    d = 'http://www.stillhq.com/pdfdb/%s/' % d
    files.append(d + 'info.html')
    files.append(d + 'data.pdf')

prefix = '/usr/bin/wget -N --force-directories --directory-prefix=data --limit-rate=500k'.split()
while files:
    shortlist = files[-8:]
    del files[-8:]
    result = subprocess.call(prefix + shortlist)
    print result, len(files)
