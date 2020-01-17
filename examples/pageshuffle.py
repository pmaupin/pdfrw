#!/usr/bin/python3
#PYTHON_ARGCOMPLETE_OK

import argparse
parser = argparse.ArgumentParser(description='pdf modification utility')
subparsers = parser.add_subparsers(title='subcommands')

parser_pdftk = subparsers.add_parser('pdftk', help='utility')
parser_pdftk_group = parser_pdftk.add_mutually_exclusive_group(required=True)
parser_pdftk_group.add_argument('-f', '--form', action='store_true', help='dump_data_fields_utf8')
parser_pdftk_group.add_argument('-o', '--output', action='store_true', help='dump_data_utf8')
parser_pdftk_group.add_argument('-i', '--input', metavar='I', help='update_info_utf8')
parser_pdftk_group.add_argument('-r', '--repair', action='store_true',
                                help='flatten drop_xfa drop_xmp compress')
parser_pdftk_group.add_argument('-u', '--uncompress', action='store_true',
                                help='flatten drop_xfa drop_xmp uncompress')
parser_pdftk.add_argument('document')

parser_scan = subparsers.add_parser('scan', help='image')
parser_scan.add_argument('-c', '--color', action='store_true', help='[default=gray]')
parser_scan.add_argument('-r', '--resolution', type=int, metavar='R', help='dpi [default=300]')
parser_scan_group = parser_scan.add_mutually_exclusive_group()
parser_scan_group.add_argument('-s', '--size', choices=('A4', 'LT'), default='A4', help='[default=A4]')
parser_scan_group.add_argument('-f', '--file', nargs='*')

parser_insert = subparsers.add_parser('insert', help='merge')
parser_insert.add_argument('-p', '--page', type=int, required=True, metavar='P')
parser_insert.add_argument('-i', '--input', required=True, metavar='I')
parser_insert.add_argument('document')

parser_extract = subparsers.add_parser('extract', help='delete')
parser_extract.add_argument('-d', '--delete', action='store_true')
parser_extract.add_argument('-p', '--page', required=True, metavar='P', help='p[-p] end is 0')
parser_extract.add_argument('-o', '--output', metavar='O')
parser_extract.add_argument('document')

parser_mark = subparsers.add_parser('mark', help='book')
parser_mark.add_argument('-o', '--operation',
                         choices=('insert','delete','rename','shift','list'), required=True)
parser_mark.add_argument('-p', '--page', metavar='P', help='p[-p] end is 0')
parser_mark.add_argument('-l', '--level', type=int, metavar='L', help='offset or increment')
parser_mark.add_argument('-b', '--before', metavar='B', help='previous title or insert before (blank for first)')
parser_mark.add_argument('-t', '--title', metavar='T', help='destination title')
parser_mark.add_argument('document')

parser_utility = subparsers.add_parser('utility')
parser_utility.add_argument('-f', '--field', action='store_true', help='dump')
parser_utility.add_argument('document')

#the argcomplete call needs to come as early as possible to make tabs responsive
'''
sudo apt install python-pip python3-pip
sudo -H pip install argcomplete
sudo -H pip3 install argcomplete
sudo activate-global-python-argcomplete
'''
#but, ignore the error if not installed
try: import argcomplete ; argcomplete.autocomplete(parser)
except ImportError: pass

import pdfrw # sudo -H pip3 install pdfrw
import glob
import os
import re
import subprocess
import types

def subcommand_pdftk(args):
    # sudo apt install pdftk
    if args.form: subprocess.run([
            'pdftk', args.document, 'dump_data_fields_utf8',
    ], check=True)
    # signature: "/Type /Sig", annotation: "/Type /Annot" "/Subtype /Widget" "/FT /Sig"

    elif args.output: subprocess.run([
            'pdftk', args.document, 'dump_data_utf8',
    ], check=True)

    elif args.input:
        bak_name = args.document + '.0'
        os.replace(args.document, bak_name)
        subprocess.run([
            'pdftk', bak_name, 'update_info_utf8', args.input, 'output', args.document,
        ], check=True)

    elif args.repair or args.uncompress:
        bak_name = args.document + '.0'
        os.replace(args.document, bak_name)
        subprocess.run([
            'pdftk', bak_name, 'output', args.document,
            'flatten', 'drop_xfa', 'drop_xmp',
            'uncompress' if args.uncompress else 'compress',
        ], check=True)
parser_pdftk.set_defaults(func=subcommand_pdftk)

