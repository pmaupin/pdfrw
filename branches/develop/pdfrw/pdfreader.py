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

from pdferrors import PdfUnexpectedTokenError, PdfStructureError, PdfInputError
from new_pdftokens import PdfTokens
from pdfobjects import PdfDict, PdfArray, PdfName, PdfObject
from pdfcompress import uncompress

from pdflog import log

class PdfReader(PdfDict):

    warned_bad_stream = False

    class DeferredObject(object):
        pass

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
            assert tok.startswith('/'), (tok, source.multiple(10))
            key = tok
            value = next()
            func = specialget(value)
            if func is not None:
                value = func(source)
                tok = next()
            else:
                tok = next()
                if value.isdigit() and tok.isdigit():
                    assert next() == 'R'
                    value = self.findindirect(value, tok, result, key)
                    tok = next()
            result[key] = value
        return result

    def empty_obj(self, source, PdfObject=PdfObject):
        ''' Some silly git put an empty object in the
            file.  Back up so the caller sees the endobj.
        '''
        fdata = source.fdata
        floc = fdata.rindex('endobj', 0, source.floc)
        source.setstart(floc) # Back up
        return PdfObject('')

    def badtoken(self, source):
        ''' Didn't see that coming.
        '''
        raise PdfStructureError(source.fdata, source.floc - 2, 'Unexpected delimiter')

    def findstream(self, obj, tok, source, PdfDict=PdfDict, isinstance=isinstance, len=len):
        ''' Figure out if there is a content stream
            following an object, and return the start
            pointer to the content stream if so.

            (We can't read it yet, because we might not
            know how long it is, because Length might
            be an indirect object.)
        '''

        assert isinstance(obj, PdfDict), (type(obj), obj)
        assert tok == 'stream', tok
        fdata = source.fdata
        floc = fdata.rindex(tok, 0, source.floc) + len(tok)
        ch = fdata[floc]
        if ch == '\r':
            floc += 1
            ch = '\n'
            if ch != fdata[floc]:
                floc -= 1
                if not self.warned_bad_stream:
                    log.warning("foo stream terminated by \\r without \\n at file location %s" % floc)
                    self.private.warned_bad_stream = True
        assert ch == '\n'
        startstream = floc + 1
        return startstream

    def read_all_indirect(self, source, int=int,
                isinstance=isinstance, DeferredObject=DeferredObject):
        ''' Read all the indirect objects from the file.
            Sort them into file order before reading -- this helps
            to reduce the number of instantiations of re.finditer objects
            inside the tokenizer.
        '''

        obj_offsets = self.obj_offsets.iteritems()
        obj_offsets = [(offset, key) for (key, offset) in obj_offsets]
        obj_offsets.sort()
        setstart = source.setstart
        next = source.next
        multiple = source.multiple
        specialget = self.special.get
        indirect_objects = self.indirect_objects
        indirectget = indirect_objects.get
        findstream = self.findstream
        streams = []

        for offset, key in obj_offsets:
            # Read the object header and validate it
            objnum, gennum = key
            setstart(offset)
            objid = multiple(3)
            try:
                ok = objid[2] == 'obj'
                ok = ok and int(objid[0]) == objnum
                ok = ok and int(objid[1]) == gennum
                if not ok:
                    raise PdfStructureError
            except:
                log.warning("Did not find PDF object '%d %d obj' at file offset %d" % (objnum, gennum, offset))
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
                streams.append((obj, findstream(obj, tok, source)))

        # Once we've read ALL the indirect objects, including
        # stream lengths, we can update the stream objects with
        # the stream information.
        streamending = 'endstream endobj'.split()
        fdata = self.fdata
        for obj, startstream in streams:
            endstream = startstream + int(obj.Length)
            obj._stream = fdata[startstream:endstream]
            setstart(endstream)
            try:
                endit = source.multiple(2)
                if endit != streamending:
                    raise PdfUnexpectedTokenError(fdata, endstream, endit[0])
            except PdfInputError:
                # perhaps the /Length attribute is broken,
                # try to read stream anyway disregarding the specified value
                log.error('incorrect obj stream /Length parameter')
                endstream = fdata.index('endstream', startstream)
                if fdata[endstream-2:endstream] == '\r\n':
                    endstream -= 2
                elif fdata[endstream-1] in ['\n', '\r']:
                    endstream -= 1
                setstart(endstream)
                endit = source.multiple(2)
                if endit != streamending:
                    raise
                obj.Length = str(endstream-startstream)
                obj._stream = fdata[startstream:endstream]


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
            raise PdfStructureError(fdata, 0, 'Trailer not found')
        xrefinfo = list(PdfTokens(fdata, startloc, False))
        if (len(xrefinfo) != 3 or
            xrefinfo[0] != 'startxref' or
            not xrefinfo[1].isdigit() or
            xrefinfo[2].rstrip() != '%%EOF'):
                raise PdfStructureError(fdata, startloc, 'Invalid trailer', xrefinfo)
        return startloc, PdfTokens(fdata, int(xrefinfo[1]), True)
    findxref = staticmethod(findxref)

    def parsexref(self, source, int=int, range=range):
        ''' Parse (one of) the cross-reference file section(s)
        '''
        fdata = self.fdata
        setdefault = self.obj_offsets.setdefault
        next = source.next
        tok = next()
        if tok != 'xref':
            raise PdfStructureError(source.fdata, source.floc, 'Invalid xref', tok)
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
                raise PdfStructureError(fdata, 0, 'Invalid PDF header', fdata[:20])

            endloc = fdata.rfind('%%EOF')
            if endloc < 0:
                raise PdfStructureError(fdata, len(fdata)-20, 'EOF mark not found')
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
                    raise PdfStructureError(source.fdata, source.floc, 'Invalid xref', tok)
                # Do not overwrite preexisting entries
                newdict = self.readdict(source).copy()
                newdict.update(self)
                self.update(newdict)

                # Loop if any previously-written tables.
                token = source.next()
                if token != 'startxref':
                    raise PdfStructureError(source.fdata, source.floc, 'Invalid xref', token)
                if self.Prev is None:
                    break
                source.setstart(int(self.Prev))
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
