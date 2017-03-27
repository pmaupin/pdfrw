# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
#                    2016 James Laird-Wah, Sydney, Australia
# MIT license -- See LICENSE.txt for details

"""

================================
PdfString encoding and decoding
================================

Introduction
=============


This module handles encoding and decoding of PDF strings.  PDF strings
are described in the PDF 1.7 reference manual, mostly in chapter 3
(sections 3.2 and 3.8) and chapter 5.

PDF strings are used in the document structure itself, and also inside
the stream of page contents dictionaries.

A PDF string can represent pure binary data (e.g. for a font or an
image), or text, or glyph indices.  For Western fonts, the glyph indices
usually correspond to ASCII, but that is not guaranteed.  (When it does
happen, it makes examination of raw PDF data a lot easier.)

The specification defines PDF string encoding at two different levels.
At the bottom, it defines ways to encode arbitrary bytes so that a PDF
tokenizer can understand they are a string of some sort, and can figure
out where the string begins and ends.  (That is all the tokenizer itself
cares about.)  Above that level, if the string represents text, the
specification defines ways to encode Unicode text into raw bytes, before
the byte encoding is performed.

There are two ways to do the byte encoding, and two ways to do the text
(Unicode) encoding.

Encoding bytes into PDF strings
================================

Adobe calls the two ways to encode bytes into strings "Literal strings"
and "Hexadecimal strings."

Literal strings
------------------

A literal string is delimited by ASCII parentheses ("(" and ")"), and a
hexadecimal string is delimited by ASCII less-than and greater-than
signs ("<" and ">").

A literal string may encode bytes almost unmolested.  The caveat is
that if a byte has the same value as a parenthesis, it must be escaped
so that the tokenizer knows the string is not finished.  This is accomplished
by using the ASCII backslash ("\") as an escape character.  Of course,
now any backslash appearing in the data must likewise be escaped.

Hexadecimal strings
---------------------

A hexadecimal string requires twice as much space as the source data
it represents (plus two bytes for the delimiter), simply storing each
byte as two hexadecimal digits, most significant digit first.  The spec
allows for lower or upper case hex digits, but most PDF encoders seem
to use upper case.

Special cases -- Legacy systems and readability
-----------------------------------------------

It is possible to create a PDF document that uses 7 bit ASCII encoding,
and it is desirable in many cases to create PDFs that are reasonably
readable when opened in a text editor.  For these reasons, the syntax
for both literal strings and hexadecimal strings is slightly more
complicated that the initial description above.  In general, the additional
syntax allows the following features:

  - Making the delineation between characters, or between sections of
    a string, apparent, and easy to see in an editor.
  - Keeping output lines from getting too wide for some editors
  - Keeping output lines from being so narrow that you can only see the
    small fraction of a string at a time in an editor.
  - Suppressing unprintable characters
  - Restricting the output string to 7 bit ASCII

Hexadecimal readability
~~~~~~~~~~~~~~~~~~~~~~~

For hexadecimal strings, only the first two bullets are relevant.  The syntax
to accomplish this is simple, allowing any ASCII whitespace to be inserted
anywhere in the encoded hex string.

Literal readability
~~~~~~~~~~~~~~~~~~~

For literal strings, all of the bullets except the first are relevant.
The syntax has two methods to help with these goals.  The first method
is to overload the escape operator to be able to do different functions,
and the second method can reduce the number of escapes required for
parentheses in the normal case.

The escape function works differently, depending on what byte follows
the backslash.  In all cases, the escaping backslash is discarded,
and then the next character is examined:

  - For parentheses and backslashes (and, in fact, for all characters
    not described otherwise in this list), the character after the
    backslash is preserved in the output.
  - A letter from the set of "nrtbf" following a backslash is interpreted
    as a line feed, carriage return, tab, backspace, or form-feed, respectively.
  - One to three octal digits following the backslash indicate the
    numeric value of the encoded byte.
  - A carriage return, carriage return/line feed, or line feed following
    the backslash indicates a line break that was put in for readability,
    and that is not part of the actual data, so this is discarded.

The second method that can be used to improve readability (and reduce space)
in literal strings is to not escape parentheses.  This only works, and is
only allowed, when the parentheses are properly balanced.  For example,
"((Hello))" is a valid encoding for a literal string, but "((Hello)" is not;
the latter case should be encoded "(\(Hello)"

Encoding text into strings
==========================

Section 3.8.1 of the PDF specification describes text strings.

The individual characters of a text string can all be considered to
be Unicode; Adobe specifies two different ways to encode these characters
into a string of bytes before further encoding the byte string as a
literal string or a hexadecimal string.

The first way to encode these strings is called PDFDocEncoding.  This
is mostly a one-for-one mapping of bytes into single bytes, similar to
Latin-1.  The representable character set is limited to the number of
characters that can fit in a byte, and this encoding cannot be used
with Unicode strings that start with the two characters making up the
UTF-16-BE BOM.

The second way to encode these strings is with UTF-16-BE.  Text strings
encoded with this method must start with the BOM, and although the spec
does not appear to mandate that the resultant bytes be encoded into a
hexadecimal string, that seems to be the canonical way to do it.


PDF string handling in pdfrw
=============================

Responsibility for handling PDF strings in the pdfrw library is shared
between this module, the tokenizer, and the pdfwriter.

tokenizer string handling
--------------------------

As far as the tokenizer and its clients such as the pdfreader are concerned,
the PdfString class must simply be something that it can instantiate by
passing a string, that doesn't compare equal (or throw an exception when
compared) to other possible token strings.  The tokenizer must understand
enough about the syntax of the string to successfully find its beginning
and end in a stream of tokens, but doesn't otherwise know or care about
the data represented by the string.

pdfwriter string handling
--------------------------

The pdfwriter knows and cares about two attributes of PdfString instances:

  - First, PdfString objects have an 'indirect' attribute, which pdfwriter
    uses as an indication that the object knows how to represent itself
    correctly when output to a new PDF.  (In the case of a PdfString object,
    no work is really required, because it is already a string.)
  - Second, the PdfString.encode() method is used as a convenience to
    automatically convert any user-supplied strings (that didn't come
    from PDFs) when a PDF is written out to a file.

pdfstring handling
-------------------

The code in this module is designed to support those uses by the
tokenizer and the pdfwriter, and to additionally support encoding
and decoding of PdfString objects as a convenience for the user.

Most users of the pdfrw library never encode or decode a PdfString,
so it is imperative that (a) merely importing this module does not
take a significant amount of CPU time; and (b) it is cheap for the
tokenizer to produce a PdfString, and cheap for the pdfwriter to
consume a PdfString -- if the tokenizer finds a string that conforms
to the PDF specification, it will be wrapped in a PdfString object,
and if the pdfwriter finds an object with an indirect attribute, it
simply calls str() to ask it to format itself.

Encoding and decoding are not actually performed very often at all,
compared to how often tokenization and then subsequent concatenation
by the pdfwriter are performed.  In fact, versions of pdfrw prior to
0.4 did not even support Unicode for this function.  Encoding and
decoding can also easily be performed by the user, outside of the
library, and this might still be recommended, at least for encoding,
if the visual appeal of encodings generated by this module is found
lacking.


PdfString.decode()
~~~~~~~~~~~~~~~~~~~

Decoding strings can be tricky, but is a bounded process.  Each
properly-encoded encoded string represents exactly one output string,
with the caveat that is up to the caller of the function to know whether
he expects a Unicode string, or just bytes.

The decode function defaults to producing a Unicode string, but will
produce bytes if the to_bytestring parameter is set True.  Unicode
strings will be regular strings in Python 3, and u'' unicode strings
in Python 2.  Byte strings will be regular strings in Python 2, and
b'' bytes in Python 3.

PdfString.encode()
~~~~~~~~~~~~~~~~~~

The encoder takes the string to be encoded, and first examines the type
of the string (see decode section above) to determine if it is Unicode
or just bytes.  If it is Unicode, it is first encoded into bytes, and in
either case, the bytes are then encoded into a hexadecimal string or a
literal string.

Unlike decoding(), encoding is not (mathematically) a function.
There are (literally) an infinite number of ways to encode any given
source string.  (Of course, most of them would be stupid, unless
the intent is some sort of denial-of-service attack.)

So encoding strings is either simpler than decoding, or can be made to
be an open-ended science fair project (to create the best looking
encoded strings).

There are parameters to encode() that allow control over the final
encoded string, but the intention is to make the default values produce
a reasonable encoding.

As mentioned previously, if encode() does not do what a particular
user needs, that user is free to write his own encoder, and then
simply instantiate a PdfString object by passing a string to the
default constructor, the same way that the tokenizer does it.

However, if desirable, encode() may gradually become more capable
over time, adding the ability to generate more aesthetically pleasing
encoded strings.

PDFDocString encoding and decoding
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To handle this encoding in a fairly standard way, this module registers
an encoder and decoder for PDFDocEncoding with the codecs module.

"""

