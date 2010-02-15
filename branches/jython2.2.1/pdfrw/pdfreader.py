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

from pdftokens import PdfTokens
from pdfobjects import PdfDict, PdfArray, PdfName
from pdfcompress import uncompress

class PdfReader(PdfDict):

    class DeferredObject(object):
        pass

    def readindirect(self, objnum, gennum, Deferred=DeferredObject):
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
            self.deferred.add(result)
        return isinstance(result, Deferred), result

    def readarray(self, source):
        special = self.special
        result = PdfArray()

        for value in source:
            if value == ']':
                break
            deferred = False
            if value in special:
                value = special[value](source)
            elif value == 'R':
                generation = result.pop()
                deferred, value = self.readindirect(result.pop(), generation)
            if deferred:
                value.usedby.append((result, len(result)))
            result.append(value)
        return result

    def readdict(self, source):
        special = self.special
        result = PdfDict()

        tok = source.next()
        while tok != '>>':
            assert tok.startswith('/'), (tok, source.multiple(10))
            key = tok
            value = source.next()
            deferred = False
            if value in special:
                value = special[value](source)
                tok = source.next()
            else:
                tok = source.next()
                if value.isdigit() and tok.isdigit():
                    assert source.next() == 'R'
                    deferred, value = self.readindirect(value, tok)
                    tok = source.next()
            if deferred:
                value.usedby.append((result, key))
            result[key] = value
        return result

    def readstream(obj, source):
        ''' Read optional stream following a dictionary
            object.
        '''
        tok = source.next()
        if tok == 'endobj':
            return  # No stream

        assert isinstance(obj, PdfDict)
        assert tok == 'stream', tok
        fdata = source.fdata
        floc = fdata.rfind(tok, 0, source.floc) + len(tok)
        ch = fdata[floc]
        if ch == '\r':
            floc += 1
            ch = fdata[floc]
        assert ch == '\n'
        startstream = floc + 1
        return startstream
    readstream = staticmethod(readstream)

    def expand_deferred(self):
        deferredset = self.deferred
        obj_offsets = self.obj_offsets
        specialget = self.special.get
        indirect_objects = self.indirect_objects
        readstream = self.readstream
        fdata = self.fdata
        DeferredObject = self.DeferredObject
        streams = []

        while deferredset:
            deferred = deferredset.pop()
            key = deferred.key
            offset = obj_offsets[key]

            # Read the object header and validate it
            objnum, gennum = key
            source = PdfTokens(fdata, offset)
            objid = source.multiple(3)
            assert int(objid[0]) == objnum, objid
            assert int(objid[1]) == gennum, objid
            assert objid[2] == 'obj', objid

            # Read the object, and call special code if it starts
            # an array or dictionary
            obj = source.next()
            func = specialget(obj)
            if func is not None:
                obj = func(source)
            startstream = readstream(obj, source)
            obj.indirect = True
            indirect_objects[key] = obj
            deferred.value = obj
            for parent, index in deferred.usedby:
                parent[index] = obj

            if startstream is not None:
                streams.append((obj, startstream))

        for obj, startstream in streams:
            endstream = startstream + int(obj.Length)
            obj._stream = fdata[startstream:endstream]
            source = PdfTokens(fdata, endstream)
            endit = source.multiple(2)
            assert endit == 'endstream endobj'.split(), endit

        newdict = {}
        for key, obj in self.iteritems():
            if isinstance(obj, DeferredObject):
                newdict[key] = obj.value
        self.update(newdict)

    def readxref(fdata):
        startloc = fdata.rfind('startxref')
        xrefinfo = list(PdfTokens(fdata, startloc, False))
        assert len(xrefinfo) == 3, xrefinfo
        assert xrefinfo[0] == 'startxref', xrefinfo[0]
        assert xrefinfo[1].isdigit(), xrefinfo[1]
        assert xrefinfo[2].rstrip() == '%%EOF', repr(xrefinfo[2])
        return startloc, PdfTokens(fdata, int(xrefinfo[1]))
    readxref = staticmethod(readxref)

    def parsexref(self, source):
        fdata = self.fdata
        obj_offsets = self.obj_offsets
        tok = source.next()
        assert tok == 'xref', tok
        while 1:
            tok = source.next()
            if tok == 'trailer':
                break
            startobj = int(tok)
            for objnum in range(startobj, startobj + int(source.next())):
                offset = int(source.next())
                generation = int(source.next())
                if source.next() == 'n':
                    objid = objnum, generation
                    obj_offsets.setdefault(objid, offset)

    pagename = PdfName.Page
    pagesname = PdfName.Pages

    def readpages(self, node):
        # PDFs can have arbitrarily nested Pages/Page
        # dictionary structures.
        if node.Type == self.pagename:
            return [node]
        assert node.Type == self.pagesname, node.Type
        result = []
        for node in node.Kids:
            result.extend(self.readpages(node))
        return result

    def __init__(self, fname=None, fdata=None, decompress=True):

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
        fdata = fdata.rstrip('\00')
        self.private.fdata = fdata

        self.private.indirect_objects = {}
        self.private.special = {'<<': self.readdict, '[': self.readarray}
        self.private.deferred = deferred = set()
        self.private.obj_offsets = {}

        startloc, source = self.readxref(fdata)
        while 1:
            self.parsexref(source)
            assert source.next() == '<<'
            self.update(self.readdict(source))
            token = source.next()
            assert token == 'startxref' # and source.floc > startloc, (token, source.floc, startloc)
            if self.Prev is None:
                break
            source = PdfTokens(fdata, int(self.Prev))
            self.Prev = None

        if deferred:
            self.expand_deferred()

        self.private.pages = self.readpages(self.Root.Pages)
        if decompress:
            self.uncompress()

        # For compatibility with pyPdf
        self.numPages = len(self.pages)


    # For compatibility with pyPdf
    def getPage(self, pagenum):
        return self.pages[pagenum]

    def uncompress(self):
        uncompress([x[1] for x in self.indirect_objects.itervalues()])
