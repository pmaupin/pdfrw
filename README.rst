=============
pdfrw 0.2
=============

:Author: Patrick Maupin

.. contents::
    :backlinks: none

.. sectnum::

Introduction
============

**pdfrw** is a Python library and utility that reads and writes PDF files:

* Version 0.2 works on Python 2.6, 2.7, 3.3, and 3.4.
* Operations include subsetting, merging, rotating, modifying metadata, etc.
* The fastest pure PDF parser available
* Has been used for years by a printer in pre-press production
* Can be used either standalone, or in conjunction with `reportlab`__
  to reuse existing PDFs in new ones
* Permissively licensed

__ http://www.reportlab.org/

Although pdfrw is not as full-featured as some other libraries,
it is small, fast, easy-to-understand, and quite useful for
some scenarios.

Examples
=========

The library comes with several examples that show operation both with
and without reportlab.


Introduction
------------

The examples directory has a few scripts which use the library.
Note that if these examples do not work with your PDF, you should
try to use pdftk to uncompress and/or unencrypt them first.

* `4up.py`__ will shrink pages down and place 4 of them on
  each output page.
* `alter.py`__ shows an example of modifying metadata, without
  altering the structure of the PDF.
* `booklet.py`__ shows an example of creating a 2-up output
  suitable for printing and folding (e.g on tabloid size paper).
* `cat.py`__ shows an example of concatenating multiple PDFs together.
* `extract.py`__ will extract images and Form XObjects (embedded pages)
  from existing PDFs to make them easier to use and refer to from
  new PDFs (e.g. with reportlab or rst2pdf).
* `poster.py`__ increases the size of a PDF so it can be printed
  as a poster.
* `print_two.py`__ Allows creation of 8.5 X 5.5" booklets by slicing
  8.5 X 11" paper apart after printing.
* `rotate.py`__ Rotates all or selected pages in a PDF.
* `subset.py`__ Creates a new PDF with only a subset of pages from the
  original.
* `unspread.py`__ Takes a 2-up PDF, and splits out pages.
* `watermark.py`__ Adds a watermark PDF image over or under all the pages
  of a PDF.
* `rl1/4up.py`__ Another 4up example, using reportlab canvas for output.
* `rl1/booklet.py`__ Another booklet example, using reportlab canvas for
  output.
* `rl1/platypus_pdf_template.py`__ Aother watermarking example, using
  reportlab canvas and generated output for the document.
* `rl2`__ Experimental code for parsing graphics.  Needs work.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/4up.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/alter.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/booklet.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/cat.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/extract.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/poster.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/print_two.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rotate.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/subset.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/unspread.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/watermark.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl1/4up.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl1/booklet.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl1/platypus_pdf_template.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl2/

Notes on selected examples
------------------------------------

`booklet.py`__
````````````````

__ https://github.com/pmaupin/pdfrw/tree/master/examples/booklet.py

A printer with a fancy printer and/or a full-up copy of Acrobat can
easily turn your small PDF into a little booklet (for example, print 4
letter-sized pages on a single 11" x 17").

But that assumes several things, including that the personnel know how
to operate the hardware and software. booklet.py lets you turn your PDF
into a preformatted booklet, to give them fewer chances to mess it up.

Adding or modifying metadata
----------------------------

The `cat.py`__ example will accept multiple input files on the command
line, concatenate them and output them to output.pdf, after adding some
nonsensical metadata to the output PDF file.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/cat.py

The `alter.py`__ example alters a single metadata item in a PDF,
and writes the result to a new PDF.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/alter.py


One difference is that, since **cat** is creating a new PDF structure,
and **alter** is attempting to modify an existing PDF structure, the
PDF produced by alter (and also by watermark.py) *should* be
more faithful to the original (except for the desired changes).

For example, the alter.py navigation should be left intact, whereas with
cat.py it will be stripped.


Rotating and doubling
-----------------------------------

If you ever want to print something that is like a small booklet, but
needs to be spiral bound, you either have to do some fancy rearranging,
or just waste half your paper.

The `print_two.py`__ example program will, for example, make two side-by-side
copies each page of of your PDF on a each output sheet.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/print_two.py

But, every other page is flipped, so that you can print double-sided and
the pages will line up properly and be pre-collated.

Graphics stream parsing proof of concept
----------------------------------------

The `copy.py`__ script shows a simple example of reading in a PDF, and
using the decodegraphics.py module to try to write the same information
out to a new PDF through a reportlab canvas. (If you know about reportlab,
you know that if you can faithfully render a PDF to a reportlab canvas, you
can do pretty much anything else with that PDF you want.) This kind of
low level manipulation should be done only if you really need to.
decodegraphics is really more than a proof of concept than anything
else. For most cases, just use the Form XObject capability, as shown in
the examples/rl1/booklet.py demo.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl2/copy.py

pdfrw philosophy
==================

Core library
-------------

The philosophy of the library portion of pdfrw is to provide intuitive
functions to read, manipulate, and write PDF files.  There should be
minimal leakage between abstraction layers, although getting useful
work done makes "pure" functionality separation difficult.

A key concept supported by the library is the use of Form XObjects,
which allow easy embedding of pieces of one PDF into another.

Addition of core support to the library is typically done carefully
and thoughtfully, so as not to clutter it up with too many special
cases.

There are a lot of incorrectly formatted PDFs floating around; support
for these is added in some cases.  The decision is often based on what
acroread and okular do with the PDFs; if they can display them properly,
then eventually pdfrw should, too, if it is not too difficult or costly.

Contributions are welcome; one user has contributed some decompression
filters and the ability to process PDF 1.5 stream objects.  Additional
functionality that would obviously be useful includes additional
decompression filters, the ability to process password-protected PDFs,
and the ability to output linearized PDFs.

