==================
pdfrw 0.4
==================

:Author: Patrick Maupin

.. contents::
    :backlinks: none

.. sectnum::

Introduction
============

**pdfrw** is a Python library and utility that reads and writes PDF files:

* Version 0.4 is tested and works on Python 2.6, 2.7, 3.3, 3.4, 3.5, and 3.6
* Operations include subsetting, merging, rotating, modifying metadata, etc.
* The fastest pure Python PDF parser available
* Has been used for years by a printer in pre-press production
* Can be used with rst2pdf to faithfully reproduce vector images
* Can be used either standalone, or in conjunction with `reportlab`__
  to reuse existing PDFs in new ones
* Permissively licensed

__ http://www.reportlab.org/


pdfrw will faithfully reproduce vector formats without
rasterization, so the rst2pdf package has used pdfrw
for PDF and SVG images by default since March 2010.

pdfrw can also be used in conjunction with reportlab, in order
to re-use portions of existing PDFs in new PDFs created with
reportlab.


Examples
=========

The library comes with several examples that show operation both with
and without reportlab.


All examples
------------------

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
* `rl1/subset.py`__ Another subsetting example, using reportlab canvas for
  output.
* `rl1/platypus_pdf_template.py`__ Another watermarking example, using
  reportlab canvas and generated output for the document.  Contributed
  by user asannes.