def subcommand_scan(args):
    if not args.file:
        # A4: 598 842 = 210x297mm = 8.3×11.7in (1.41)
        # LT: 612 792 = 215.9×279.4mm = 8.5x11in (1.30)
        geometry = '-x 210 -y 297' if args.size == 'A4' else '-x 216 -y 279'
        resolution = '--resolution ' + ('300' if args.resolution is None else str(args.resolution))
        color = '--mode gray' if not args.color else '--mode color'

        name = "pdfScan" ; index = 0
        try:
            while next(glob.iglob(name + str(index) + '*')): index += 1
        except StopIteration: pass
        name += str(index)

        # sudo apt install sane-utils
        subprocess.run((
            'scanimage --format tiff ' + resolution + ' ' + color + ' ' + geometry
            + ' --batch=' + name + '_%02d.tif --batch-prompt --progress --verbose'
        ).split(), check=True)
        files = glob.glob(name + '_*.tif')
        files.sort()
        output = name + '.pdf'
    else:
        files = args.file
        output = files[0] + '.pdf'

    if not files: return
    process_post = '-threshold 67% -monochrome -compress group4' if not args.color else \
                   '-compress jpeg'
    process_pre = '-density 300' if not args.resolution else \
                  '-density ' + str(args.resolution) + 'x' + str(args.resolution)
    # sudo apt install imagemagick
    # -crop 2550x3300+0+0 ;# crop to 8.5" x 11" assuming 300 dpi
    # -crop 2480x3508+0+0 ;# crop to 210mm x 297mm assuming 300 dpi
    subprocess.run((
        'convert ' + ''.join('( ' + process_pre + ' ' + v + ' ' + process_post + ' ) '
                             for v in files) + output
    ).split(), check=True)
parser_scan.set_defaults(func=subcommand_scan)

class PdfBookmarks():

    def __init__(self, reader=None):
        self.pagecount = 0
        self.mark = []
        if not reader: return
        self.pagecount = len(reader.pages)
        if not reader.Root.Outlines: return

        def outline_walk(elt, level=0):
            # walk the document's outline tree
            while True:
                if hasattr(elt, 'Title') and elt.Title:
                    yield elt, level
                if hasattr(elt, 'First') and elt.First:
                    for ret in outline_walk(elt.First, level + 1):
                        yield ret
                if hasattr(elt, 'Next') and elt.Next:
                    elt = elt.Next
                else:
                    break

        def name_look(name, names=None):
            # search document catalog for a named destination
            if names is None: names = reader.Root.Names.Dests
            if hasattr(names, 'Names') and not names.Names is None:
                for n, p in zip(names.Names[0::2], names.Names[1::2]):
                    if n == name: return p
            if hasattr(names, 'Kids') and not names.Kids is None:
                for k in names.Kids:
                    p = name_look(name, k)
                    if not p is None: return p
            return None

        def import_dest(dest, level, title):
            if isinstance(dest, pdfrw.objects.pdfstring.PdfString):
                # dest as a named destination
                dest = name_look(dest)
            if isinstance(dest, pdfrw.objects.pdfdict.PdfDict):
                # dest as a dictionary
                dest = dest.D
            if isinstance(dest, pdfrw.objects.pdfarray.PdfArray):
                # page is in dest[0]
                for page in range(0, len(reader.pages)):
                    if reader.pages[page] is dest[0]:
                        self.mark.append(types.SimpleNamespace(
                            level=level, page=page, title=title))
                        break

        for elt, level in outline_walk(reader.Root.Outlines.First):
            title=elt.Title.to_unicode()
            if not elt.Dest is None:
                # dest can be in the outline itself
                import_dest(elt.Dest, level, title)
            elif hasattr(elt, 'A') and hasattr(elt.A, 'S') \
                 and elt.A.S == pdfrw.objects.pdfname.PdfName('GoTo') \
                 and hasattr(elt.A, 'D'):
                # dest can be in a GoTo action in the outline
                import_dest(elt.A.D, level, title)
            else:
                print('Missing destination:', title)
        self.mark.sort(key=lambda t: t.page)

    def export_outlines(self, writer):
        if not self.mark: return
        root = writer._get_trailer().Root
        elt = root.Outlines = pdfrw.objects.pdfdict.PdfDict()
        elt.indirect = True
        level = -1
        for m in self.mark:
            if m.level > level:
                for _ in range(m.level - level):
                    elt.First = pdfrw.objects.pdfdict.PdfDict(Parent=elt)
                    elt = elt.First
                    elt.indirect = True
            elif m.level < level:
                for _ in range(level - m.level):
                    elt.Parent.Last = elt
                    elt = elt.Parent
            if m.level <= level:
                elt.Next = pdfrw.objects.pdfdict.PdfDict(Parent=elt.Parent, Prev=elt)
                elt = elt.Next
                elt.indirect = True
            level = m.level
            elt.Title=pdfrw.objects.pdfstring.PdfString \
                       (pdfrw.objects.pdfstring.PdfString.from_unicode(m.title))
            elt.Dest=pdfrw.objects.pdfarray.PdfArray \
                      ([writer.pagearray[m.page], pdfrw.objects.pdfname.PdfName('XYZ')])
        for _ in range(level + 1):
            elt.Parent.Last = elt
            elt = elt.Parent

    def format(self):
        return ''.join(str(m.page) + '.' + str(m.level) + ' ' + m.title + '\n' for m in self.mark)

    def add(self, page, title, level, before):
        self.mark.insert(next((
            i for i, m in enumerate(self.mark) if m.page > page
            or (m.page == page and before is not None
                and (before == '' or m.title == before))), len(self.mark)),
            types.SimpleNamespace(level=level, page=page, title=title))

    def remove(self, page, title, level):
        self.mark = [m for m in self.mark if not
                     (m.page >= page.start and m.page < page.stop
                      and (level is None or m.level == level)
                      and (title is None or m.title == title))]

    def rename(self, page, title, level, before):
        for m in self.mark:
            if m.page >= page.start and m.page < page.stop \
               and (level is None or m.level == level) \
               and (before is None or m.title == before):
                m.title = title

    def shift(self, page, title, level):
        for m in self.mark:
            if m.page >= page.start and m.page < page.stop \
               and (title is None or m.title == title):
                m.level += level

    def merge(self, bookmarks, page):
        index = None
        for i, m in enumerate(self.mark):
            if index is None and m.page >= page:
                # insert before this
                index = i
            if index is not None:
                # increase the page numbers after the insert
                m.page += bookmarks.pagecount
        if index is None: index = self.pagecount
        # copy bookmarks and increase the inserted page numbers
        insert = [types.SimpleNamespace(**n.__dict__) for n in bookmarks.mark]
        for m in insert: m.page += page
        self.pagecount += bookmarks.pagecount
        self.mark[index:index] = insert

    def extract(self, page, delete):
        result = PdfBookmarks()
        result.pagecount = page.stop - page.start
        index = None
        for i, m in enumerate(self.mark):
            if index is None and m.page >= page.start:
                # remove starting here
                index = slice(i, None)
            if index is not None and index.stop is None and m.page >= page.stop:
                # stop remove on previous index
                index = slice(index.start, i)
            if index is not None and index.stop is not None and delete:
                # decrease the page numbers after the delete
                m.page -= result.pagecount
        if delete and index:
            # take the source bookmarks
            result.mark = self.mark[index]
            del self.mark[index]
        elif index is not None:
            # copy the source bookmarks
            result.mark = [types.SimpleNamespace(**n.__dict__) for n in self.mark[index]]
        # decrease the page numbers of the delete
        for m in result.mark: m.page -= page.start
        return result

