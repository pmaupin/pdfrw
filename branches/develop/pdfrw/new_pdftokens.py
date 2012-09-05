# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A tokenizer for PDF streams.

In general, documentation used was "PDF reference",
sixth edition, for PDF version 1.7, dated November 2006.

'''

from __future__ import generators
import bisect
import itertools

try:
    set
except NameError:
    from sets import Set as set

import re
import pdferrors
from pdfobjects import PdfString, PdfObject

class TokenGroup(object):

    # Table 3.1, page 50 of reference, defines whitespace
    eol = '\n\r'
    whitespace = '\x00 \t\f' + eol

    # Text on page 50 defines delimiter characters
    # Escape the ]
    delimiters = r'()<>{}[\]/%'

    # ORDER MATTERS!!!
    special = (eol, delimiters, whitespace)

    # "normal" stuff is all but delimiters.  Also, we include
    # escaped delimiters, but we don't include escaped whitespace,
    # since we will later do a regular string split, and that wouldn't
    # know about the escape.  Finally, we either do full lines,
    # or stop at the end of the line, because of the ambiguity
    # between comments and nested parentheses in literal strings.
    # If we're not doing a full line, we might do the comment
    # or string at the start, too.
    p_normal_single = r'(?:[(%%]?[^\\%s%s]+|\\[^%s])+' % special
    p_normal_multiple = r'[%s](?:[^\\%s]+|\\[^%s])*' % special

    # A hex string.  This one's easy.
    p_hex_string = r'\<[%s0-9A-Fa-f]*\>' % whitespace

    p_dictdelim = r'\<\<|\>\>'
    p_name = r'/[^%s%s]*' % (delimiters, whitespace)

    pattern = '|'.join([p_name, p_hex_string, p_normal_single, p_normal_multiple, p_dictdelim, '.'])
    findall = re.compile(pattern).findall

    ending_pattern = r'[%s]+\>\>[%s]*stream[%s]+' % (whitespace, whitespace, eol)
    search = re.compile(ending_pattern).search

    # For splitting out simple tokens from whitespace
    split = re.compile('([^%s]+)' % whitespace).split

    def getraw(s, start, search=search, findall=findall):
        end = search(s, start)
        if end is None:
            end = ()
        else:
            end = end.end(),
        result = findall(s, start, *end)
        result.reverse()
        return result

    @staticmethod
    def gettoks(source, start, strip_comments, getraw=getraw,
                       split=split, delimiters=delimiters, eol = eol,
                       PdfString=PdfString, PdfObject=PdfObject, len=len, join=''.join):
        raw = getraw(source,start)
        pop = raw.pop
        loc = start
        while raw:
            token = pop()
            firstch = token[0]
            if firstch not in delimiters:
                toklist = split(token)
                toklist.reverse()
                lpop = toklist.pop
                loc += len(lpop())
                while toklist:
                    token = lpop()
                    loc += len(token)
                    yield loc, PdfObject(token)
                    loc += len(lpop())
                continue

            if firstch == '/':
                if '#' not in token:
                    token = PdfObject(token)
                else:
                    substrs = token.split('#')
                    substrs.reverse()
                    tokens = [substrs.pop()]
                    while substrs:
                        s = substrs.pop()
                        tokens.append(chr(int(s[:2], 16)))
                        try:
                            tokens.append(chr(int(s[:2], 16)))
                        except ValueError:
                            raise pdferrors.PdfInvalidCharacterError(source, loc, s[:2])
                        tokens.append(s[2:])
                    result = PdfObject(join(tokens))
                    result.encoded = token
                    token = result
            elif firstch == '<':
                token = PdfString(token)
            elif firstch == '(':
                toklist = [token]
                lappend = toklist.append
                nest = 1
                while 1:
                    while nest and raw:
                        token = pop()
                        lappend(token)
                        firstch = token[0]
                        nest += (firstch == '(') - (firstch == ')')
                    if not nest:
                        break
                    if not raw:
                        raw = getraw(source,start)
                        pop = raw.pop
                        if not raw:
                            # Error here, maybe???
                            break
                token = PdfString(join(toklist))
            elif firstch == '%':
                toklist = [token]
                while raw[-1] not in eol:
                    toklist.append(pop())
                token = join(toklist)
                if strip_comments:
                    loc += len(token)
                    continue

            loc += len(token)
            yield loc, token

class PdfTokens(object):

    def __init__(self, fdata, startloc=0, strip_comments=True):
        self.fdata = fdata
        self.strip_comments = strip_comments
        self.tokens = []
        self.current = [(None, None)]
        self.setstart(startloc)

    def setstart(self, startloc, gettoks=TokenGroup.gettoks, bisect=bisect.bisect_left, len=len, islice=itertools.islice):
        current = self.current
        tokens = self.tokens

        ok = tokens and tokens[0][0] - len(tokens[0][1]) <= startloc < tokens[-1][0]
        if not ok:
            tokens[:] = gettoks(self.fdata, startloc, self.strip_comments)


        def iterator():
            start = bisect(tokens, (startloc+1,))
            itokens = start > 0 and islice(tokens, start, None) or tokens
            while 1:
                for token in itokens:
                    current[0] = token
                    yield token[1]
                tokens[:] = gettoks(self.fdata, current[0][0], self.strip_comments)
                if not tokens:
                    raise StopIteration
                itokens = tokens
        iterator = iterator()
        self.iterator = iterator
        self.next = iterator.next

    def floc(self):
        return self.current[0][0]
    floc = property(floc)

    def __iter__(self):
        return self.iterator

    def multiple(self, count, islice=itertools.islice, list=list):
        return list(islice(self, count))