Examples
--------

The philosophy of the examples is to provide small, easily-understood
examples that showcase pdfrw functionality.


Release information
=======================

Revisions:

0.2 -- In development.  Will support Python 2.6, 2.7, 3.3, and 3.4.

    - Several bugs have been fixed
    - New regression test functionally tests core with dozens of
      PDFs, and also tests examples.
    - Core has been ported and tested on Python3 by round-tripping
      several difficult files and observing binary matching results
      across the different Python versions.
    - Still only minimal support for compression and no support
      for encryption or newer PDF features.  (pdftk is useful
      to put PDFs in a form that pdfrw can use.)

0.1 -- Released to PyPI.  Supports Python 2.5 - 2.7


PDF files and Python
======================

Introduction
------------

In general, PDF files conceptually map quite well to Python. The major
objects to think about are:

-  **strings**. Most things are strings. These also often decompose
   naturally into
-  **lists of tokens**. Tokens can be combined to create higher-level
   objects like
-  **arrays** and
-  **dictionaries** and
-  **Contents streams** (which can be more streams of tokens)

Difficulties
------------

The apparent primary difficulty in mapping PDF files to Python is the
PDF file concept of "indirect objects."  Indirect objects provide
the efficiency of allowing a single piece of data to be referred to
from more than one containing object, but probably more importantly,
indirect objects provide a way to get around the chicken and egg
problem of circular object references when mapping arbitrary data
structures to files. To flatten out a circular reference, an indirect
object is *referred to* instead of being *directly included* in another
object. PDF files have a global mechanism for locating indirect objects,
and they all have two reference numbers (a reference number and a
"generation" number, in case you wanted to append to the PDF file
rather than just rewriting the whole thing).

pdfrw automatically handles indirect references on reading in a PDF
file. When pdfrw encounters an indirect PDF file object, the
corresponding Python object it creates will have an 'indirect' attribute
with a value of True. When writing a PDF file, if you have created
arbitrary data, you just need to make sure that circular references are
broken up by putting an attribute named 'indirect' which evaluates to
True on at least one object in every cycle.

Another PDF file concept that doesn't quite map to regular Python is a
"stream". Streams are dictionaries which each have an associated
unformatted data block. pdfrw handles streams by placing a special
attribute on a subclassed dictionary.

Usage Model
-----------

The usage model for pdfrw treats most objects as strings (it takes their
string representation when writing them to a file). The two main
exceptions are the PdfArray object and the PdfDict object.

PdfArray is a subclass of list with two special features.  First,
an 'indirect' attribute allows a PdfArray to be written out as
an indirect PDF object.  Second, pdfrw reads files lazily, so
PdfArray knows about, and resolves references to other indirect
objects on an as-needed basis.

PdfDict is a subclass of dict that also has an indirect attribute
and lazy reference resolution as well.  (And the subclassed
IndirectPdfDict has indirect automatically set True).

But PdfDict also has an optional associated stream. The stream object
defaults to None, but if you assign a stream to the dict, it will
automatically set the PDF /Length attribute for the dictionary.

Finally, since PdfDict instances are indexed by PdfName objects (which
always start with a /) and since most (all?) standard Adobe PdfName
objects use names formatted like "/CamelCase", it makes sense to allow
access to dictionary elements via object attribute accesses as well as
object index accesses. So usage of PdfDict objects is normally via
attribute access, although non-standard names (though still with a
leading slash) can be accessed via dictionary index lookup.

The PdfReader object is a subclass of PdfDict, which allows easy access
to an entire document::

    >>> from pdfrw import PdfReader
    >>> x = PdfReader('source.pdf')
    >>> x.keys()
    ['/Info', '/Size', '/Root']
    >>> x.Info
    {'/Producer': '(cairo 1.8.6 (http://cairographics.org))',
     '/Creator': '(cairo 1.8.6 (http://cairographics.org))'}
    >>> x.Root.keys()
    ['/Type', '/Pages']

Info, Size, and Root are retrieved from the trailer of the PDF file.

In addition to the tree structure, pdfrw creates a special attribute
named pages, that is a list of all the pages in the document. It is created
because the PDF format allows arbitrarily complicated nested
dictionaries to describe the page order. Each entry in the pages list is
the PdfDict object for one of the pages in the file, in order.

::

    >>> len(x.pages)
    1
    >>> x.pages[0]
    {'/Parent': {'/Kids': [{...}], '/Type': '/Pages', '/Count': '1'},
     '/Contents': {'/Length': '11260', '/Filter': None},
     '/Resources': ... (Lots more stuff snipped)
    >>> x.pages[0].Contents
    {'/Length': '11260', '/Filter': None}
    >>> x.pages[0].Contents.stream
    'q\n1 1 1 rg /a0 gs\n0 0 0 RG 0.657436
      w\n0 J\n0 j\n[] 0.0 d\n4 M q' ... (Lots more stuff snipped)

As you can see, it is quite easy to dig down into a PDF document. But
what about when it's time to write it out?

::

    >>> from pdfrw import PdfWriter
    >>> y = PdfWriter()
    >>> y.addpage(x.pages[0])
    >>> y.write('result.pdf')

That's all it takes to create a new PDF. You still need to read the
`Adobe PDF reference manual`__ to figure out what needs to go *into*
the PDF, but at least you don't have to sweat actually building it
and getting the file offsets right.

__ http://www.adobe.com/devnet/acrobat/pdfs/pdf_reference_1-7.pdf


Library internals and other libraries
========================================

Coming soon!  For now, please peruse the wiki -- not all material has
been migrated from there yet.
