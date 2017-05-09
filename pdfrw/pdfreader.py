# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2015 Patrick Maupin, Austin, Texas
# Copyright (C) 2012-2015 Nerijus Mika
# MIT license -- See LICENSE.txt for details

'''
The PdfReader class reads an entire PDF file into memory and
parses the top-level container objects.  (It does not parse
into streams.)  The object subclasses PdfDict, and the
document pages are stored in a list in the pages attribute
of the object.
'''
import gc
import binascii
import collections
import itertools

from .errors import PdfParseError, log
from .tokens import PdfTokens
from .objects import PdfDict, PdfArray, PdfName, PdfObject, PdfIndirect
from .uncompress import uncompress
from . import crypt
from .py23_diffs import convert_load, convert_store, iteritems


class PdfReader(PdfDict):

    def findindirect(self, objnum, gennum, PdfIndirect=PdfIndirect, int=int):
        ''' Return a previously loaded indirect object, or create
            a placeholder for it.
        '''
        key = int(objnum), int(gennum)
        result = self.indirect_objects.get(key)
        if result is None:
            self.indirect_objects[key] = result = PdfIndirect(key)
            self.deferred_objects.add(key)
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
                source.error('Expected PDF /name object')
                tok = next()
                continue
            key = tok
            value = next()
            func = specialget(value)
            if func is not None:
                value = func(source)
                tok = next()
            else:
                tok = next()
                if value.isdigit() and tok.isdigit():
                    tok2 = next()
                    if tok2 != 'R':
                        source.error('Expected "R" following two integers')
                        tok = tok2
                        continue
                    value = self.findindirect(value, tok)
                    tok = next()
            result[key] = value
        return result

    def empty_obj(self, source, PdfObject=PdfObject):
        ''' Some silly git put an empty object in the
            file.  Back up so the caller sees the endobj.
        '''
        source.floc = source.tokstart

    def badtoken(self, source):
        ''' Didn't see that coming.
        '''
        source.exception('Unexpected delimiter')

    def findstream(self, obj, tok, source, len=len):
        ''' Figure out if there is a content stream
            following an object, and return the start
            pointer to the content stream if so.

            (We can't read it yet, because we might not
            know how long it is, because Length might
            be an indirect object.)
        '''

        fdata = source.fdata
        startstream = source.tokstart + len(tok)
        gotcr = fdata[startstream] == '\r'
        startstream += gotcr
        gotlf = fdata[startstream] == '\n'
        startstream += gotlf
        if not gotlf:
            if not gotcr:
                source.error(r'stream keyword not followed by \n')
            else:
                source.warning(r"stream keyword terminated "
                               r"by \r without \n")
        return startstream

    def readstream(self, obj, startstream, source, exact_required=False,
                   streamending='endstream endobj'.split(), int=int):
        fdata = source.fdata
        length = int(obj.Length)
        source.floc = target_endstream = startstream + length
        endit = source.multiple(2)
        obj._stream = fdata[startstream:target_endstream]
        if endit == streamending:
            return

        if exact_required:
            source.exception('Expected endstream endobj')

        # The length attribute does not match the distance between the
        # stream and endstream keywords.

        # TODO:  Extract maxstream from dictionary of object offsets
        # and use rfind instead of find.
        maxstream = len(fdata) - 20
        endstream = fdata.find('endstream', startstream, maxstream)
        source.floc = startstream
        room = endstream - startstream
        if endstream < 0:
            source.error('Could not find endstream')
            return
        if (length == room + 1 and
                fdata[startstream - 2:startstream] == '\r\n'):
            source.warning(r"stream keyword terminated by \r without \n")
            obj._stream = fdata[startstream - 1:target_endstream - 1]
            return
        source.floc = endstream
        if length > room:
            source.error('stream /Length attribute (%d) appears to '
                         'be too big (size %d) -- adjusting',
                         length, room)
            obj.stream = fdata[startstream:endstream]
            return
        if fdata[target_endstream:endstream].rstrip():
            source.error('stream /Length attribute (%d) appears to '
                         'be too small (size %d) -- adjusting',
                         length, room)
            obj.stream = fdata[startstream:endstream]
            return
        endobj = fdata.find('endobj', endstream, maxstream)
        if endobj < 0:
            source.error('Could not find endobj after endstream')
            return
        if fdata[endstream:endobj].rstrip() != 'endstream':
            source.error('Unexpected data between endstream and endobj')
            return
        source.error('Illegal endstream/endobj combination')

    def loadindirect(self, key, PdfDict=PdfDict,
                     isinstance=isinstance):
        result = self.indirect_objects.get(key)
        if not isinstance(result, PdfIndirect):
            return result
        source = self.source
        offset = int(self.source.obj_offsets.get(key, '0'))
        if not offset:
            source.warning("Did not find PDF object %s", key)
            return None

        # Read the object header and validate it
        objnum, gennum = key
        source.floc = offset
        objid = source.multiple(3)
        ok = len(objid) == 3
        ok = ok and objid[0].isdigit() and int(objid[0]) == objnum
        ok = ok and objid[1].isdigit() and int(objid[1]) == gennum
        ok = ok and objid[2] == 'obj'
        if not ok:
            source.floc = offset
            source.next()
            objheader = '%d %d obj' % (objnum, gennum)
            fdata = source.fdata
            offset2 = (fdata.find('\n' + objheader) + 1 or
                       fdata.find('\r' + objheader) + 1)
            if (not offset2 or
                    fdata.find(fdata[offset2 - 1] + objheader, offset2) > 0):
                source.warning("Expected indirect object '%s'", objheader)
                return None
            source.warning("Indirect object %s found at incorrect "
                           "offset %d (expected offset %d)",
                           objheader, offset2, offset)
            source.floc = offset2 + len(objheader)

        # Read the object, and call special code if it starts
        # an array or dictionary
        obj = source.next()
        func = self.special.get(obj)
        if func is not None:
            obj = func(source)

        self.indirect_objects[key] = obj
        self.deferred_objects.remove(key)

        # Mark the object as indirect, and
        # just return it if it is a simple object.
        obj.indirect = key
        tok = source.next()
        if tok == 'endobj':
            return obj

        # Should be a stream.  Either that or it's broken.
        isdict = isinstance(obj, PdfDict)
        if isdict and tok == 'stream':
            self.readstream(obj, self.findstream(obj, tok, source), source)
            return obj

        # Houston, we have a problem, but let's see if it
        # is easily fixable.  Leaving out a space before endobj
        # is apparently an easy mistake to make on generation
        # (Because it won't be noticed unless you are specifically
        # generating an indirect object that doesn't end with any
        # sort of delimiter.)  It is so common that things like
        # okular just handle it.

        if isinstance(obj, PdfObject) and obj.endswith('endobj'):
            source.error('No space or delimiter before endobj')
            obj = PdfObject(obj[:-6])
        else:
            source.error("Expected 'endobj'%s token",
                         isdict and " or 'stream'" or '')
            obj = PdfObject('')

        obj.indirect = key
        self.indirect_objects[key] = obj
        return obj

    def read_all(self):
        deferred = self.deferred_objects
        prev = set()
        while 1:
            new = deferred - prev
            if not new:
                break
            prev |= deferred
            for key in new:
                self.loadindirect(key)

    def decrypt_all(self):
        self.read_all()

        if self.crypt_filters is not None:
            crypt.decrypt_objects(
                self.indirect_objects.values(), self.stream_crypt_filter,
                self.crypt_filters)

    def uncompress(self):
        self.read_all()

        uncompress(self.indirect_objects.values())

    def load_stream_objects(self, object_streams):
        # read object streams
        objs = []
        for num in object_streams:
            obj = self.findindirect(num, 0).real_value()
            assert obj.Type == '/ObjStm'
            objs.append(obj)

        # read objects from stream
        if objs:
            # Decrypt
            if self.crypt_filters is not None:
                crypt.decrypt_objects(
                    objs, self.stream_crypt_filter, self.crypt_filters)

            # Decompress
            uncompress(objs)

            for obj in objs:
                objsource = PdfTokens(obj.stream, 0, False)
                next = objsource.next
                offsets = []
                firstoffset = int(obj.First)
                while objsource.floc < firstoffset:
                    offsets.append((int(next()), firstoffset + int(next())))
                for num, offset in offsets:
                    # Read the object, and call special code if it starts
                    # an array or dictionary
                    objsource.floc = offset
                    sobj = next()
                    func = self.special.get(sobj)
                    if func is not None:
                        sobj = func(objsource)

                    key = (num, 0)
                    self.indirect_objects[key] = sobj
                    if key in self.deferred_objects:
                        self.deferred_objects.remove(key)

                    # Mark the object as indirect, and
                    # add it to the list of streams if it starts a stream
                    sobj.indirect = key

    def findxref(self, fdata):
        ''' Find the cross reference section at the end of a file
        '''
        startloc = fdata.rfind('startxref')
        if startloc < 0:
            raise PdfParseError('Did not find "startxref" at end of file')
        source = PdfTokens(fdata, startloc, False, self.verbose)
        tok = source.next()
        assert tok == 'startxref'  # (We just checked this...)
        tableloc = source.next_default()
        if not tableloc.isdigit():
            source.exception('Expected table location')
        if source.next_default().rstrip().lstrip('%') != 'EOF':
            source.exception('Expected %%EOF')
        return startloc, PdfTokens(fdata, int(tableloc), True, self.verbose)

    def parse_xref_stream(self, source, int=int, range=range,
                          enumerate=enumerate, islice=itertools.islice,
                          defaultdict=collections.defaultdict,
                          hexlify=binascii.hexlify):
        ''' Parse (one of) the cross-reference file section(s)
        '''

        def readint(s, lengths):
            offset = 0
            for length in itertools.cycle(lengths):
                next = offset + length
                yield int(hexlify(s[offset:next]), 16) if length else None
                offset = next

        setdefault = source.obj_offsets.setdefault
        next = source.next
        # check for xref stream object
        objid = source.multiple(3)
        ok = len(objid) == 3
        ok = ok and objid[0].isdigit()
        ok = ok and objid[1] == 'obj'
        ok = ok and objid[2] == '<<'
        if not ok:
            source.exception('Expected xref stream start')
        obj = self.readdict(source)
        if obj.Type != PdfName.XRef:
            source.exception('Expected dict type of /XRef')
        tok = next()
        self.readstream(obj, self.findstream(obj, tok, source), source, True)
        old_strm = obj.stream
        if not uncompress([obj], True):
            source.exception('Could not decompress Xref stream')
        stream = obj.stream
        # Fix for issue #76 -- goofy compressed xref stream
        # that is NOT ACTUALLY COMPRESSED
        stream = stream if stream is not old_strm else convert_store(old_strm)
        num_pairs = obj.Index or PdfArray(['0', obj.Size])
        num_pairs = [int(x) for x in num_pairs]
        num_pairs = zip(num_pairs[0::2], num_pairs[1::2])
        entry_sizes = [int(x) for x in obj.W]
        if len(entry_sizes) != 3:
            source.exception('Invalid entry size')
        object_streams = defaultdict(list)
        get = readint(stream, entry_sizes)
        for objnum, size in num_pairs:
            for cnt in range(size):
                xtype, p1, p2 = islice(get, 3)
                if xtype in (1, None):
                    if p1:
                        setdefault((objnum, p2 or 0), p1)
                elif xtype == 2:
                    object_streams[p1].append((objnum, p2))
                objnum += 1

        obj.private.object_streams = object_streams
        return obj

    def parse_xref_table(self, source, int=int, range=range):
        ''' Parse (one of) the cross-reference file section(s)
        '''
        setdefault = source.obj_offsets.setdefault
        next = source.next
        # plain xref table
        start = source.floc
        try:
            while 1:
                tok = next()
                if tok == 'trailer':
                    return
                startobj = int(tok)
                for objnum in range(startobj, startobj + int(next())):
                    offset = int(next())
                    generation = int(next())
                    inuse = next()
                    if inuse == 'n':
                        if offset != 0:
                            setdefault((objnum, generation), offset)
                    elif inuse != 'f':
                        raise ValueError
        except:
            pass
        try:
            # Table formatted incorrectly.
            # See if we can figure it out anyway.
            end = source.fdata.rindex('trailer', start)
            table = source.fdata[start:end].splitlines()
            for line in table:
                tokens = line.split()
                if len(tokens) == 2:
                    objnum = int(tokens[0])
                elif len(tokens) == 3:
                    offset, generation, inuse = (int(tokens[0]),
                                                 int(tokens[1]), tokens[2])
                    if offset != 0 and inuse == 'n':
                        setdefault((objnum, generation), offset)
                    objnum += 1
                elif tokens:
                    log.error('Invalid line in xref table: %s' %
                              repr(line))
                    raise ValueError
            log.warning('Badly formatted xref table')
            source.floc = end
            next()
        except:
            source.floc = start
            source.exception('Invalid table format')

    def parsexref(self, source):
        ''' Parse (one of) the cross-reference file section(s)
        '''
        next = source.next
        try:
            tok = next()
        except StopIteration:
            tok = ''
        if tok.isdigit():
            return self.parse_xref_stream(source), True
        elif tok == 'xref':
            self.parse_xref_table(source)
            tok = next()
            if tok != '<<':
                source.exception('Expected "<<" starting catalog')
            return self.readdict(source), False
        else:
            source.exception('Expected "xref" keyword or xref stream object')

    def readpages(self, node):
        pagename = PdfName.Page
        pagesname = PdfName.Pages
        catalogname = PdfName.Catalog
        typename = PdfName.Type
        kidname = PdfName.Kids

        try:
            result = []
            stack = [node]
            append = result.append
            pop = stack.pop
            while stack:
                node = pop()
                nodetype = node[typename]
                if nodetype == pagename:
                    append(node)
                elif nodetype == pagesname:
                    stack.extend(reversed(node[kidname]))
                elif nodetype == catalogname:
                    stack.append(node[pagesname])
                else:
                    log.error('Expected /Page or /Pages dictionary, got %s' %
                            repr(node))
            return result
        except (AttributeError, TypeError) as s:
            log.error('Invalid page tree: %s' % s)
            return []

    def _parse_encrypt_info(self, source, password, trailer):
        """Check password and initialize crypt filters."""
        # Create and check password key
        key = crypt.create_key(password, trailer)

        if not crypt.check_user_password(key, trailer):
            source.warning('User password does not validate')

        # Create default crypt filters
        private = self.private
        crypt_filters = self.crypt_filters
        version = int(trailer.Encrypt.V or 0)
        if version in (1, 2):
            crypt_filter = crypt.RC4CryptFilter(key)
            private.stream_crypt_filter = crypt_filter
            private.string_crypt_filter = crypt_filter
        elif version == 4:
            if PdfName.CF in trailer.Encrypt:
                for name, params in iteritems(trailer.Encrypt.CF):
                    if name == PdfName.Identity:
                        continue

                    cfm = params.CFM
                    if cfm == PdfName.AESV2:
                        crypt_filters[name] = crypt.AESCryptFilter(key)
                    elif cfm == PdfName.V2:
                        crypt_filters[name] = crypt.RC4CryptFilter(key)
                    else:
                        source.warning(
                            'Unsupported crypt filter: {}, {}'.format(
                                name, cfm))

            # Read default stream filter
            if PdfName.StmF in trailer.Encrypt:
                name = trailer.Encrypt.StmF
                if name in crypt_filters:
                    private.stream_crypt_filter = crypt_filters[name]
                else:
                    source.warning(
                        'Invalid crypt filter name in /StmF:'
                        ' {}'.format(name))

            # Read default string filter
            if PdfName.StrF in trailer.Encrypt:
                name = trailer.Encrypt.StrF
                if name in crypt_filters:
                    private.string_crypt_filter = crypt_filters[name]
                else:
                    source.warning(
                        'Invalid crypt filter name in /StrF:'
                        ' {}'.format(name))
        else:
            source.warning(
                'Unsupported Encrypt version: {}'.format(version))

    def __init__(self, fname=None, fdata=None, decompress=False,
                 decrypt=False, password='', disable_gc=True, verbose=True):
        self.private.verbose = verbose

        # Runs a lot faster with GC off.
        disable_gc = disable_gc and gc.isenabled()
        if disable_gc:
            gc.disable()

        try:
            if fname is not None:
                assert fdata is None
                # Allow reading preexisting streams like pyPdf
                if hasattr(fname, 'read'):
                    fdata = fname.read()
                else:
                    try:
                        f = open(fname, 'rb')
                        fdata = f.read()
                        f.close()
                    except IOError:
                        raise PdfParseError('Could not read PDF file %s' %
                                            fname)

            assert fdata is not None
            fdata = convert_load(fdata)

            if not fdata.startswith('%PDF-'):
                startloc = fdata.find('%PDF-')
                if startloc >= 0:
                    log.warning('PDF header not at beginning of file')
                else:
                    lines = fdata.lstrip().splitlines()
                    if not lines:
                        raise PdfParseError('Empty PDF file!')
                    raise PdfParseError('Invalid PDF header: %s' %
                                        repr(lines[0]))

            self.private.version = fdata[5:8]

            endloc = fdata.rfind('%EOF')
            if endloc < 0:
                raise PdfParseError('EOF mark not found: %s' %
                                    repr(fdata[-20:]))
            endloc += 6
            junk = fdata[endloc:]
            fdata = fdata[:endloc]
            if junk.rstrip('\00').strip():
                log.warning('Extra data at end of file')

            private = self.private
            private.indirect_objects = {}
            private.deferred_objects = set()
            private.special = {'<<': self.readdict,
                               '[': self.readarray,
                               'endobj': self.empty_obj,
                               }
            for tok in r'\ ( ) < > { } ] >> %'.split():
                self.special[tok] = self.badtoken

            startloc, source = self.findxref(fdata)
            private.source = source

            # Find all the xref tables/streams, and
            # then deal with them backwards.
            xref_list = []
            while 1:
                source.obj_offsets = {}
                trailer, is_stream = self.parsexref(source)
                prev = trailer.Prev
                if prev is None:
                    token = source.next()
                    if token != 'startxref' and not xref_list:
                        source.warning('Expected "startxref" '
                                       'at end of xref table')
                    break
                xref_list.append((source.obj_offsets, trailer, is_stream))
                source.floc = int(prev)

            # Handle document encryption
            private.crypt_filters = None
            if decrypt and PdfName.Encrypt in trailer:
                identity_filter = crypt.IdentityCryptFilter()
                crypt_filters = {
                    PdfName.Identity: identity_filter
                }
                private.crypt_filters = crypt_filters
                private.stream_crypt_filter = identity_filter
                private.string_crypt_filter = identity_filter

                if not crypt.HAS_CRYPTO:
                    raise PdfParseError(
                        'Install PyCrypto to enable encryption support')

                self._parse_encrypt_info(source, password, trailer)

            if is_stream:
                self.load_stream_objects(trailer.object_streams)

            while xref_list:
                later_offsets, later_trailer, is_stream = xref_list.pop()
                source.obj_offsets.update(later_offsets)
                if is_stream:
                    trailer.update(later_trailer)
                    self.load_stream_objects(later_trailer.object_streams)
                else:
                    trailer = later_trailer

            trailer.Prev = None

            if (trailer.Version and
                    float(trailer.Version) > float(self.version)):
                self.private.version = trailer.Version

            if decrypt:
                self.decrypt_all()
                trailer.Encrypt = None

            if is_stream:
                self.Root = trailer.Root
                self.Info = trailer.Info
                self.ID = trailer.ID
                self.Size = trailer.Size
                self.Encrypt = trailer.Encrypt
            else:
                self.update(trailer)

            # self.read_all_indirect(source)
            private.pages = self.readpages(self.Root)
            if decompress:
                self.uncompress()

            # For compatibility with pyPdf
            private.numPages = len(self.pages)
        finally:
            if disable_gc:
                gc.enable()

    # For compatibility with pyPdf
    def getPage(self, pagenum):
        return self.pages[pagenum]
