# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2009 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
This file is an example parser that will parse a graphics stream
into a reportlab canvas.

Needs work on fonts and unicode, but works on a few PDFs.

Better to use Form XObjects for most things (see the example in rl1).

'''
from inspect import getargspec

from pdfrw import PdfTokens
from pdfrw.objects import PdfString

#############################################################################
# Graphics parsing


def parse_array(self, token='[', params=None):
    mylist = []
    for token in self.tokens:
        if token == ']':
            break
        mylist.append(token)
    self.params.append(mylist)


def parse_savestate(self, token='q', params=''):
    self.canv.saveState()


def parse_restorestate(self, token='Q', params=''):
    self.canv.restoreState()


def parse_transform(self, token='cm', params='ffffff'):
    self.canv.transform(*params)


def parse_linewidth(self, token='w', params='f'):
    self.canv.setLineWidth(*params)


def parse_linecap(self, token='J', params='i'):
    self.canv.setLineCap(*params)


def parse_linejoin(self, token='j', params='i'):
    self.canv.setLineJoin(*params)


def parse_miterlimit(self, token='M', params='f'):
    self.canv.setMiterLimit(*params)


def parse_dash(self, token='d', params='as'):  # Array, string
    self.canv.setDash(*params)


def parse_intent(self, token='ri', params='n'):
    # TODO: add logging
    pass


def parse_flatness(self, token='i', params='i'):
    # TODO: add logging
    pass


def parse_gstate(self, token='gs', params='n'):
    # TODO: add logging
    # Could parse stuff we care about from here later
    pass


def parse_move(self, token='m', params='ff'):
    if self.gpath is None:
        self.gpath = self.canv.beginPath()
    self.gpath.moveTo(*params)
    self.current_point = params


def parse_line(self, token='l', params='ff'):
    self.gpath.lineTo(*params)
    self.current_point = params


def parse_curve(self, token='c', params='ffffff'):
    self.gpath.curveTo(*params)
    self.current_point = params[-2:]


def parse_curve1(self, token='v', params='ffff'):
    parse_curve(self, token, tuple(self.current_point) + tuple(params))


def parse_curve2(self, token='y', params='ffff'):
    parse_curve(self, token, tuple(params) + tuple(params[-2:]))


def parse_close(self, token='h', params=''):
    self.gpath.close()


def parse_rect(self, token='re', params='ffff'):
    if self.gpath is None:
        self.gpath = self.canv.beginPath()
    self.gpath.rect(*params)
    self.current_point = params[-2:]


def parse_stroke(self, token='S', params=''):
    finish_path(self, 1, 0, 0)


def parse_close_stroke(self, token='s', params=''):
    self.gpath.close()
    finish_path(self, 1, 0, 0)


def parse_fill(self, token='f', params=''):
    finish_path(self, 0, 1, 1)


def parse_fill_compat(self, token='F', params=''):
    finish_path(self, 0, 1, 1)


def parse_fill_even_odd(self, token='f*', params=''):
    finish_path(self, 0, 1, 0)


def parse_fill_stroke_even_odd(self, token='B*', params=''):
    finish_path(self, 1, 1, 0)


def parse_fill_stroke(self, token='B', params=''):
    finish_path(self, 1, 1, 1)


def parse_close_fill_stroke_even_odd(self, token='b*', params=''):
    self.gpath.close()
    finish_path(self, 1, 1, 0)


def parse_close_fill_stroke(self, token='b', params=''):
    self.gpath.close()
    finish_path(self, 1, 1, 1)


def parse_nop(self, token='n', params=''):
    finish_path(self, 0, 0, 0)


def finish_path(self, stroke, fill, fillmode):
    if self.gpath is not None:
        canv = self.canv
        canv._fillMode, oldmode = fillmode, canv._fillMode
        canv.drawPath(self.gpath, stroke, fill)
        canv._fillMode = oldmode
        self.gpath = None


def parse_clip_path(self, token='W', params=''):
    # TODO: add logging
    pass


def parse_clip_path_even_odd(self, token='W*', params=''):
    # TODO: add logging
    pass


def parse_stroke_gray(self, token='G', params='f'):
    self.canv.setStrokeGray(*params)


def parse_fill_gray(self, token='g', params='f'):
    self.canv.setFillGray(*params)


def parse_stroke_rgb(self, token='RG', params='fff'):
    self.canv.setStrokeColorRGB(*params)


def parse_fill_rgb(self, token='rg', params='fff'):
    self.canv.setFillColorRGB(*params)


def parse_stroke_cmyk(self, token='K', params='ffff'):
    self.canv.setStrokeColorCMYK(*params)


def parse_fill_cmyk(self, token='k', params='ffff'):
    self.canv.setFillColorCMYK(*params)

#############################################################################
# Text parsing


def parse_begin_text(self, token='BT', params=''):
    assert self.tpath is None
    self.tpath = self.canv.beginText()


def parse_text_transform(self, token='Tm', params='ffffff'):
    path = self.tpath

    # Stoopid optimization to remove nop
    try:
        code = path._code
    except AttributeError:
        pass
    else:
        if code[-1] == '1 0 0 1 0 0 Tm':
            code.pop()

    path.setTextTransform(*params)


def parse_setfont(self, token='Tf', params='nf'):
    fontinfo = self.fontdict[params[0]]
    self.tpath._setFont(fontinfo.name, params[1])
    self.curfont = fontinfo


def parse_text_out(self, token='Tj', params='t'):
    text = params[0].decode(self.curfont.remap, self.curfont.twobyte)
    self.tpath.textOut(text)

def parse_lf_text_out(self, token="'", params='t'):
    self.tpath.textLine()
    text = params[0].decode(self.curfont.remap, self.curfont.twobyte)
    self.tpath.textOut(text)


def parse_lf_text_out_with_spacing(self, token='"', params='fft'):
    self.tpath.setWordSpace(params[0])
    self.tpath.setCharSpace(params[1])
    self.tpath.textLine()
    text = params[2].decode(self.curfont.remap, self.curfont.twobyte)
    self.tpath.textOut(text)


def parse_TJ(self, token='TJ', params='a'):
    remap = self.curfont.remap
    twobyte = self.curfont.twobyte
    result = []
    for x in params[0]:
        if isinstance(x, PdfString):
            result.append(x.decode(remap, twobyte))
        else:
            # TODO: Adjust spacing between characters here
            int(x)
    text = ''.join(result)
    self.tpath.textOut(text)


def parse_end_text(self, token='ET', params=''):
    assert self.tpath is not None
    self.canv.drawText(self.tpath)
    self.tpath = None


def parse_move_cursor(self, token='Td', params='ff'):
    self.tpath.moveCursor(params[0], -params[1])


def parse_set_leading(self, token='TL', params='f'):
    self.tpath.setLeading(*params)


def parse_text_line(self, token='T*', params=''):
    self.tpath.textLine()


def parse_set_char_space(self, token='Tc', params='f'):
    self.tpath.setCharSpace(*params)


def parse_set_word_space(self, token='Tw', params='f'):
    self.tpath.setWordSpace(*params)


def parse_set_hscale(self, token='Tz', params='f'):
    self.tpath.setHorizScale(params[0] - 100)


def parse_set_rise(self, token='Ts', params='f'):
    self.tpath.setRise(*params)


def parse_xobject(self, token='Do', params='n'):
    # TODO: Need to do this
    pass


class FontInfo(object):
    ''' Pretty basic -- needs a lot of work to work right for all fonts
    '''
    lookup = {
                # WRONG -- have to learn about font stuff...
                'BitstreamVeraSans': 'Helvetica',
             }

    def __init__(self, source):
        name = source.BaseFont[1:]
        self.name = self.lookup.get(name, name)
        self.remap = chr
        self.twobyte = False
        info = source.ToUnicode
        if not info:
            return
        info = info.stream.split('beginbfchar')[1].split('endbfchar')[0]
        info = list(PdfTokens(info))
        assert not len(info) & 1
        info2 = []
        for x in info:
            assert x[0] == '<' and x[-1] == '>' and len(x) in (4, 6), x
            i = int(x[1:-1], 16)
            info2.append(i)
        self.remap = dict((x, chr(y)) for (x, y) in
                          zip(info2[::2], info2[1::2])).get
        self.twobyte = len(info[0]) > 4

#############################################################################
# Control structures


def findparsefuncs():

    def checkname(n):
        assert n.startswith('/')
        return n

    def checkarray(a):
        assert isinstance(a, list), a
        return a

    def checktext(t):
        assert isinstance(t, PdfString)
        return t

    fixparam = dict(f=float, i=int, n=checkname, a=checkarray,
                    s=str, t=checktext)
    fixcache = {}

    def fixlist(params):
        try:
            result = fixcache[params]
        except KeyError:
            result = tuple(fixparam[x] for x in params)
            fixcache[params] = result
        return result

    dispatch = {}
    expected_args = 'self token params'.split()
    for key, func in globals().items():
        if key.startswith('parse_'):
            args, varargs, keywords, defaults = getargspec(func)
            assert (args == expected_args and varargs is None and
                    keywords is None and len(defaults) == 2), (
                    key, args, varargs, keywords, defaults)
            token, params = defaults
            if params is not None:
                params = fixlist(params)
            value = func, params
            assert dispatch.setdefault(token, value) is value, repr(token)
    return dispatch


class _ParseClass(object):
    dispatch = findparsefuncs()

    @classmethod
    def parsepage(cls, page, canvas=None):
        self = cls()
        contents = page.Contents
        if contents.Filter is not None:
            raise SystemExit('Cannot parse graphics -- page encoded with %s'
                             % contents.Filter)
        dispatch = cls.dispatch.get
        self.tokens = tokens = iter(PdfTokens(contents.stream))
        self.params = params = []
        self.canv = canvas
        self.gpath = None
        self.tpath = None
        self.fontdict = dict((x, FontInfo(y)) for
                             (x, y) in page.Resources.Font.items())

        for token in self.tokens:
            info = dispatch(token)
            if info is None:
                params.append(token)
                continue
            func, paraminfo = info
            if paraminfo is None:
                func(self, token, ())
                continue
            delta = len(params) - len(paraminfo)
            if delta:
                if delta < 0:
                    print ('Operator %s expected %s parameters, got %s' %
                           (token, len(paraminfo), params))
                    params[:] = []
                    continue
                else:
                    print ("Unparsed parameters/commands: %s" % params[:delta])
                del params[:delta]
            paraminfo = zip(paraminfo, params)
            try:
                params[:] = [x(y) for (x, y) in paraminfo]
            except:
                for i, (x, y) in enumerate(paraminfo):
                    try:
                        x(y)
                    except:
                        raise  # For now
                    continue
            func(self, token, params)
            params[:] = []


def debugparser(undisturbed=set('parse_array'.split())):
    def debugdispatch():
        def getvalue(oldval):
            name = oldval[0].__name__

            def myfunc(self, token, params):
                print ('%s called %s(%s)' % (token, name,
                       ', '.join(str(x) for x in params)))
            if name in undisturbed:
                myfunc = oldval[0]
            return myfunc, oldval[1]
        return dict((x, getvalue(y))
                    for (x, y) in _ParseClass.dispatch.items())

    class _DebugParse(_ParseClass):
        dispatch = debugdispatch()

    return _DebugParse.parsepage

parsepage = _ParseClass.parsepage

if __name__ == '__main__':
    import sys
    from pdfrw import PdfReader
    parse = debugparser()
    fname, = sys.argv[1:]
    pdf = PdfReader(fname, decompress=True)
    for i, page in enumerate(pdf.pages):
        print ('\nPage %s ------------------------------------' % i)
        parse(page)