import re
import codecs
import binascii
import itertools
from ..py23_diffs import convert_load, convert_store

def find_pdfdocencoding(encoding):
    """ This function conforms to the codec module registration
        protocol.  It defers calculating data structures until
        a pdfdocencoding encode or decode is required.

        PDFDocEncoding is described in the PDF 1.7 reference manual.
    """

    if encoding != 'pdfdocencoding':
        return

    # Create the decoding map based on the table in section D.2 of the
    # PDF 1.7 manual

    # Start off with the characters with 1:1 correspondence
    decoding_map = set(range(0x20, 0x7F)) | set(range(0xA1, 0x100))
    decoding_map.update((0x09, 0x0A, 0x0D))
    decoding_map.remove(0xAD)
    decoding_map = dict((x, x) for x in decoding_map)

    # Add in the special Unicode characters
    decoding_map.update(zip(range(0x18, 0x20), (
            0x02D8, 0x02C7, 0x02C6, 0x02D9, 0x02DD, 0x02DB, 0x02DA, 0x02DC)))
    decoding_map.update(zip(range(0x80, 0x9F), (
            0x2022, 0x2020, 0x2021, 0x2026, 0x2014, 0x2013, 0x0192, 0x2044,
            0x2039, 0x203A, 0x2212, 0x2030, 0x201E, 0x201C, 0x201D, 0x2018,
            0x2019, 0x201A, 0x2122, 0xFB01, 0xFB02, 0x0141, 0x0152, 0x0160,
            0x0178, 0x017D, 0x0131, 0x0142, 0x0153, 0x0161, 0x017E)))
    decoding_map[0xA0] = 0x20AC

    # Make the encoding map from the decoding map
    encoding_map = codecs.make_encoding_map(decoding_map)

    # Not every PDF producer follows the spec, so conform to Postel's law
    # and interpret encoded strings if at all possible.  In particular, they
    # might have nulls and form-feeds, judging by random code snippets floating
    # around the internet.
    decoding_map.update(((x, x) for x in range(0x18)))

    def encode(input, errors='strict'):
        return codecs.charmap_encode(input, errors, encoding_map)

    def decode(input, errors='strict'):
        return codecs.charmap_decode(input, errors, decoding_map)

    return codecs.CodecInfo(encode, decode, name='pdfdocencoding')

