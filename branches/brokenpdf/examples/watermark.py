#!/usr/bin/env python

'''
Simple example of watermarking using form xobjects (pdfrw).

usage:   watermark.py my.pdf single_page.pdf

Creates watermark.my.pdf, with every page overlaid with
first page from single_page.pdf
'''

import sys
import os

import find_pdfrw
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, IndirectPdfDict, PdfArray
from pdfrw.buildxobj import pagexobj

def fixpage(page, watermark):

    # Find the page's resource dictionary. Create if none
    resources = page.inheritable.Resources
    if resources is None:
        resources = page.Resources = PdfDict()

    # Find or create the parent's xobject dictionary
    xobjdict = resources.XObject
    if xobjdict is None:
        xobjdict = resources.XObject = PdfDict()

    # Allow for an infinite number of cascaded watermarks
    index = 0
    while 1:
        watermark_name = '/Watermark.%d' % index
        if watermark_name not in xobjdict:
            break
        index += 1
    xobjdict[watermark_name] = watermark

    # Turn the contents into an array if it is not already one
    contents = page.Contents
    if not isinstance(contents, PdfArray):
        contents = page.Contents = PdfArray([contents])

    # Save initial state before executing page
    contents.insert(0, IndirectPdfDict(stream='q\n'))

    # Restore initial state and append the watermark
    contents.append(IndirectPdfDict(stream='Q %s Do\n' % watermark_name))
    return page

def watermark(input_fname, watermark_fname, output_fname=None):
    outfn = output_fname or ('watermark.' + os.path.basename(input_fname))
    w = pagexobj(PdfReader(watermark_fname, decompress=False).pages[0])
    pages = PdfReader(input_fname, decompress=False).pages
    PdfWriter().addpages([fixpage(x, w) for x in pages]).write(outfn)
    return outfn

def fix_pdf(fname, watermark_fname, indir, outdir):
    from os import mkdir, path
    if not path.exists(outdir):
        mkdir(outdir)
    watermark = pagexobj(PdfReader(watermark_fname, decompress=False).pages[0])
    trailer = PdfReader(path.join(indir, fname), decompress=False)
    for page in trailer.pages:
        fixpage(page, watermark)
    PdfWriter().write(path.join(outdir, fname), trailer)
    return len(trailer.pages)
    
def batch_watermark(pdfdir, watermark_fname, outputdir='tmp'):
    import traceback
    from glob import glob
    from os import path
    fnames=glob(pdfdir+"/*.pdf")
    total_pages = 0
    good_files = 0
    
    for fname in fnames:
        fname = fname.replace(pdfdir+'/','')
        try:
            total_pages += fix_pdf(fname, watermark_fname, pdfdir, outputdir)
            good_files += 1
            print "%s OK" %fname
        except Exception:
            print "%s Failed miserably" %fname
            print traceback.format_exc()[:2000]
            #raise
    
    print "success %.2f%% %s pages" %((float(good_files)/len(fnames))*100, total_pages)
    
if __name__ == "__main__":
    
    from optparse import OptionParser
    parser = OptionParser(description = __doc__)
    parser.add_option('-i', dest='input_fname', help='file name to be watermarked (pdf)')
    parser.add_option('-w', dest='watermark_fname', help='watermark file name (pdf)')
    parser.add_option('-d', dest='pdfdir', help='watermark all pdf files in this directory')
    parser.add_option('-o', dest='outdir', help='outputdir used with option -d', default='tmp')
    options, args = parser.parse_args()
    
    if options.input_fname and options.watermark_fname:
        watermark = pagexobj(PdfReader(options.watermark_fname, decompress=False).pages[0])
        outfn = 'watermark.' + os.path.basename(options.input_fname)
        pages = PdfReader(options.input_fname, decompress=False).pages
        
        PdfWriter().addpages([fixpage(x, watermark) for x in pages]).write(outfn)
    
    elif options.pdfdir and options.watermark_fname:
        batch_watermark(options.pdfdir, options.watermark_fname, options.outdir)
    
    else:
        parser.print_help()
        
        