def PdfReader(document):
    doc_reader = pdfrw.PdfReader(document)
    if hasattr(doc_reader.Root, 'AcroForm') and doc_reader.Root.AcroForm \
       and doc_reader.Root.AcroForm.Fields:
        raise SystemExit('error AcroForm in ' + document)
    return doc_reader

def subcommand_insert(args):
    # open inputs
    doc_reader = PdfReader(args.document)
    doc_mark = PdfBookmarks(doc_reader)
    arg_reader = PdfReader(args.input)
    arg_mark = PdfBookmarks(arg_reader)

    # check arguments
    arg_page = args.page - 1
    if arg_page == -1: arg_page = len(doc_reader.pages)
    if arg_page < 0 or arg_page > len(doc_reader.pages):
        parser_insert.error('page number')

    # do operations
    doc_mark.merge(arg_mark, arg_page)

    # write output
    writer = pdfrw.PdfWriter()
    writer.addpages(doc_reader.pages[:arg_page])
    writer.addpages(arg_reader.pages)
    writer.addpages(doc_reader.pages[arg_page:])
    doc_mark.export_outlines(writer)
    writer.write(args.document + '.1')

    # swap new document with backup
    os.replace(args.document, args.document + '.0')
    os.replace(args.document + '.1', args.document)
parser_insert.set_defaults(func=subcommand_insert)

