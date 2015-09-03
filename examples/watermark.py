#!/usr/bin/env python

'''
Simple example of watermarking using form xobjects (pdfrw).

usage:   watermark.py [-u] my.pdf single_page.pdf

Creates watermark.my.pdf, with every page overlaid with
first page from single_page.pdf.  If -u is selected, watermark
will be placed underneath page (painted first).

NB:  At one point, this example was extremely complicated, with
     multiple options.  That only led to errors in implementation,
     so it has been re-simplified in order to show basic principles
     of the library operation and to match the other examples better.

The original version of this program assumed that the watermark
page and the document to be watermarked had the same page size.

This version applies the watermark such that the upper right
corner of the watermark is at the upper right corner of the
document page, for each page of the document.  (It makes the
assumption that the lower left corner of both is (0, 0).)

To handle documents with different page sizes, a cache is
maintained of a modified intermediate watermark object
for each page size.
'''

import sys
import os

from pdfrw import PdfReader, PdfWriter, PageMerge

# Get all the filenames

argv = sys.argv[1:]
underneath = '-u' in argv
if underneath:
    del argv[argv.index('-u')]
inpfn, wmarkfn = argv
outfn = 'watermark.' + os.path.basename(inpfn)

# Open both the source files
wmark_trailer = PdfReader(wmarkfn)
trailer = PdfReader(inpfn)

# Handle different sized pages in same document with
# a memoization cache, so we don't create more watermark
# objects than we need to (typically only one per document).

wmark_page = wmark_trailer.pages[0]
wmark_cache = {}

# Process every page
for page in trailer.pages:

    # Get the media box of the page, and see
    # if we have a matching watermark in the cache
    mbox = tuple(float(x) for x in page.MediaBox)
    wmark = wmark_cache.get(mbox)
    if wmark is None:

        # Create and cache a new watermark object.
        wmark = wmark_cache[mbox] = PageMerge().add(wmark_page)[0]

        # Adjust it so that the top-right corner matches
        # the top-right corner of the page

        wmark.x += mbox[2] - wmark.w  # Adjust left/right
        wmark.y += mbox[3] - wmark.h  # Adjust up/down

    # Add the watermark to the page
    PageMerge(page).add(wmark, prepend=underneath).render()

# Write out the destination file
PdfWriter().write(outfn, trailer)
