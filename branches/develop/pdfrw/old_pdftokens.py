# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A tokenizer for PDF streams.

In general, documentation used was "PDF reference",
sixth edition, for PDF version 1.7, dated November 2006.

'''

from __future__ import generators

try:
    set
except NameError:
    from sets import Set as set

import re
import pdferrors
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

    pattern = '|'.join([whitespace_pattern,
                        dictdelim_pattern, delimiter_pattern])
    re_func = re.compile(pattern).finditer
    del whitespace_pattern, dictdelim_pattern
    del delimiter_pattern, pattern

    def __init__(self, fdata):

        class MyIterator(object):
            def next():
                if not tokens:
                    startloc = next_startloc[0]
                    for match in next_match[0]:
                        start = match.start()
                        end = match.end()
                        tappend(fdata[start:end])
                        if start > startloc:
                            tappend(fdata[startloc:start])
                        next_startloc[0] = end
                        break
                    else:
                        s = fdata[startloc:]
                        next_startloc[0] = len(fdata)
                        if s:
                            tappend(s)
                    if not tokens:
                        raise StopIteration
                return tpop()
            next = staticmethod(next)

        def coalesce(result):
            ''' This function coalesces tokens together up until
                the next delimiter or whitespace.
                All of the coalesced tokens will either be non-matches,
                or will be a matched backslash.  We distinguish the
                non-matches by the fact that next() will have left
                a following match inside self.tokens for the actual match.
            '''
            # Optimized path for usual case -- regular data (not a name string),
            # with no escape character, and followed by whitespace.

            if tokens:
                token = tpop()
                if token != '\\':
                    if token[0] not in whitespace:
                        tappend(token)
                    return
                result.append(token)

            # Non-optimized path.  Either start of a name string received,
            # or we just had one escape.

            rappend = result.append
            for token in self:
                if tokens:
                    rappend(token)
                    token = tpop()
                if token != '\\':
                    if token[0] not in whitespace:
                        tappend(token)
                    return
                rappend(token)

        def setstart(startloc):
            while tokens:
                tpop()
            old_loc = next_startloc[0]
            if old_loc != startloc:
                next_startloc[0] = startloc
                next_match[0] = re_func(fdata, startloc)

        self.fdata = fdata
        self.tokens = tokens = []
        self.iterator = iterator = MyIterator()
        self.next = iterator.next
        self.next_match = next_match = [None]
        self.startloc = next_startloc = [0]
        self.coalesce = coalesce
        self.setstart = setstart
        tappend = tokens.append
        tpop = tokens.pop
        re_func = self.re_func
        whitespace = self.whitespaceset

    def __iter__(self):
        return self.iterator

    def floc(self):
        return self.startloc[0] - sum([len(x) for x in self.tokens])

class PdfTokens(object):

    def __init__(self, fdata, startloc=0, strip_comments=True):

        def comment(token):
            tokens = [token]
            for token in primitive:
                tokens.append(token)
                if token[0] in whitespaceset and ('\n' in token or '\r' in token):
                    break
            return not self.strip_comments and join(tokens)

        def single(token):
            return token

        def regular_string(token):
            def escaped():
                escaped = False
                i = -2
                while tokens[i] == '\\':
                    escaped = not escaped
                    i -= 1
                return escaped

            tokens = [token]
            nestlevel = 1
            for token in primitive:
                tokens.append(token)
                if token in '()' and not escaped():
                    nestlevel += token == '(' or -1
                    if not nestlevel:
                        break
            else:
                raise pdferrors.PdfUnexpectedEOFError(self.fdata)
            return PdfString(join(tokens))

        def hex_string(token):
            tokens = [token]
            for token in primitive:
                tokens.append(token)
                if token == '>':
                    break
            while tokens[-2] == '>>':
                primitive.tokens.append(tokens.pop(-2))
            return PdfString(join(tokens))

        def normal_data(token):

            # Obscure optimization -- we can get here with
            # whitespace or regular character data.  If we get
            # here with whitespace, then there won't be an additional
            # token queued up in the primitive object, otherwise there
            # will...
            if primitive_tokens:     #if token[0] not in whitespaceset:
                tokens = [token]
                coalesce(tokens)
                return PdfObj(join(tokens))

        def name_string(token):
            tokens = [token]
            coalesce(tokens)
            token = join(tokens)
            if '#' not in token:
                return PdfObj(token)
            substrs = token.split('#')
            substrs.reverse()
            tokens = [substrs.pop()]
            while substrs:
                s = substrs.pop()
                try:
                    tokens.append(chr(int(s[:2], 16)))
                except ValueError:
                    raise pdferrors.PdfInvalidCharacterError(self.fdata, self.floc, s[:2])
                tokens.append(s[2:])
            result = PdfObj(join(tokens))
            result.encoded = token
            return result

        def broken(token):
            raise pdferrors.PdfUnexpectedTokenError(self.fdata, self.floc, token)

        dispatch = {
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
        }.get

        class MyIterator(object):
            def next():
                while not tokens:
                    token = primitive_next()
                    token = dispatch(token, normal_data)(token)
                    if token:
                        return token
                return tokens.pop()
            next = staticmethod(next)

        self.primitive = primitive = _PrimitiveTokens(fdata)
        self.setstart = primitive.setstart
        primitive.setstart(startloc)
        self.fdata = fdata
        self.strip_comments = strip_comments
        self.tokens = tokens = []
        self.iterator = iterator = MyIterator()
        self.next = iterator.next
        primitive_next = primitive.next
        primitive_tokens = primitive.tokens
        whitespaceset = primitive.whitespaceset
        coalesce = primitive.coalesce
        PdfObj = PdfObject
        join = ''.join

    def set_floc(self, startloc):
        self.setstart(startloc)

    def floc(self):
        return self.primitive.floc() - sum([len(x) for x in self.tokens])
    floc = property(floc, set_floc)

    def __iter__(self):
        return self.iterator

    def multiple(self, count):
        next = self.next
        return [next() for i in range(count)]
