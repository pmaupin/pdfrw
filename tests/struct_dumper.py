#! /usr/bin/env python

import sys
import pdfrw


def go(fname):
    def output(*stuff):
        outlist.append(stuff)

    PdfDict = pdfrw.PdfDict
    PdfArray = pdfrw.PdfArray
    allobjs = {}
    outlist = []
    q = []
    queue = q.append
    queue(('', pdfrw.PdfReader(fname)))

    for name, obj in q:
        prior = allobjs.setdefault(id(obj), name)
        if prior is not name:
            output(name, '-->', prior)
        elif isinstance(obj, PdfArray):
            objlen = len(obj)
            digits = 1 if objlen < 10 else (2 if objlen < 100 else 3)
            fmt = name + '[%%0%dd]' % digits
            for i, subobj in enumerate(obj):
                queue((fmt % i, subobj))
            output(name, ':', len(obj), 'entry array')
        elif isinstance(obj, PdfDict):
            for key, subobj in obj.items():
                if not key.startswith('/'):
                    key = '.' + key
                queue((name + key, subobj))
            output(name, ':', len(obj), 'entry dict')
        else:
            value = repr(obj)
            room = max(120 - len(name), 20)
            if len(value) > room:
                value = value[:room-4] + ' ...'
            output(name, '=', value)

    for line in sorted(outlist):
        print ' '.join((str(x) for x in line))

if __name__ == '__main__':
    argv = sys.argv[1:]
    flags = set(x for x in argv if x.startswith('-'))
    fname, = [x for x in argv if x not in flags]
    roundtrip = flags == set(['-r'])
    assert roundtrip or not flags
    if roundtrip:
        trailer = pdfrw.PdfReader(fname)
        fname = 'scratch.pdf'
        out = pdfrw.PdfWriter()
        out.addpages(trailer.pages)
        out.write(fname)
    go(fname)
