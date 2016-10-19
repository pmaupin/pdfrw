# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2015 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

'''
This module contains code to edit pages.  Sort of a canvas, I
suppose, but I wouldn't want to call it that and get people all
excited or anything.

No, this is just for doing basic things like merging/splitting
apart pages, watermarking, etc.  All it does is allow converting
pages (or parts of pages) into Form XObject rectangles, and then
plopping those down on new or pre-existing pages.
'''

from .objects import PdfDict, PdfArray, PdfName
from .buildxobj import pagexobj, ViewInfo

NullInfo = ViewInfo()


class RectXObj(PdfDict):
    ''' This class facilitates doing positioning (moving and scaling)
        of Form XObjects within their containing page, by modifying
        the Form XObject's transformation matrix.

        By default, this class keeps the aspect ratio locked.  For
        example, if your object is foo, you can write 'foo.w = 200',
        and it will scale in both the x and y directions.

        To unlock the aspect ration, you have to do a tiny bit of math
        and call the scale function.
    '''
    def __init__(self, page, viewinfo=NullInfo, **kw):
        ''' The page is a page returned by PdfReader.  It will be
            turned into a cached Form XObject (so that multiple
            rectangles can be extracted from it if desired), and then
            another Form XObject will be built using it and the viewinfo
            (which should be a ViewInfo class).  The viewinfo includes
            source coordinates (from the top/left) and rotation information.

            Once the object has been built, its destination coordinates
            may be examined and manipulated by using x, y, w, h, and
            scale.  The destination coordinates are in the normal
            PDF programmatic system (starting at bottom left).
        '''
        if kw:
            if viewinfo is not NullInfo:
                raise ValueError("Cannot modify preexisting ViewInfo")
            viewinfo = ViewInfo(**kw)
        viewinfo.cacheable = False
        base = pagexobj(page, viewinfo)
        self.update(base)
        self.indirect = True
        self.stream = base.stream
        private = self.private
        private._rect = [base.x, base.y, base.w, base.h]
        matrix = self.Matrix
        if matrix is None:
            matrix = self.Matrix = PdfArray((1, 0, 0, 1, 0, 0))
        private._matrix = matrix  # Lookup optimization
        # Default to lower-left corner
        self.x = 0
        self.y = 0

    @property
    def x(self):
        ''' X location (from left) of object in points
        '''
        return self._rect[0]

    @property
    def y(self):
        ''' Y location (from bottom) of object in points
        '''
        return self._rect[1]

    @property
    def w(self):
        ''' Width of object in points
        '''
        return self._rect[2]

    @property
    def h(self):
        ''' Height of object in points
        '''
        return self._rect[3]

    def __setattr__(self, name, value, next=PdfDict.__setattr__,
                    mine=set('x y w h'.split())):
        ''' The underlying __setitem__ won't let us use a property
            setter, so we have to fake one.
        '''
        if name not in mine:
            return next(self, name, value)
        if name in 'xy':
            r_index, m_index = (0, 4) if name == 'x' else (1, 5)
            self._rect[r_index], old = value, self._rect[r_index]
            self._matrix[m_index] += value - old
        else:
            index = 2 + (value == 'h')
            self.scale(value / self._rect[index])

    def scale(self, x_scale, y_scale=None):
        ''' Current scaling deals properly with things that
            have been rotated in 90 degree increments
            (via the ViewMerge object given when instantiating).
        '''
        if y_scale is None:
            y_scale = x_scale
        x, y, w, h = rect = self._rect
        ao, bo, co, do, eo, fo = matrix = self._matrix
        an = ao * x_scale
        bn = bo * y_scale
        cn = co * x_scale
        dn = do * y_scale
        en = x + (eo - x) * 1.0 * (an + cn) / (ao + co)
        fn = y + (fo - y) * 1.0 * (bn + dn) / (bo + do)
        matrix[:] = an, bn, cn, dn, en, fn
        rect[:] = x, y, w * x_scale, h * y_scale

    @property
    def box(self):
        ''' Return the bounding box for the object
        '''
        x, y, w, h = self._rect
        return PdfArray([x, y, x + w, y + h])


