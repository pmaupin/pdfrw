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

    def _fixname(token, PdfObject=PdfObject, join=''.join):
        ''' Inside name tokens, a '#' character indicates that
            the next two bytes are hex characters to be used
            to form the 'real' character.
        '''
        substrs = token.split('#')
        substrs.reverse()
        tokens = [substrs.pop()]
        while substrs:
            s = substrs.pop()
            tokens.append(chr(int(s[:2], 16)))
            tokens.append(s[2:])
        result = PdfObject(join(tokens))
        result.encoded = token
        return result

    def _gettoks(self, startloc, fixname=_fixname,
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
        current = self.current = [startloc]
        prev = self.prev = [startloc]
        while 1:
            for match in findtok(fdata, current[0]):
                m_start, loc = match.span()
                token = match.group(1)
                firstch = token[0]
                if firstch not in delimiters:
                    token = PdfObject(token)
                elif firstch in '/<(%':
                    if firstch == '/':
                        # PDF Name
                        if '#' in token:
                            try:
                                token = fixname(token)
                            except ValueError:
                                log.warning('Invalid name token: %s' % token)
                        else:
                            token = PdfObject(token)
                    elif firstch == '<':
                        # << dict delim, or < hex string >
                        if token[1:2] != '<':
                            token = PdfString(token)
                    elif firstch == '(':
                        # Literal string
                        # It's probably simple, but maybe not
                        # Nested parentheses are a bear, and if
                        # they are present, we exit the for loop
                        # and get back in with a new starting location.
                        if fdata[match.end(1)-1] == ')':
                            token = PdfString(token)
                        else:
                            nest = 2
                            for match in findparen(fdata, loc):
                                loc = match.end(1)
                                nest += 1 - (fdata[loc-1] == ')') * 2
                                if not nest:
                                    break
                            if nest:
                                log.error('Unterminated literal string on line %d' %
                                    countlines(fdata, m_start))
                            token = PdfString(fdata[m_start:loc])
                            loc = match.end()
                            current[0] = loc
                            prev[0] = m_start
                            yield token
                            break
                    elif firstch == '%':
                        # Comment
                        if self.strip_comments:
                            continue

                current[0] = loc
                prev[0] = m_start
                yield token
                if current[0] is not loc:
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
        if startloc != current[0]:
            current[0] = startloc

    def floc(self):
        ''' Return the current file position
            (where the next token will be retrieved)
        '''
        return self.current[0]
    floc = property(floc)

    def __iter__(self):
        return self.iterator

    def multiple(self, count, islice=itertools.islice, list=list):
        ''' Retrieve multiple tokens
        '''
        return list(islice(self, count))
