# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A token parser for PDF streams.

In general, documentation used was "PDF reference",
sixth edition, for PDF version 1.7, dated November 2006.

'''

import re
from pdfobjects import PdfString, PdfObject

class _PrimitiveTokens(object):

    # Table 3.1, page 50 of reference, defines whitespace
    whitespaceset = set('\x00\t\n\f\r ')


    # Text on page 50 defines delimiter characters
    delimiterset = set('()<>{}[]/%')

    # Coalesce contiguous whitespace into a single token
    whitespace_pattern = '[%s]+' % ''.join(whitespaceset)

    # In addition to the delimiters, we also use '\', which
    # is special in some contexts in PDF.
    delimiter_pattern = '\\\\|' + '|\\'.join(delimiterset)

    # Dictionary delimiters are '<<' and '>>'.  Look for
    # these before the single variety.
    dictdelim_pattern = r'\<\<|\>\>'

    pattern = '(%s|%s|%s)' % (whitespace_pattern,
                    dictdelim_pattern, delimiter_pattern)
    re_func = re.compile(pattern).split
    del whitespace_pattern, dictdelim_pattern
    del delimiter_pattern, pattern

    # Use re to split this many characters at a time.
    # Should not be smaller than a few hundred, to hold
    # the maximum name string.
    chunksize = 2000

    def __init__(self, fdata, startloc, streamlen=None):
        self.startloc = startloc
        self.fdata = fdata
        self.tokens = []
        if streamlen is None:
            self.endloc = 2000000000
        else:
            self.endloc = startloc + streamlen

    def __iter__(self):
        return self

    def readchunk(self):
        fdata, startloc = self.fdata, self.startloc
        endloc = min(startloc + self.chunksize, self.endloc)
        chunk = self.fdata[startloc:endloc]
        tokens = self.tokens = [x for x in self.re_func(chunk) if x]
        startloc += len(chunk)
        self.startloc = startloc - (len(tokens) > 1 and len(tokens.pop()))
        tokens.reverse()
        return tokens

    def next(self):
        tokens = self.tokens
        if not tokens:
            tokens = self.readchunk()
            if not tokens:
                raise StopIteration
        return tokens.pop()

    def peek(self):
        tokens = self.tokens
        if not tokens:
            tokens = self.readchunk()
            if not tokens:
                return '\n'        # Pretend like we have additional whitespace
        return tokens[-1]

    def push(self, what):
        self.tokens.append(what)

    def readuntil(self, stopset):
        while self.peek()[0] not in stopset:
            yield self.tokens.pop()

    @property
    def floc(self):
        return self.startloc - sum(len(x) for x in self.tokens)

class PdfTokens(object):

    whitespaceset = _PrimitiveTokens.whitespaceset
    delimiterset = _PrimitiveTokens.delimiterset
    whiteordelim = whitespaceset | delimiterset

    cached_strings = {}

    def __init__(self, fdata, startloc=0, strip_comments=True, streamlen=None):
        self.primitive = _PrimitiveTokens(fdata, startloc, streamlen)
        self.fdata = fdata
        self.strip_comments = strip_comments

    @property
    def floc(self):
        return self.primitive.floc

    def comment(self, token):
        whitespaceset = self.whitespaceset
        tokens = [token]
        for token in self.primitive:
            tokens.append(token)
            if token[0] in whitespaceset and ('\n' in token or '\r' in token):
                break
        return not self.strip_comments and ''.join(tokens)

    def single(self, token):
        return token

    def regular_string(self, token):
        def escaped():
            escaped = False
            i = -1
            while tokens[i] == '\\':
                escaped = not escaped
                i -= 1
            return escaped

        tokens = [token]
        nestlevel = 1
        for token in self.primitive:
            tokens.append(token)
            if token in '()' and not escaped():
                nestlevel += token == '(' or -1
                if not nestlevel:
                    break
        else:
            assert 0, "Unexpected end of token stream"
        return PdfString(''.join(tokens))

    def hex_string(self, token):
        tokens = [token]
        for token in self.primitive:
            tokens.append(token)
            if token == '>':
                break
        while tokens[-2] == '>>':
            self.primitive.push(tokens.pop(-2))
        return PdfString(''.join(tokens))

    def normal_data(self, dummy, token):
        if token[0] in self.whitespaceset:
            return
        tokens = [token]
        tokens.extend(self.primitive.readuntil(self.whiteordelim))
        return PdfObject(''.join(tokens))

    def name_string(self, token):
        tokens = [token]
        tokens.extend(self.primitive.readuntil(self.whiteordelim))
        token = ''.join(tokens)
        if '#' in token:
            substrs = token.split('#')
            substrs.reverse()
            tokens = [substrs.pop()]
            while substrs():
                s = substrs.pop()
                tokens.append(chr(s[:2]))
                tokens.append(s[2:])
            token = ''.join(tokens)
        return PdfObject(token)

    def broken(self, token):
        assert 0, token

    dispatchers = {
        '(': regular_string,
        ')': broken,
        '<': hex_string,
        '>': broken,
        '[': single,
        ']': single,
        '{': single,
        '}': single,
        '/': name_string,
        '%' : comment,
        '<<': single,
        '>>': single,
    }

    def __iter__(self):
        return self

    def next(self):
        while 1:
            token = self.primitive.next()
            token = self.dispatchers.get(token, self.normal_data)(self, token)
            if token:
                return self.cached_strings.setdefault(token, token)

    def multiple(self, count):
        return [self.next() for i in range(count)]