* `rl2`__ Experimental code for parsing graphics.  Needs work.
* `subset_booklets.py`__ shows an example of creating a full printable pdf
  version in a more professional and pratical way ( take a look at
  http://www.wikihow.com/Bind-a-Book )

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
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl1/subset.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl1/platypus_pdf_template.py
__ https://github.com/pmaupin/pdfrw/tree/master/examples/rl2/
__ https://github.com/pmaupin/pdfrw/tree/master/examples/subset_booklets.py

Notes on selected examples
------------------------------------

Reorganizing pages and placing them two-up
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

A printer with a fancy printer and/or a full-up copy of Acrobat can
easily turn your small PDF into a little booklet (for example, print 4
letter-sized pages on a single 11" x 17").

But that assumes several things, including that the personnel know how
to operate the hardware and software. `booklet.py`__ lets you turn your PDF
into a preformatted booklet, to give them fewer chances to mess it up.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/booklet.py

Adding or modifying metadata
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you ever want to print something that is like a small booklet, but
needs to be spiral bound, you either have to do some fancy rearranging,
or just waste half your paper.

The `print_two.py`__ example program will, for example, make two side-by-side
copies each page of of your PDF on a each output sheet.

__ https://github.com/pmaupin/pdfrw/tree/master/examples/print_two.py

But, every other page is flipped, so that you can print double-sided and
the pages will line up properly and be pre-collated.

Graphics stream parsing proof of concept
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Reading PDFs
~~~~~~~~~~~~~~~

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
named *pages*, that is a list of all the pages in the document. pdfrw
creates the *pages* attribute as a simplification for the user, because
the PDF format allows arbitrarily complicated nested dictionaries to
describe the page order. Each entry in the *pages* list is the PdfDict
object for one of the pages in the file, in order.

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

Writing PDFs
~~~~~~~~~~~~~~~

As you can see, it is quite easy to dig down into a PDF document. But
what about when it's time to write it out?

::

    >>> from pdfrw import PdfWriter
    >>> y = PdfWriter()
    >>> y.addpage(x.pages[0])
    >>> y.write('result.pdf')

That's all it takes to create a new PDF. You may still need to read the
`Adobe PDF reference manual`__ to figure out what needs to go *into*
the PDF, but at least you don't have to sweat actually building it
and getting the file offsets right.

__ http://www.adobe.com/devnet/acrobat/pdfs/pdf_reference_1-7.pdf

Manipulating PDFs in memory
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For the most part, pdfrw tries to be agnostic about the contents of
PDF files, and support them as containers, but to do useful work,
something a little higher-level is required, so pdfrw works to
understand a bit about the contents of the containers.  For example:

-  PDF pages. pdfrw knows enough to find the pages in PDF files you read
   in, and to write a set of pages back out to a new PDF file.
-  Form XObjects. pdfrw can take any page or rectangle on a page, and
   convert it to a Form XObject, suitable for use inside another PDF
   file.  It knows enough about these to perform scaling, rotation,
   and positioning.
-  reportlab objects. pdfrw can recursively create a set of reportlab
   objects from its internal object format. This allows, for example,
   Form XObjects to be used inside reportlab, so that you can reuse
   content from an existing PDF file when building a new PDF with
   reportlab.

There are several examples that demonstrate these features in
the example code directory.

Missing features
~~~~~~~~~~~~~~~~~~~~~~~

Even as a pure PDF container library, pdfrw comes up a bit short. It
does not currently support:

-  Most compression/decompression filters
-  encryption

`pdftk`__ is a wonderful command-line
tool that can convert your PDFs to remove encryption and compression.
However, in most cases, you can do a lot of useful work with PDFs
without actually removing compression, because only certain elements
inside PDFs are actually compressed.

__ https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/

Library internals
==================

Introduction
------------

**pdfrw** currently consists of 19 modules organized into a main
package and one sub-package.

The `__init.py__`__ module does the usual thing of importing a few
major attributes from some of the submodules, and the `errors.py`__
module supports logging and exception generation.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/__init__.py
__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/errors.py


PDF object model support
--------------------------

The `objects`__ sub-package contains one module for each of the
internal representations of the kinds of basic objects that exist
in a PDF file, with the `objects/__init__.py`__ module in that
package simply gathering them up and making them available to the
main pdfrw package.

One feature that all the PDF object classes have in common is the
inclusion of an 'indirect' attribute. If 'indirect' exists and evaluates
to True, then when the object is written out, it is written out as an
indirect object. That is to say, it is addressable in the PDF file, and
could be referenced by any number (including zero) of container objects.
This indirect object capability saves space in PDF files by allowing
objects such as fonts to be referenced from multiple pages, and also
allows PDF files to contain internal circular references.  This latter
capability is used, for example, when each page object has a "parent"
object in its dictionary.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/
__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/__init__.py

Ordinary objects
~~~~~~~~~~~~~~~~

The `objects/pdfobject.py`__ module contains the PdfObject class, which is
a subclass of str, and is the catch-all object for any PDF file elements
that are not explicitly represented by other objects, as described below.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/pdfobject.py

Name objects
~~~~~~~~~~~~

The `objects/pdfname.py`__ module contains the PdfName singleton object,
which will convert a string into a PDF name by prepending a slash. It can
be used either by calling it or getting an attribute, e.g.::

    PdfName.Rotate == PdfName('Rotate') == PdfObject('/Rotate')

In the example above, there is a slight difference between the objects
returned from PdfName, and the object returned from PdfObject.  The
PdfName objects are actually objects of class "BasePdfName".  This
is important, because only these may be used as keys in PdfDict objects.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/pdfname.py

String objects
~~~~~~~~~~~~~~

The `objects/pdfstring.py`__
module contains the PdfString class, which is a subclass of str that is
used to represent encoded strings in a PDF file. The class has encode
and decode methods for the strings.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/pdfstring.py


Array objects
~~~~~~~~~~~~~

The `objects/pdfarray.py`__
module contains the PdfArray class, which is a subclass of list that is
used to represent arrays in a PDF file. A regular list could be used
instead, but use of the PdfArray class allows for an indirect attribute
to be set, and also allows for proxying of unresolved indirect objects
(that haven't been read in yet) in a manner that is transparent to pdfrw
clients.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/pdfarray.py

Dict objects
~~~~~~~~~~~~

The `objects/pdfdict.py`__
module contains the PdfDict class, which is a subclass of dict that is
used to represent dictionaries in a PDF file. A regular dict could be
used instead, but the PdfDict class matches the requirements of PDF
files more closely:

* Transparent (from the library client's viewpoint) proxying
  of unresolved indirect objects
* Return of None for non-existent keys (like dict.get)
* Mapping of attribute accesses to the dict itself
  (pdfdict.Foo == pdfdict[NameObject('Foo')])
* Automatic management of following stream and /Length attributes
  for content dictionaries
* Indirect attribute
* Other attributes may be set for private internal use of the
  library and/or its clients.
* Support for searching parent dictionaries for PDF "inheritable"
  attributes.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/pdfdict.py

If a PdfDict has an associated data stream in the PDF file, the stream
is accessed via the 'stream' (all lower-case) attribute.  Setting the
stream attribute on the PdfDict will automatically set the /Length attribute
as well.  If that is not what is desired (for example if the the stream
is compressed), then _stream (same name with an underscore) may be used
to associate the stream with the PdfDict without setting the length.

To set private attributes (that will not be written out to a new PDF
file) on a dictionary, use the 'private' attribute::

    mydict.private.foo = 1

Once the attribute is set, it may be accessed directly as an attribute
of the dictionary::

    foo = mydict.foo

Some attributes of PDF pages are "inheritable."  That is, they may
belong to a parent dictionary (or a parent of a parent dictionary, etc.)
The "inheritable" attribute allows for easy discovery of these::

    mediabox = mypage.inheritable.MediaBox


Proxy objects
~~~~~~~~~~~~~

The `objects/pdfindirect.py`__
module contains the PdfIndirect class, which is a non-transparent proxy
object for PDF objects that have not yet been read in and resolved from
a file. Although these are non-transparent inside the library, client code
should never see one of these -- they exist inside the PdfArray and PdfDict
container types, but are resolved before being returned to a client of
those types.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/objects/pdfindirect.py


File reading, tokenization and parsing
--------------------------------------

`pdfreader.py`__
contains the PdfReader class, which can read a PDF file (or be passed a
file object or already read string) and parse it. It uses the PdfTokens
class in `tokens.py`__  for low-level tokenization.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/pdfreader.py
__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/tokens.py


The PdfReader class does not, in general, parse into containers (e.g.
inside the content streams). There is a proof of concept for doing that
inside the examples/rl2 subdirectory, but that is slow and not well-developed,
and not useful for most applications.

An instance of the PdfReader class is an instance of a PdfDict -- the
trailer dictionary of the PDF file, to be exact.  It will have a private
attribute set on it that is named 'pages' that is a list containing all
the pages in the file.

When instantiating a PdfReader object, there are options available
for decompressing all the objects in the file.  pdfrw does not currently
have very many options for decompression, so this is not all that useful,
except in the specific case of compressed object streams.

Also, there are no options for decryption yet.  If you have PDF files
that are encrypted or heavily compressed, you may find that using another
program like pdftk on them can make them readable by pdfrw.

In general, the objects are read from the file lazily, but this is not
currently true with compressed object streams -- all of these are decompressed
and read in when the PdfReader is instantiated.


File output
-----------

`pdfwriter.py`__
contains the PdfWriter class, which can create and output a PDF file.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/pdfwriter.py

There are a few options available when creating and using this class.

In the simplest case, an instance of PdfWriter is instantiated, and
then pages are added to it from one or more source files (or created
programmatically), and then the write method is called to dump the
results out to a file.

If you have a source PDF and do not want to disturb the structure
of it too badly, then you may pass its trailer directly to PdfWriter
rather than letting PdfWriter construct one for you.  There is an
example of this (alter.py) in the examples directory.


Advanced features
-----------------

`buildxobj.py`__
contains functions to build Form XObjects out of pages or rectangles on
pages.  These may be reused in new PDFs essentially as if they were images.

buildxobj is careful to cache any page used so that it only appears in
the output once.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/buildxobj.py


`toreportlab.py`__
provides the makerl function, which will translate pdfrw objects into a
format which can be used with `reportlab <http://www.reportlab.org/>`__.
It is normally used in conjunction with buildxobj, to be able to reuse
parts of existing PDFs when using reportlab.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/toreportlab.py


`pagemerge.py`__ builds on the foundation laid by buildxobj.  It
contains classes to create a new page (or overlay an existing page)
using one or more rectangles from other pages.  There are examples
showing its use for watermarking, scaling, 4-up output, splitting
each page in 2, etc.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/pagemerge.py

`findobjs.py`__ contains code that can find specific kinds of objects
inside a PDF file.  The extract.py example uses this module to create
a new PDF that places each image and Form XObject from a source PDF onto
its own page, e.g. for easy reuse with some of the other examples or
with reportlab.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/findobjs.py


Miscellaneous
----------------

`compress.py`__ and `uncompress.py`__
contains compression and decompression functions. Very few filters are
currently supported, so an external tool like pdftk might be good if you
require the ability to decompress (or, for that matter, decrypt) PDF
files.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/compress.py
__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/uncompress.py


`py23_diffs.py`__ contains code to help manage the differences between
Python 2 and Python 3.

__ https://github.com/pmaupin/pdfrw/tree/master/pdfrw/py23_diffs.py

Testing
===============

The tests associated with pdfrw require a large number of PDFs,
which are not distributed with the library.

To run the tests:

* Download or clone the full package from github.com/pmaupin/pdfrw
* cd into the tests directory, and then clone the package
  github.com/pmaupin/static_pdfs into a subdirectory (also named
  static_pdfs).
* Now the tests may be run from tests directory using unittest, or
  py.test, or nose.
* travisci is used at github, and runs the tests with py.test

.. code-block:: bash
    $ pip install pytest
    $ pip install reportlab
    $ pwd
    <...>/pdfrw/tests
    $ git clone https://github.com/pmaupin/static_pdfs
    $ ln -s ../pdfrw
    $ pytest

To run a single test-case:

.. code-block:: bash
    $ pytest test_roundtrip.py -k "test_compress_9f98322c243fe67726d56ccfa8e0885b.pdf"

Other libraries
=====================

Pure Python
-----------

-  `reportlab <http://www.reportlab.org/>`__

    reportlab is must-have software if you want to programmatically
    generate arbitrary PDFs.

-  `pyPdf <https://github.com/mstamy2/PyPDF2>`__

    pyPdf is, in some ways, very full-featured. It can do decompression
    and decryption and seems to know a lot about items inside at least
    some kinds of PDF files. In comparison, pdfrw knows less about
    specific PDF file features (such as metadata), but focuses on trying
    to have a more Pythonic API for mapping the PDF file container
    syntax to Python, and (IMO) has a simpler and better PDF file
    parser.  The Form XObject capability of pdfrw means that, in many
    cases, it does not actually need to decompress objects -- they
    can be left compressed.

-  `pdftools <http://www.boddie.org.uk/david/Projects/Python/pdftools/index.html>`__

    pdftools feels large and I fell asleep trying to figure out how it
    all fit together, but many others have done useful things with it.

-  `pagecatcher <http://www.reportlab.com/docs/pagecatcher-ds.pdf>`__

    My understanding is that pagecatcher would have done exactly what I
    wanted when I built pdfrw. But I was on a zero budget, so I've never
    had the pleasure of experiencing pagecatcher. I do, however, use and
    like `reportlab <http://www.reportlab.org/>`__ (open source, from
    the people who make pagecatcher) so I'm sure pagecatcher is great,
    better documented and much more full-featured than pdfrw.

-  `pdfminer <http://www.unixuser.org/~euske/python/pdfminer/index.html>`__

    This looks like a useful, actively-developed program. It is quite
    large, but then, it is trying to actively comprehend a full PDF
    document. From the website:

    "PDFMiner is a suite of programs that help extracting and analyzing
    text data of PDF documents. Unlike other PDF-related tools, it
    allows to obtain the exact location of texts in a page, as well as
    other extra information such as font information or ruled lines. It
    includes a PDF converter that can transform PDF files into other
    text formats (such as HTML). It has an extensible PDF parser that
    can be used for other purposes instead of text analysis."

non-pure-Python libraries
-------------------------

-  `pyPoppler <https://launchpad.net/poppler-python/>`__ can read PDF
   files.
-  `pycairo <http://www.cairographics.org/pycairo/>`__ can write PDF
   files.
-  `PyMuPDF <https://github.com/rk700/PyMuPDF>`_ high performance rendering
   of PDF, (Open)XPS, CBZ and EPUB

Other tools
-----------

-  `pdftk <https://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/>`__ is a wonderful command
   line tool for basic PDF manipulation. It complements pdfrw extremely
   well, supporting many operations such as decryption and decompression
   that pdfrw cannot do.
-  `MuPDF <http://www.mupdf.com/>`_ is a free top performance PDF, (Open)XPS, CBZ and EPUB rendering library
   that also comes with some command line tools. One of those, ``mutool``, has big overlaps with pdftk's - 
   except it is up to 10 times faster.

Release information
=======================

Revisions:

0.4 -- Released 18 September, 2017

    - Python 3.6 added to test matrix
    - Proper unicode support for text strings in PDFs added
    - buildxobj fixes allow better support creating form XObjects
      out of compressed pages in some cases
    - Compression fixes for Python 3+
    - New subset_booklets.py example
    - Bug with non-compressed indices into compressed object streams fixed
    - Bug with distinguishing compressed object stream first objects fixed
    - Better error reporting added for some invalid PDFs (e.g. when reading
      past the end of file)
    - Better scrubbing of old bookmark information when writing PDFs, to
      remove dangling references
    - Refactoring of pdfwriter, including updating API, to allow future
      enhancements for things like incremental writing
    - Minor tokenizer speedup
    - Some flate decompressor bugs fixed
    - Compression and decompression tests added
    - Tests for new unicode handling added
    - PdfReader.readpages() recursion error (issue #92) fixed.
    - Initial crypt filter support added


0.3 -- Released 19 October, 2016.

    - Python 3.5 added to test matrix
    - Better support under Python 3.x for in-memory PDF file-like objects
    - Some pagemerge and Unicode patches added
    - Changes to logging allow better coexistence with other packages
    - Fix for "from pdfrw import \*"
    - New fancy_watermark.py example shows off capabilities of pagemerge.py
    - metadata.py example renamed to cat.py


0.2 -- Released 21 June, 2015.  Supports Python 2.6, 2.7, 3.3, and 3.4.

    - Several bugs have been fixed
    - New regression test functionally tests core with dozens of
      PDFs, and also tests examples.
    - Core has been ported and tested on Python3 by round-tripping
      several difficult files and observing binary matching results
      across the different Python versions.
    - Still only minimal support for compression and no support
      for encryption or newer PDF features.  (pdftk is useful
      to put PDFs in a form that pdfrw can use.)

0.1 -- Released to PyPI in 2012.  Supports Python 2.5 - 2.7

