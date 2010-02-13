# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A tokenizer for PDF streams.

In general, documentation used was "PDF reference",
sixth edition, for PDF version 1.7, dated November 2006.

'''

from __future__ import generators
from sets import Set as set
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
    delimiter_pattern = '\\\\|\\' + '|\\'.join(delimiterset)

    # Dictionary delimiters are '<<' and '>>'.  Look for
    # these before the single variety.
    dictdelim_pattern = r'\<\<|\>\>'

    pattern = '(%s|%s|%s)' % (whitespace_pattern,
                    dictdelim_pattern, delimiter_pattern)
    re_func = re.compile(pattern).finditer
    del whitespace_pattern, dictdelim_pattern
    del delimiter_pattern, pattern

    def __init__(self, fdata, startloc):
        self.fdata = fdata
        self.startloc = startloc
        self.next_match = self.re_func(fdata, startloc).next
        self.tokens = []

    def __iter__(self):
        return self

    def readchunk(self):
        fdata = self.fdata
        startloc = self.startloc
        tokens = self.tokens = []
        match = self.next_match()
        if match is not None:
            start, end = match.start(), match.end()
            tokens.append(fdata[start:end])
            if start > startloc:
                tokens.append(fdata[startloc:start])
            self.startloc = end
        else:
            s = fdata[startloc:]
            if s:
                tokens.append(s)
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

    def readuntil(self, stopset, result):
        while self.peek()[0] not in stopset:
            result.append(self.tokens.pop())

    def floc(self):
        return self.startloc - sum([len(x) for x in self.tokens])
    floc = property(floc)

class PdfTokens(object):

    whitespaceset = _PrimitiveTokens.whitespaceset
    delimiterset = _PrimitiveTokens.delimiterset
    whiteordelim = whitespaceset | delimiterset

    def __init__(self, fdata, startloc=0, strip_comments=True):
        self.primitive = _PrimitiveTokens(fdata, startloc)
        self.fdata = fdata
        self.strip_comments = strip_comments
        self.tokens = []

    def floc(self):
        return self.primitive.floc
    floc = property(floc)

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
            i = -2
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
            self.tokens.append(tokens.pop(-2))
        return PdfString(''.join(tokens))

    def normal_data(self, dummy, token):
        if token[0] in self.whitespaceset:
            return
        tokens = [token]
        self.primitive.readuntil(self.whiteordelim, tokens)
        return PdfObject(''.join(tokens))

    def name_string(self, token):
        tokens = [token]
        self.primitive.readuntil(self.whiteordelim, tokens)
        token = ''.join(tokens)
        if '#' in token:
            substrs = token.split('#')
            substrs.reverse()
            tokens = [substrs.pop()]
            while substrs:
                s = substrs.pop()
                tokens.append(chr(int(s[:2], 16)))
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
        tokens = self.tokens
        while not tokens:
            token = self.primitive.next()
            token = self.dispatchers.get(token, self.normal_data)(self, token)
            if token:
                return token
        return tokens.pop()

    def multiple(self, count):
        return [self.next() for i in range(count)]
