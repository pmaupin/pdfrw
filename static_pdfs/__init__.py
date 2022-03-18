'''
Static PDFs are maintained by MD5

You may have local-only PDFs in the
local subdirectory, or global PDFs in
the global subdirectory.  Only the
global ones are stored at github.

Part of github.com/pmaupin/static_pdfs.

'''

import os

rootdir = os.path.abspath(os.path.dirname(__file__))

# GLOBAL IS ASSUMED TO BE FIRST!!!

pdfpaths = 'global', 'local'

pdfpaths = [os.path.join(rootdir, x) for x in pdfpaths]

pdffiles = [[os.path.join(x, y) for y in os.listdir(x)]
            for x in pdfpaths if os.path.exists(x)]

allpdfs = sum(pdffiles, [])

