# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A tokenizer for PDF streams.

In general, documentation used was "PDF reference",
sixth edition, for PDF version 1.7, dated November 2006.

'''

import re
import itertools
from .objects import PdfString, PdfObject
from .objects.pdfname import BasePdfName
from .errors import log, PdfParseError
from .py23_diffs import nextattr, intern


def linepos(fdata, loc):
    line = fdata.count('\n', 0, loc) + 1
    line += fdata.count('\r', 0, loc) - fdata.count('\r\n', 0, loc)
    col = loc - max(fdata.rfind('\n', 0, loc), fdata.rfind('\r', 0, loc))
    return line, col


class PdfTokens(object):

    # Table 3.1, page 50 of reference, defines whitespace
    eol = '\n\r'
    whitespace = '\x00 \t\f' + eol

    # Text on page 50 defines delimiter characters
    # Escape the ]
    delimiters = r'()<>{}[\]/%'

    # "normal" stuff is all but delimiters or whitespace.

    p_normal = r'(?:[^\\%s%s]+|\\[^%s])+' % (whitespace, delimiters,
                                             whitespace)

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

    pattern = '|'.join([p_normal, p_name, p_hex_string, p_dictdelim,
                        p_literal_string, p_comment, p_catchall])
    findtok = re.compile('(%s)[%s]*' % (pattern, whitespace),
                         re.DOTALL).finditer
    findparen = re.compile('(%s)[%s]*' % (p_literal_string_extend,
                                          whitespace), re.DOTALL).finditer

    def _gettoks(self, startloc, intern=intern,
                 delimiters=delimiters, findtok=findtok,
                 findparen=findparen, PdfString=PdfString,
                 PdfObject=PdfObject, BasePdfName=BasePdfName):
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
        get_cache = cache.get
        while 1:
            for match in findtok(fdata, current[0][1]):
                current[0] = tokspan = match.span()
                token = match.group(1)
                firstch = token[0]
                toktype = intern
                if firstch not in delimiters:
                    toktype = PdfObject
                elif firstch in '/<(%':
                    if firstch == '/':
                        # PDF Name
                        toktype = BasePdfName
                    elif firstch == '<':
                        # << dict delim, or < hex string >
                        if token[1:2] != '<':
                            toktype = PdfString
                    elif firstch == '(':
                        # Literal string
                        # It's probably simple, but maybe not
                        # Nested parentheses are a bear, and if
                        # they are present, we exit the for loop
                        # and get back in with a new starting location.
                        ends = None  # For broken strings
                        if fdata[match.end(1) - 1] != ')':
                            nest = 2
                            m_start, loc = tokspan
                            for match in findparen(fdata, loc):
                                loc = match.end(1)
                                ending = fdata[loc - 1] == ')'
                                nest += 1 - ending * 2
                                if not nest:
                                    break
                                if ending and ends is None:
                                    ends = loc, match.end(), nest
                            token = fdata[m_start:loc]
                            current[0] = m_start, match.end()
                            if nest:
                                # There is one possible recoverable error
                                # seen in the wild -- some stupid generators
                                # don't escape (.  If this happens, just
                                # terminate on first unescaped ). The string
                                # won't be quite right, but that's a science
                                # fair project for another time.
                                (self.error, self.exception)[not ends](
                                    'Unterminated literal string')
                                loc, ends, nest = ends
                                token = fdata[m_start:loc] + ')' * nest
                                current[0] = m_start, ends
                        toktype = PdfString
                    elif firstch == '%':
                        # Comment
                        if self.strip_comments:
                            continue
                    else:
                        self.exception(('Tokenizer logic incorrect -- '
                                        'should never get here'))

                newtok = get_cache(token)
                if newtok is None:
                    newtok = cache[token] = toktype(token)
                yield newtok
                if current[0] is not tokspan:
                    break
            else:
                if self.strip_comments:
                    break
                raise StopIteration

    def __init__(self, fdata, startloc=0, strip_comments=True, verbose=True):
        self.fdata = fdata
        self.strip_comments = strip_comments
        self.iterator = iterator = self._gettoks(startloc)
        self.msgs_dumped = None if verbose else set()
        self.next = getattr(iterator, nextattr)
        self.current = [(startloc, startloc)]

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

    def tokstart(self):
        ''' Return the file position of the most
            recently retrieved token.
        '''
        return self.current[0][0]
    tokstart = property(tokstart, setstart)

    def __iter__(self):
        return self.iterator

    def multiple(self, count, islice=itertools.islice, list=list):
        ''' Retrieve multiple tokens
        '''
        return list(islice(self, count))

    def next_default(self, default='nope'):
        for result in self:
            return result
        return default

    def msg(self, msg, *arg):
        dumped = self.msgs_dumped
        if dumped is not None:
            if msg in dumped:
                return
            dumped.add(msg)
        if arg:
            msg %= arg
        fdata = self.fdata
        begin, end = self.current[0]
        if begin >= len(fdata):
            return '%s (filepos %s past EOF %s)' % (msg, begin, len(fdata))
        line, col = linepos(fdata, begin)
        if end > begin:
            tok = fdata[begin:end].rstrip()
            if len(tok) > 30:
                tok = tok[:26] + ' ...'
            return ('%s (line=%d, col=%d, token=%s)' %
                    (msg, line, col, repr(tok)))
        return '%s (line=%d, col=%d)' % (msg, line, col)

    def warning(self, *arg):
        s = self.msg(*arg)
        if s:
            log.warning(s)

    def error(self, *arg):
        s = self.msg(*arg)
        if s:
            log.error(s)

    def exception(self, *arg):
        raise PdfParseError(self.msg(*arg))
