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
import pdferrors
from pdfobjects import PdfString, PdfObject


def fixname(token, PdfObject=PdfObject, join=''.join):
    ''' Inside name tokens, a '#' character indicates that
        the next two bytes are hex characters to be used
        to form the 'real' character.
    '''
    try:
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
    except ValueError:
        raise pdferrors.PdfInvalidCharacterError(source, m_start, token)

class TokenGroup(object):

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

    @staticmethod
    def gettoks(source, loc, strip_comments, fixname=fixname,
                       delimiters=delimiters, findtok=findtok, findparen=findparen,
                       PdfString=PdfString, PdfObject=PdfObject):
        ''' Given a source data string and a location inside it,
            gettoks generates tokens.  Each token is a tuple of the form:
             <starting file loc>, <ending file loc>, <token string>
            The ending file loc is past any trailing whitespace.

            The main complication here is the literal strings, which
            can contain nested parentheses.  In order to cope with these
            we can discard the current iterator and loop back to the
            top to get a fresh one.  This is handled  by the changed_loc
            local variable.
        '''
        changed_loc = True
        while changed_loc:
            changed_loc = False
            for match in findtok(source, loc):
                m_start, loc = match.span()
                token = match.group(1)
                firstch = token[0]
                if firstch not in delimiters:
                    token = PdfObject(token)
                elif firstch in '/<(%':
                    if firstch == '/':
                        # PDF Name
                        if '#' in token:
                            token = fixname(token)
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
                        if source[match.end(1)-1] == ')':
                            token = PdfString(token)
                        else:
                            nest = 2
                            for match in findparen(source, loc):
                                loc = match.end(1)
                                nest += 1 - (source[loc-1] == ')') * 2
                                if not nest:
                                    break
                            if nest:
                                raise pdferrors.PdfUnexpectedEOFError(source)
                            token = PdfString(source[m_start:loc])
                            loc = match.end()
                            changed_loc = True
                            yield m_start, loc, token
                            break
                    elif firstch == '%':
                        # Comment
                        if strip_comments:
                            continue

                yield m_start, loc, token

class PdfTokens(object):

    def __init__(self, fdata, startloc=0, strip_comments=True):
        self.fdata = fdata
        self.strip_comments = strip_comments
        self.current = current = [(startloc, startloc)]

        def iterator(gettoks=TokenGroup.gettoks):
            while 1:
                for token in gettoks(fdata, current[0][1], self.strip_comments):
                    current[0] = token
                    yield token[2]
                    if current[0] is not token:
                        # If client changed starting location,
                        # break out of the for loop and start over
                        break
                else:
                    raise StopIteration

        iterator = iterator()
        self.iterator = iterator
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
    floc = property(floc)

    def __iter__(self):
        return self.iterator

    def multiple(self, count, islice=itertools.islice, list=list):
        ''' Retrieve multiple tokens
        '''
        return list(islice(self, count))
