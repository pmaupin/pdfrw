#!/usr/bin/env python

'''
Enhanced example of watermarking using form xobjects (pdfrw).

usage:   fancy_watermark.py [-u] my.pdf single_page.pdf

Creates watermark.my.pdf, with every page overlaid with
first page from single_page.pdf.  If -u is selected, watermark
will be placed underneath page (painted first).

The stock watermark.py program assumes all pages are the same
size.  This example deals with pages of differing sizes in order
to show some concepts of positioning and scaling.

This version applies the watermark such that the upper right
corner of the watermark is at the upper right corner of the
document page for odd pages, and at the upper left corner
of the document page for even pages, for each page of the
document.

It also rescales the size of the watermark if the watermark
is too wide for the page.

These scaling and positioning adjustments can easily
be customized for any particular application.

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
for pagenum, page in enumerate(trailer.pages, 1):

    # Get the media box of the page, and see
    # if we have a matching watermark in the cache
    mbox = tuple(float(x) for x in page.MediaBox)
    odd = pagenum & 1
    key = mbox, odd
    wmark = wmark_cache.get(key)
    if wmark is None:

        # Create and cache a new watermark object.
        wmark = wmark_cache[key] = PageMerge().add(wmark_page)[0]

        # The math is more complete than it probably needs to be,
        # because the origin of all pages is almost always (0, 0).
        # Nonetheless, we illustrate all the values and their names.

        page_x, page_y, page_x1, page_y1 = mbox
        page_w = page_x1 - page_x
        page_h = page_y1 - page_y  # For illustration, not used

        # Scale the watermark if it is too wide for the page
        # (Could do the same for height instead if needed)
        if wmark.w > page_w:
            wmark.scale(1.0 * page_w / wmark.w)

        # Always put watermark at the top of the page
        # (but see horizontal positioning for other ideas)
        wmark.y += page_y1 - wmark.h

        # For odd pages, put it at the left of the page,
        # and for even pages, put it on the right of the page.
        if odd:
            wmark.x = page_x
        else:
            wmark.x += page_x1 - wmark.w

        # Optimize the case where the watermark is same width
        # as page.
        if page_w == wmark.w:
            wmark_cache[mbox, not odd] = wmark

    # Add the watermark to the page
    PageMerge(page).add(wmark, prepend=underneath).render()

# Write out the destination file
PdfWriter().write(outfn, trailer)
