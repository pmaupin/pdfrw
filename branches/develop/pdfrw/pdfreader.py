# A part of pdfrw (pdfrw.googlecode.com)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
The PdfReader class reads an entire PDF file into memory and
parses the top-level container objects.  (It does not parse
into streams.)  The object subclasses PdfDict, and the
document pages are stored in a list in the pages attribute
of the object.
'''

try:
    set
except NameError:
    from sets import Set as set

import gc

from pdferrors import PdfParseError, log
from new_pdftokens import PdfTokens
from pdfobjects import PdfDict, PdfArray, PdfName, PdfObject
from pdfcompress import uncompress

class PdfReader(PdfDict):

    warned_bad_stream_start = False  # Use to keep from spewing warnings
    warned_bad_stream_length = False  # Use to keep from spewing warnings

    class DeferredObject(object):
        ''' A placeholder for an object that hasn't been read in yet.
        '''

    def findindirect(self, objnum, gennum, parent, index,
                     Deferred=DeferredObject, int=int, isinstance=isinstance):
        ''' Read an indirect object.  If it has already
            been read, return it from the cache.
        '''
        key = int(objnum), int(gennum)
        result = self.indirect_objects.get(key)
        if result is None:
            result = Deferred()
            result.key = key
            result.usedby = []
            self.indirect_objects[key] = result
        if isinstance(result, Deferred):
            result.usedby.append((parent, index))
        return result

    def readarray(self, source, PdfArray=PdfArray, len=len):
        ''' Found a [ token.  Parse the tokens after that.
        '''
        specialget = self.special.get
        result = PdfArray()
        pop = result.pop
        append = result.append

        for value in source:
            if value in ']R':
                if value == ']':
                    break
                generation = pop()
                value = self.findindirect(pop(), generation, result, len(result))
            else:
                func = specialget(value)
                if func is not None:
                    value = func(source)
            append(value)
        return result

    def readdict(self, source, PdfDict=PdfDict):
        ''' Found a << token.  Parse the tokens after that.
        '''
        specialget = self.special.get
        result = PdfDict()
        next = source.next

        tok = next()
        while tok != '>>':
            if not tok.startswith('/'):
                source.exception('Expected PDF /name object')
            key = tok
            value = next()
            func = specialget(value)
            if func is not None:
                value = func(source)
                tok = next()
            else:
                tok = next()
                if value.isdigit() and tok.isdigit():
                    if next() != 'R':
                        source.exception('Expected "R" following two integers')
                    value = self.findindirect(value, tok, result, key)
                    tok = next()
            result[key] = value
        return result

    def empty_obj(self, source, PdfObject=PdfObject):
        ''' Some silly git put an empty object in the
            file.  Back up so the caller sees the endobj.
        '''
        source.floc = source.tokstart
        return PdfObject('')

    def badtoken(self, source):
        ''' Didn't see that coming.
        '''
        source.exception('Unexpected delimiter')

    def findstream(self, obj, tok, source, PdfDict=PdfDict, isinstance=isinstance, len=len):
        ''' Figure out if there is a content stream
            following an object, and return the start
            pointer to the content stream if so.

            (We can't read it yet, because we might not
            know how long it is, because Length might
            be an indirect object.)
        '''

        isdict = isinstance(obj, PdfDict)
        if not isdict or tok != 'stream':
            source.exception("Expected 'endobj'%s token", isdict and " or 'stream'" or '')
        fdata = source.fdata
        startstream = source.tokstart + len(tok)
        gotcr = fdata[startstream] == '\r'
        startstream += gotcr
        gotlf = fdata[startstream] == '\n'
        startstream += gotlf
        if not gotlf:
            if not gotcr:
                source.exception(r'stream keyword not followed by \n')
            if not self.warned_bad_stream_start:
                source.warning(r"stream keyword terminated by \r without \n")
                self.private.warned_bad_stream_start = True
        return startstream

    def readstream(self, info, source, fdata,
                     streamending = 'endstream endobj'.split(), int=int):
        obj, startstream, maxstream = info
        length =  int(obj.Length)
        source.floc = endstream = startstream + length
        endit = source.multiple(2)
        if endit == streamending:
            obj._stream = fdata[startstream:endstream]
            return

        # The length attribute is not right.  Perhaps it's fixable.

        endstream = fdata.rfind('endstream', startstream, maxstream)
        if fdata[endstream-1] == '\n':
            endstream -= 1
        if fdata[endstream-1] == '\r':
            endstream -= 1
        ok = endstream >= startstream
        if ok:
            source.floc = endstream
            endit = source.multiple(2)
            ok = endit == streamending
        source.floc = 0
        source.floc = startstream
        if not ok:
            source.exception('Cannot find endstream or endobj')
        if not self.warned_bad_stream_length:
            source.error('Stream of apparent length %d has declared length of %d',
                    endstream - startstream, length)
            self.private.warned_bad_stream_length = True
        obj.stream = fdata[startstream:endstream]

    def ordered_offsets(self):
        obj_offsets = sorted(self.obj_offsets.iteritems(), key=lambda x:x[1])
        obj_offsets.append((None, len(self.fdata)))
        for i in range(len(obj_offsets)-1):
            yield obj_offsets[i:i+2]

    def read_all_indirect(self, source, int=int,
                isinstance=isinstance, DeferredObject=DeferredObject):
        ''' Read all the indirect objects from the file.
            Sort them into file order before reading -- this helps
            to reduce the number of instantiations of re.finditer objects
            inside the tokenizer.
        '''

        next = source.next
        multiple = source.multiple
        specialget = self.special.get
        indirect_objects = self.indirect_objects
        indirectget = indirect_objects.get
        findstream = self.findstream
        streams = []

        for (key, offset), (key2, offset2) in self.ordered_offsets():
            # Read the object header and validate it
            objnum, gennum = key
            source.floc = offset
            objid = multiple(3)
            ok = objid[2] == 'obj'
            ok = ok and objid[0].isdigit() and int(objid[0]) == objnum
            ok = ok and objid[1].isdigit() and int(objid[1]) == gennum
            if not ok:
                source.floc = offset
                source.next()
                source.warning("Expected indirect object '%d %d obj'" % (objnum, gennum))
                continue

            # Read the object, and call special code if it starts
            # an array or dictionary
            obj = next()
            func = specialget(obj)
            if func is not None:
                obj = func(source)

            # Replace any occurences of the deferred object
            # with the real thing, then insert our object
            deferred = indirectget(key)
            if deferred is not None:
                deferred.value = obj
                for parent, index in deferred.usedby:
                    parent[index] = obj
            indirect_objects[key] = obj

            # Mark the object as indirect, and
            # add it to the list of streams if it starts a stream
            obj.indirect = True
            tok = source.next()
            if tok != 'endobj':
                streams.append((obj, findstream(obj, tok, source), offset2))

        # Once we've read ALL the indirect objects, including
        # stream lengths, we can update the stream objects with
        # the stream information.
        fdata = source.fdata
        for info in streams:
            self.readstream(info, source, fdata)

        # We created the top dict by merging other dicts,
        # so now we need to fix up the indirect objects there.
        for key, obj in list(self.iteritems()):
            if isinstance(obj, DeferredObject):
                self[key] = obj.value

    def findxref(fdata):
        ''' Find the cross reference section at the end of a file
        '''
        startloc = fdata.rfind('startxref')
        if startloc < 0:
            raise PdfParseError('Did not find trailer ("startxref") at end of file')
        source = PdfTokens(fdata, startloc, False)
        assert source.next() == 'startxref'  # (We just checked this...)
        tableloc = source.next_default()
        if not tableloc.isdigit():
            source.exception('Expected table location')
        if source.next_default().rstrip() != '%%EOF':
            source.exception('Expected %%EOF')
        return startloc, PdfTokens(fdata, int(tableloc), True)
    findxref = staticmethod(findxref)

    def parsexref(self, source, int=int, range=range):
        ''' Parse (one of) the cross-reference file section(s)
        '''
        fdata = self.fdata
        setdefault = self.obj_offsets.setdefault
        next = source.next
        tok = next()
        if tok != 'xref':
            source.exception('Expected "xref" keyword')
        start = source.floc
        try:
            while 1:
                tok = next()
                if tok == 'trailer':
                    break
                startobj = int(tok)
                for objnum in range(startobj, startobj + int(next())):
                    offset = int(next())
                    generation = int(next())
                    if next() == 'n' and offset != 0:
                        setdefault((objnum, generation), offset)
        except:
            source.floc = start
            source.exception('Invalid table format')

    def readpages(self, node, pagename=PdfName.Page, pagesname=PdfName.Pages):
        # PDFs can have arbitrarily nested Pages/Page
        # dictionary structures.
        if node.Type == pagename:
            return [node]
        assert node.Type == pagesname, node.Type
        result = []
        for node in node.Kids:
            result.extend(self.readpages(node))
        return result

    def __init__(self, fname=None, fdata=None, decompress=True, disable_gc=True):

        # Runs a lot faster with GC off.
        disable_gc = disable_gc and gc.isenabled()
        try:
            if disable_gc:
                gc.disable()
            if fname is not None:
                assert fdata is None
                # Allow reading preexisting streams like pyPdf
                if hasattr(fname, 'read'):
                    fdata = fname.read()
                else:
                    f = open(fname, 'rb')
                    fdata = f.read()
                    f.close()

            assert fdata is not None
            if not fdata.startswith('%PDF-'):
                raise PdfParseError('Invalid PDF header: %s' % repr(fdata[:20].splitlines()[0]))

            endloc = fdata.rfind('%%EOF')
            if endloc < 0:
                raise PdfParseError('EOF mark not found: %s' % repr(fdata[-20:]))
            endloc += 6
            junk = fdata[endloc:]
            fdata = fdata[:endloc]
            if junk.rstrip('\00').strip():
                log.warning('Extra data at end of file')

            self.private.fdata = fdata

            self.private.indirect_objects = {}
            self.private.special = {'<<': self.readdict,
                                    '[': self.readarray,
                                    'endobj': self.empty_obj,
                                    }
            for tok in r'\ ( ) < > { } ] >> %'.split():
                self.special[tok] = self.badtoken

            self.private.obj_offsets = {}

            startloc, source = self.findxref(fdata)
            while 1:
                # Loop through all the cross-reference tables
                self.parsexref(source)
                tok = source.next()
                if tok != '<<':
                    source.exception('Expected "<<" starting cross-reference table')
                # Do not overwrite preexisting entries
                newdict = self.readdict(source).copy()
                newdict.update(self)
                self.update(newdict)

                # Loop if any previously-written tables.
                token = source.next()
                if token != 'startxref':
                    source.exception('Expected "startxref" at end of xref table')
                if self.Prev is None:
                    break
                source.floc = int(self.Prev)
                self.Prev = None

            self.read_all_indirect(source)
            self.private.pages = self.readpages(self.Root.Pages)
            if decompress:
                self.uncompress()

            # For compatibility with pyPdf
            self.private.numPages = len(self.pages)
        finally:
            if disable_gc:
                gc.enable()

    # For compatibility with pyPdf
    def getPage(self, pagenum):
        return self.pages[pagenum]

    def uncompress(self):
        uncompress([x[1] for x in self.indirect_objects.itervalues()])
