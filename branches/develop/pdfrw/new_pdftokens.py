# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2012 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A tokenizer for PDF streams.

In general, documentation used was "PDF reference",
sixth edition, for PDF version 1.7, dated November 2006.

'''

from __future__ import generators

import re
import itertools
from pdfobjects import PdfString, PdfObject
from pdflog import log

def countlines(fdata, loc):
    line = fdata.count('\n', 0, loc) + 1
    line += fdata.count('\r', 0, loc) - fdata.count('\r\n', 0, loc)
    return line

class PdfTokens(object):

    # Table 3.1, page 50 of reference, defines whitespace
    eol = '\n\r'
    whitespace = '\x00 \t\f' + eol

    # Text on page 50 defines delimiter characters
    # Escape the ]
    delimiters = r'()<>{}[\]/%'

    # "normal" stuff is all but delimiters or whitespace.

    p_normal = r'(?:[^\\%s%s]+|\\[^%s])+' % (whitespace, delimiters, whitespace)

    p_comment = r'\%%[^%s]*' % eol

    # This will get the bulk of literal strings.
    p_literal_string = r'\((?:[^\\()]+|\\.)*[()]?'

    # This will get more pieces of literal strings
    # (Don't ask me why, but it hangs without the trailing ?.)
    p_literal_string_extend = r'(?:[^\\()]+|\\.)*[()]?'

    # A hex string.  This one's easy.
    p_hex_string = r'\<[%s0-9A-Fa-f]*\>' % whitespace

    p_dictdelim = r'\<\<|\>\>'
    p_name = r'/[^%s%s]*' % (delimiters, whitespace)

    p_catchall = '[^%s]' % whitespace

    pattern = '|'.join([p_normal, p_name, p_hex_string, p_dictdelim, p_literal_string, p_comment, p_catchall])
    findtok = re.compile('(%s)[%s]*' % (pattern, whitespace), re.DOTALL).finditer
    findparen = re.compile('(%s)[%s]*' % (p_literal_string_extend, whitespace), re.DOTALL).finditer
    splitname = re.compile(r'\#([0-9A-Fa-f]{2})').split

    def _cacheobj(cache, obj, constructor):
        ''' This caching relies on the constructors
            returning something that will compare as
            equal to the original obj.  This works
            fine with our PDF objects.
        '''
        result = cache.get(obj)
        if result is None:
            result = constructor(obj)
            cache[result] = result
        return result

    def _fixname(cache, token, constructor, splitname=splitname, join=''.join, cacheobj=_cacheobj):
        ''' Inside name tokens, a '#' character indicates that
            the next two bytes are hex characters to be used
            to form the 'real' character.
        '''
        substrs = splitname(token)
        if '#' in join(substrs[::2]):
            log.warning('Invalid name token: %s' % repr(token))
            return token
        substrs[1::2] = (int(x, 16) for x in substrs[1::2])
        result = cacheobj(cache, join(substrs), constructor)
        result.encoded = token
        return result

    def _gettoks(self, startloc, fixname=_fixname, cacheobj=_cacheobj,
                       delimiters=delimiters, findtok=findtok, findparen=findparen,
                       PdfString=PdfString, PdfObject=PdfObject):
        ''' Given a source data string and a location inside it,
            gettoks generates tokens.  Each token is a tuple of the form:
             <starting file loc>, <ending file loc>, <token string>
            The ending file loc is past any trailing whitespace.

            The main complication here is the literal strings, which
            can contain nested parentheses.  In order to cope with these
            we can discard the current iterator and loop back to the
            top to get a fresh one.

            We could use re.search instead of re.finditer, but that's slower.
        '''
        fdata = self.fdata
        current = self.current = [(startloc, startloc)]
        cache = {}
        while 1:
            for match in findtok(fdata, current[0][1]):
                current[0] = tokspan = match.span()
                token = match.group(1)
                firstch = token[0]
                if firstch not in delimiters:
                    token = cacheobj(cache, token, PdfObject)
                elif firstch in '/<(%':
                    if firstch == '/':
                        # PDF Name
                        token = (cacheobj, fixname)['#' in token](cache, token, PdfObject)
                    elif firstch == '<':
                        # << dict delim, or < hex string >
                        if token[1:2] != '<':
                            token = cacheobj(cache, token, PdfString)
                    elif firstch == '(':
                        # Literal string
                        # It's probably simple, but maybe not
                        # Nested parentheses are a bear, and if
                        # they are present, we exit the for loop
                        # and get back in with a new starting location.
                        if fdata[match.end(1)-1] != ')':
                            nest = 2
                            m_start, loc = tokspan
                            for match in findparen(fdata, loc):
                                loc = match.end(1)
                                nest += 1 - (fdata[loc-1] == ')') * 2
                                if not nest:
                                    break
                            else:
                                log.error('Unterminated literal string on line %d' %
                                    countlines(fdata, m_start))
                            token = fdata[m_start:loc]
                            current[0] = m_start, match.end()
                        token = cacheobj(cache, token, PdfString)
                    elif firstch == '%':
                        # Comment
                        if self.strip_comments:
                            continue
                    else:
                        assert 0  # Should never get here

                yield token
                if current[0] is not tokspan:
                    break
            else:
                raise StopIteration

    def __init__(self, fdata, startloc=0, strip_comments=True):
        self.fdata = fdata
        self.strip_comments = strip_comments
        self.iterator = iterator = self._gettoks(startloc)
        self.next = iterator.next

    def setstart(self, startloc):
        ''' Change the starting location.
        '''
        current = self.current
        if startloc != current[0][1]:
            current[0] = startloc, startloc

    def floc(self):
        ''' Return the current file position
            (where the next token will be retrieved)
        '''
        return self.current[0][1]
    floc = property(floc, setstart)

    def __iter__(self):
        return self.iterator

    def multiple(self, count, islice=itertools.islice, list=list):
        ''' Retrieve multiple tokens
        '''
        return list(islice(self, count))