def subcommand_extract(args):
    # open inputs
    doc_reader = PdfReader(args.document)
    doc_mark = PdfBookmarks(doc_reader)

    # check arguments
    re_page = re.compile(r'^(?P<page0>\d+)(-(?P<page1>\d+))?$')
    arg_page = re_page.match(args.page)
    if arg_page:
        # convert to slice indicies, arg[1]==0 means through last page
        arg_page = (int(arg_page.group('page0'))-1, arg_page.group('page1'))
        arg_page = slice(arg_page[0], int(arg_page[1]) if arg_page[1] else arg_page[0]+1)
    # handle through last page case
    if arg_page and arg_page.stop == 0:
        arg_page = slice(arg_page.start, len(doc_reader.pages))
    if not arg_page or arg_page.start >= arg_page.stop \
       or arg_page.start < 0 or arg_page.start >= len(doc_reader.pages) \
       or arg_page.stop <= 0 or arg_page.stop > len(doc_reader.pages):
        parser_extract.error('page number')
    arg_mark = doc_mark.extract(arg_page, args.delete)

    # write output
    if args.output:
        writer = pdfrw.PdfWriter()
        for i in range(arg_page.start,arg_page.stop):
            writer.addPage(doc_reader.getPage(i))
        arg_mark.export_outlines(writer)
        with open(args.output, 'wb') as stream:
            writer.write(stream)

    if args.delete:
        writer = pdfrw.PdfWriter()
        for i in range(0, arg_page.start):
            writer.addPage(doc_reader.getPage(i))
        for i in range(arg_page.stop, len(doc_reader.pages)):
            writer.addPage(doc_reader.getPage(i))
        doc_mark.export_outlines(writer)
        with open(args.document + '.1', 'wb') as stream:
            writer.write(stream)

    # swap new document with backup
    if args.delete:
        os.replace(args.document, args.document + '.0')
        os.replace(args.document + '.1', args.document)
parser_extract.set_defaults(func=subcommand_extract)

def subcommand_mark(args):
    # open inputs
    doc_reader = PdfReader(args.document)
    doc_mark = PdfBookmarks(doc_reader)

    # check arguments
    if args.operation != 'shift' and args.level is not None: args.level -= 1
    if args.operation == 'insert':
        arg_page = int(args.page) - 1 if args.page is not None else None
        if args.level is None: args.level = 0
        if arg_page is None or arg_page < 0 or arg_page >= len(doc_reader.pages):
            parser_mark.error('page number')
        if args.title is None:
            parser_mark.error('title')
    elif args.page is not None:
        re_page = re.compile(r'^(?P<page0>\d+)(-(?P<page1>\d+))?$')
        arg_page = re_page.match(args.page)
        if arg_page:
            # convert to slice indicies, arg[1]==0 means through last page
            arg_page = (int(arg_page.group('page0'))-1, arg_page.group('page1'))
            arg_page = slice(arg_page[0], int(arg_page[1]) if arg_page[1] else arg_page[0]+1)
        # handle through last page case
        if arg_page and arg_page.stop == 0:
            arg_page = slice(arg_page.start, len(doc_reader.pages))
        if not arg_page or arg_page.start >= arg_page.stop \
           or arg_page.start < 0 or arg_page.start >= len(doc_reader.pages) \
           or arg_page.stop <= 0 or arg_page.stop > len(doc_reader.pages):
            parser_mark.error('page number')
    else:
        arg_page = slice(0, len(doc_reader.pages))

    # do operations
    if args.operation == 'insert':
        doc_mark.add(arg_page, args.title, args.level, args.before)
    elif args.operation == 'delete':
        doc_mark.remove(arg_page, args.title, args.level)
    elif args.operation == 'rename':
        doc_mark.rename(arg_page, args.title, args.level, args.before)
    elif args.operation == 'shift':
        doc_mark.shift(arg_page, args.title, args.level)
    elif args.operation == 'list':
        print(doc_mark.extract(arg_page, False).format())
        return

    # write outputs
    writer = pdfrw.PdfWriter()
    for i in range(len(doc_reader.pages)):
        writer.addPage(doc_reader.getPage(i))
    doc_mark.export_outlines(writer)
    with open(args.document + '.1', 'wb') as stream:
        writer.write(stream)

    # swap new document with backup
    os.replace(args.document, args.document + '.0')
    os.replace(args.document + '.1', args.document)
parser_mark.set_defaults(func=subcommand_mark)

def subcommand_utility(args):
    # open inputs
    doc_reader = pdfrw.PdfReader(args.document)

    if hasattr(doc_reader.Root, 'AcroForm') and doc_reader.Root.AcroForm:
        for field in doc_reader.Root.AcroForm.Fields:
            print(field)
parser_utility.set_defaults(func=subcommand_utility)

# run the command
args = parser.parse_args()
if hasattr(args, 'func'): raise SystemExit(args.func(args))
import __main__ ; print(os.path.basename(__main__.__file__) + ': -h for help')
# fall through when there is no function
