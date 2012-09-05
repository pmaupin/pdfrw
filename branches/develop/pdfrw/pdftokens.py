# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
A tale of two tokenizers:

- Compare the old and new for accuracy.
- Implicitly defines the public interface to the tokenizer.

'''

from old_pdftokens import PdfTokens as OldTokens
from new_pdftokens import PdfTokens as NewTokens
from pdflog import log

class PdfTokens(object):

    def __init__(self, fdata, startloc=0, strip_comments=True):
        self.fdata = fdata
        self.old = old = OldTokens(fdata, startloc, strip_comments)
        self.new = new = NewTokens(fdata, startloc, strip_comments)
        self.old_next = old.next
        self.new_next = new.next
        self.old_multiple = old.multiple
        self.new_multiple = new.multiple
        self.old_setstart = old.setstart
        self.new_setstart = new.setstart

    def next(self, Done=StopIteration):
        try:
            old = self.old_next()
        except Done:
            old = Done
        try:
            new = self.new_next()
        except Done:
            new = Done
        if old != new:
            log.warning('Tokens different: old = %s from %d; new = %s from %d' %
                        (repr(old), self.old.floc, repr(new), self.new.floc))
        if old is Done:
            raise Done
        return old


    def multiple(self, count):
        old = self.old_multiple(count)
        new = self.new_multiple(count)
        if old != new:
            log.warning('Multiples different: old = %s from %d; new = %s from %d' %
                        (old, self.old.floc, new, self.new.floc))
        return old

    @property
    def floc(self):
        old = self.old.floc
        new = self.new.floc
        if old != new:
            log.warning('Floc different: old = %d; new = %d' %
                        (old, new))
        return old

    def setstart(self, start):
        self.old_setstart(start)
        self.new_setstart(start)

    def _set_strip_comments(self, value):
        self.old.strip_comments = value
        self.new.strip_comments = value
    strip_comments = property(fset=_set_strip_comments)

    def __iter__(self):
        return self