codecs.register(find_pdfdocencoding)

class PdfString(str):
    """ A PdfString is an encoded string.  It has a decode
        method to get the actual string data out, and there
        is an encode class method to create such a string.
        Like any PDF object, it could be indirect, but it
        defaults to being a direct object.
    """
    indirect = False


    # Used by decode_literal; filled in on first use

    unescape_dict = None
    unescape_func = None

    @classmethod
    def init_unescapes(cls):
        """ Sets up the unescape attributes for decode_literal
        """
        unescape_pattern = r'\\([0-7]{1,3}|\r\n|.)'
        unescape_func = re.compile(unescape_pattern, re.DOTALL).split
        cls.unescape_func = unescape_func

        unescape_dict = dict(((chr(x), chr(x)) for x in range(0x100)))
        unescape_dict.update(zip('nrtbf', '\n\r\t\b\f'))
        unescape_dict['\r'] = ''
        unescape_dict['\n'] = ''
        unescape_dict['\r\n'] = ''
        for i in range(0o10):
            unescape_dict['%01o' % i] = chr(i)
        for i in range(0o100):
            unescape_dict['%02o' % i] = chr(i)
        for i in range(0o400):
            unescape_dict['%03o' % i] = chr(i)
        cls.unescape_dict = unescape_dict
        return unescape_func

    def decode_literal(self):
        """ Decode a PDF literal string, which is enclosed in parentheses ()

            Many pdfrw users never decode strings, so defer creating
            data structures to do so until the first string is decoded.

            Possible string escapes from the spec:
            (PDF 1.7 Reference, section 3.2.3, page 53)

                1. \[nrtbf\()]: simple escapes
                2. \\d{1,3}: octal. Must be zero-padded to 3 digits
                    if followed by digit
                3. \<end of line>: line continuation. We don't know the EOL
                    marker used in the PDF, so accept \r, \n, and \r\n.
                4. Any other character following \ escape -- the backslash
                    is swallowed.
        """
        result = (self.unescape_func or self.init_unescapes())(self[1:-1])
        if len(result) == 1:
            return convert_store(result[0])
        unescape_dict = self.unescape_dict
        result[1::2] = [unescape_dict[x] for x in result[1::2]]
        return convert_store(''.join(result))


    def decode_hex(self):
        """ Decode a PDF hexadecimal-encoded string, which is enclosed
            in angle brackets <>.
        """
        hexstr = convert_store(''.join(self[1:-1].split()))
        if len(hexstr) % 1: # odd number of chars indicates a truncated 0
            hexstr += '0'
        return binascii.unhexlify(hexstr)


    def decode(self, to_bytestring=False):
        """ Decode a PDF string.  This is a convenience function
            for user code, in that (as of pdfrw 0.3) it is never
            actually used inside pdfrw.

            A PDF string might represent Unicode code points, or
            it might just be a collection of raw bytes.  That
            distinction is context-dependent, so it is up to the
            caller of this function to set to_bytestring to True
            if it does not want a Unicode string result.

            There are two Unicode storage methods used -- either
            UTF16_BE, or something called PDFDocEncoding, which
            is defined in the PDF spec.  The determination of
            which decoding method to use is done by examining the
            first two bytes for the byte order marker.
        """
        if self.startswith('(') and self.endswith(')'):
            raw = self.decode_literal()

        elif self.startswith('<') and self.endswith('>'):
            raw = self.decode_hex()

        else:
            raise ValueError('Invalid PDF string "%s"' % repr(self))

        if to_bytestring:
            return raw
        elif raw[:2] == codecs.BOM_UTF16_BE:
            return raw[2:].decode('utf-16-be')
        else:
            return raw.decode('pdfdocencoding')

    # These constants are used for the mode parameter to encode()

    ENCODE_PDFDOC = 1   # Use PDFDocEncoding to encode Unicode
    ENCODE_UTF16 = 2    # Use UTF-16BE to encode Unicode
    ENCODE_LITERAL = 4  # Use () literal strings for byte encoding
    ENCODE_HEX = 8      # Use <> hex strings for byte encoding

    # Internal values used by encode

    bytes_bom = codecs.BOM_UTF16_BE
    uni_bom = codecs.BOM_UTF16_BE.decode('latin-1')
    uni_type = type(uni_bom)
    escape_splitter = None  # Calculated on first use

    @classmethod
    def init_escapes(cls):
        """ Initialize the escape_splitter for the encode method
        """
        cls.escape_splitter = re.compile(br'(\(|\\|\))').split
        return cls.escape_splitter

    @classmethod
    def encode(cls, source, mode=0):
        """ The encode() constructor is called to encode a source string
            or raw bytes into a PdfString that is suitable for inclusion
            in a PDF.

            If encode() is passed bytes (bytes type on Python3, regular
            string on Python2), then it will skip the encoding stage
            from Unicode to bytes.  If it is passed a Unicode string,
            then it will do that encoding first.

            NOTE 1:  There is no magic in the encoding process.  A user
            can certainly do his own encoding, and simply initialize a
            PdfString() instance with his encoded string.  That may be
            useful, for example, to add line breaks to make it easier
            to load PDFs into editors, or to not bother to escape balanced
            parentheses, or to escape additional characters to make a PDF
            more readable in a file editor.  Those are features not
            supported by this method.

            encode() can use a heuristic to figure out the best
            encoding for the string, or the user can control the process
            by setting bits in the mode parameter:

                bit 0 -- force Unicode conversion using PDFDocEncoding
                bit 1 -- force Unicode conversion using UTF-16BE
                bit 2 -- force byte encoding using literal strings
                bit 3 -- force byte encoding using hexadecimal strings

            NOTE 2:  All other mode bits should be set to 0 for possible
            future capability expansion.

            The function does not guarantee results if the user stupidly
            sets conflicting mode bits, but it does guarantee that it
            will follow the instructions or raise an exception if it
            cannot, if the user has not created a conflict.
        """
        raw = source
        if isinstance(source, cls.uni_type):
            # Give preference to pdfdocencoding, since it only
            # requires one raw byte per character, rather than two.
            if not (mode & cls.ENCODE_UTF16) and not source.startswith(cls.uni_bom):
                try:
                    raw = source.encode('pdfdocencoding')
                except ValueError:
                    if (mode & cls.ENCODE_PDFDOC):
                        raise
            if raw is source:
                raw = cls.bytes_bom + source.encode('utf-16-be')
                # If the user is not forcing literal strings,
                # it makes much more sense to use hexadecimal with 2-byte chars
                if not (mode & cls.ENCODE_LITERAL):
                    mode |= cls.ENCODE_HEX

        # If hexadecimal is not being forced, then figure out how long
        # the escaped literal string will be, and fall back to hex if
        # it is too long.
        if not (mode & cls.ENCODE_HEX):
            splitlist = (cls.escape_splitter or cls.init_escapes())(raw)
            if (not (mode & cls.ENCODE_LITERAL) and
                len(splitlist) // 2 >= len(raw)):
                mode |= cls.ENCODE_HEX

        if mode & cls.ENCODE_HEX:
            # The spec does not mandate uppercase, but it seems to be the convention.
            fmt = '<%s>'
            result = binascii.hexlify(raw).upper()
        else:
            fmt = '(%s)'
            splitlist[1::2] = [(b'\\' + x) for x in splitlist[1::2]]
            result = b''.join(splitlist)

        return cls(fmt % convert_load(result))
