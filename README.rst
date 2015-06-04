pdfrw reads and writes PDF files.

Revisions:

0.2 -- In development.  Will support Python 2.6, 2.7, 3.3, and 3.4.

    - Several bugs have been fixed
    - Work has started on regression test infrastructure
    - Core has been ported and tested on Python3 by round-tripping
      several difficult files and observing binary matching results
      across the different Python versions.
    - Buildxobj and utilities have not yet been ported tested.
    - Still only minimal support for compression and no support
      for encryption or newer PDF features.  (pdftk is useful
      to put PDFs in a form that pdfrw can use.)

0.1 -- Released to PyPI.  Supports Python 2.5 - 2.7


Please see the wiki__ for usage information

__ https://github.com/pmaupin/pdfrw/wiki
