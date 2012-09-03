Example programs:

subset.py -- This will retrieve a subset of pages from a document.

4up.py -- Prints pages four-up

print_two.py  -- this is used when printing two cut-down copies on a single sheet of paper (double-sided)  Requires uncompressed PDF.

booklet.py -- Converts a PDF into a booklet.

metadata.py -- Concatenates multiple PDFs, adds metadata.

rl1/subset.py -- Same as subset.py, using reportlab for output.  Simplest reportlab example.

rl1/4up.py -- Same as 4up.py, using reportlab for output.  Next simplest reportlab example.

rl1/booklet.py -- Version of print_booklet using reportlab for output.

rl2/copy.py -- example of how you could parse a graphics stream and then use reportlab for output.
               Works on a few different PDFs, probably not a suitable starting point for real
               production work without a lot of work on the library functions.
