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
import gc

from pdfrw.errors import PdfParseError, log
from pdfrw.tokens import PdfTokens
from pdfrw.objects import PdfDict, PdfArray, PdfName, PdfObject, PdfIndirect
from pdfrw.uncompress import uncompress

class PdfReader(PdfDict):

    warned_bad_stream_start = False  # Use to keep from spewing warnings
    warned_bad_stream_end = False  # Use to keep from spewing warnings

    def findindirect(self, objnum, gennum, PdfIndirect=PdfIndirect, int=int):
        ''' Read an indirect object.  If it has already
            been read, return it from the cache.
        '''
        key = int(objnum), int(gennum)
        result = self.indirect_objects.get(key)
        if result is None:
            self.indirect_objects[key] = result = PdfIndirect(key)
            result._loader = self.loadindirect
        return result

    def readarray(self, source, PdfArray=PdfArray):
        ''' Found a [ token.  Parse the tokens after that.
        '''
        specialget = self.special.get
        result = []
        pop = result.pop
        append = result.append

        for value in source:
            if value in ']R':
                if value == ']':
                    break
                generation = pop()
                value = self.findindirect(pop(), generation)
            else:
                func = specialget(value)
                if func is not None:
                    value = func(source)
            append(value)
        return PdfArray(result)

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
                    value = self.findindirect(value, tok)
                    tok = next()
            result[key] = value
        return result

    def empty_obj(self, source, PdfObject=PdfObject):
        ''' Some silly git put an empty object in the
            file.  Back up so the caller sees the endobj.
        '''
        source.floc = source.tokstart
        # TODO:  Change to None and check
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

    def readstream(self, obj, startstream, source,
                     streamending = 'endstream endobj'.split(), int=int):
        fdata = source.fdata
        length =  int(obj.Length)
        source.floc = target_endstream = startstream + length
        endit = source.multiple(2)
        obj._stream = fdata[startstream:target_endstream]
        if endit == streamending:
            return

        # The length attribute does not match the distance between the
        # stream and endstream keywords.

        do_warn, self.warned_bad_stream_end = self.warned_bad_stream_end, False

        #TODO:  Extract maxstream from dictionary of object offsets
        # and use rfind instead of find.
        maxstream = len(fdata) - 20
        endstream = fdata.rfind('endstream', startstream, maxstream)
        source.floc = startstream
        room = endstream - startstream
        if endstream < 0:
            source.error('Could not find endstream')
            return
        if length == room + 1 and fdata[startstream-2:startstream] == '\r\n':
            source.warning(r"stream keyword terminated by \r without \n")
            obj._stream = fdata[startstream-1:target_endstream-1]
            return
        source.floc = endstream
        if length > room:
            source.error('stream /Length attribute (%d) appears to be too big (size %d) -- adjusting',
                             length, room)
            obj.stream = fdata[startstream:endstream]
            return
        if fdata[target_endstream:endstream].rstrip():
            source.error('stream /Length attribute (%d) might be smaller than data size (%d)',
                             length, room)
            return
        endobj = fdata.find('endobj', endstream, maxstream)
        if endobj < 0:
            source.error('Could not find endobj after endstream')
            return
        if fdata[endstream:endobj].rstrip() != 'endstream':
            source.error('Unexpected data between endstream and endobj')
            return
        source.error('Illegal endstream/endobj combination')

    def loadindirect(self, key):
        source = self.source
        offset = int(self.source.obj_offsets.get(key, '0'))
        if not offset:
            log.warning("Did not find PDF object %s" % key)
            return None

        # Read the object header and validate it
        objnum, gennum = key
        source.floc = offset
        objid = source.multiple(3)
        ok = objid[2] == 'obj'
        ok = ok and objid[0].isdigit() and int(objid[0]) == objnum
        ok = ok and objid[1].isdigit() and int(objid[1]) == gennum
        if not ok:
            source.floc = offset
            source.next()
            source.warning("Expected indirect object '%d %d obj'" % (objnum, gennum))
            return None

        # Read the object, and call special code if it starts
        # an array or dictionary
        obj = source.next()
        func = self.special.get(obj)
        if func is not None:
            obj = func(source)

        self.indirect_objects[key] = obj

        # Mark the object as indirect, and
        # add it to the list of streams if it starts a stream
        obj.indirect = True
        tok = source.next()
        if tok != 'endobj':
            self.readstream(obj, self.findstream(obj, tok, source), source)
        return obj

    def findxref(fdata):
        ''' Find the cross reference section at the end of a file
        '''
        startloc = fdata.rfind('startxref')
        if startloc < 0:
            raise PdfParseError('Did not find "startxref" at end of file')
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
        fdata = source.fdata
        setdefault = source.obj_offsets.setdefault
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
        subnodes = node.Kids
        for node in node.Kids:
            result.extend(self.readpages(node))
        return result

    def __init__(self, fname=None, fdata=None, decompress=False, disable_gc=True):

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

            private = self.private
            private.indirect_objects = {}
            private.special = {'<<': self.readdict,
                               '[': self.readarray,
                               'endobj': self.empty_obj,
                               }
            for tok in r'\ ( ) < > { } ] >> %'.split():
                self.special[tok] = self.badtoken


            startloc, source = self.findxref(fdata)
            private.source = source
            source.obj_offsets = {}
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

            #self.read_all_indirect(source)
            private.pages = self.readpages(self.Root.Pages)
            #if decompress:
            #    self.uncompress()

            # For compatibility with pyPdf
            private.numPages = len(self.pages)
        finally:
            if disable_gc:
                gc.enable()

    # For compatibility with pyPdf
    def getPage(self, pagenum):
        return self.pages[pagenum]

    #def uncompress(self):
    #    uncompress([x[1] for x in self.indirect_objects.itervalues()])