class PageMerge(list):
    ''' A PageMerge object can have 0 or 1 underlying pages
        (that get edited with the results of the merge)
        and 0-n RectXObjs that can be applied before or
        after the underlying page.
    '''
    page = None
    mbox = None
    cbox = None
    resources = None
    rotate = None
    contents = None

    def __init__(self, page=None):
        if page is not None:
            self.setpage(page)

    def setpage(self, page):
        if page.Type != PdfName.Page:
            raise TypeError("Expected page")
        self.append(None)  # Placeholder
        self.page = page
        inheritable = page.inheritable
        self.mbox = inheritable.MediaBox
        self.cbox = inheritable.CropBox
        self.resources = inheritable.Resources
        self.rotate = inheritable.Rotate
        self.contents = page.Contents

    def __add__(self, other):
        if isinstance(other, dict):
            other = [other]
        for other in other:
            self.add(other)
        return self

    def add(self, obj, prepend=False, **kw):
        if kw:
            obj = RectXObj(obj, **kw)
        elif obj.Type == PdfName.Page:
            obj = RectXObj(obj)
        if prepend:
            self.insert(0, obj)
        else:
            self.append(obj)
        return self

    def render(self):
        def do_xobjs(xobj_list, restore_first=False):
            content = ['Q'] if restore_first else []
            for obj in xobj_list:
                index = PdfName('pdfrw_%d' % (key_offset + len(xobjs)))
                if xobjs.setdefault(index, obj) is not obj:
                    raise KeyError("XObj key %s already in use" % index)
                content.append('%s Do' % index)
            return PdfDict(indirect=True, stream='\n'.join(content))

        mbox = self.mbox
        cbox = self.cbox
        page = self.page
        old_contents = self.contents
        resources = self.resources or PdfDict()

        key_offset = 0
        xobjs = resources.XObject
        if xobjs is None:
            xobjs = resources.XObject = PdfDict()
        else:
            allkeys = xobjs.keys()
            if allkeys:
                keys = (x for x in allkeys if x.startswith('/pdfrw_'))
                keys = (x for x in keys if x[7:].isdigit())
                keys = sorted(keys, key=lambda x: int(x[7:]))
                key_offset = (int(keys[-1][7:]) + 1) if keys else 0
                key_offset -= len(allkeys)

        if old_contents is None:
            new_contents = do_xobjs(self)
        else:
            isdict = isinstance(old_contents, PdfDict)
            old_contents = [old_contents] if isdict else old_contents
            new_contents = PdfArray()
            index = self.index(None)
            if index:
                new_contents.append(do_xobjs(self[:index]))

            index += 1
            if index < len(self):
                # There are elements to add after the original page contents,
                # so push the graphics state to the stack. Restored below.
                new_contents.append(PdfDict(indirect=True, stream='q'))

            new_contents.extend(old_contents)

            if index < len(self):
                # Restore graphics state and add other elements.
                new_contents.append(do_xobjs(self[index:], restore_first=True))

        if mbox is None:
            cbox = None
            mbox = self.xobj_box
            mbox[0] = min(0, mbox[0])
            mbox[1] = min(0, mbox[1])

        page = PdfDict(indirect=True) if page is None else page
        page.Type = PdfName.Page
        page.Resources = resources
        page.MediaBox = mbox
        page.CropBox = cbox
        page.Rotate = self.rotate
        page.Contents = new_contents
        return page

    @property
    def xobj_box(self):
        ''' Return the smallest box that encloses every object
            in the list.
        '''
        a, b, c, d = zip(*(xobj.box for xobj in self))
        return PdfArray((min(a), min(b), max(c), max(d)))
