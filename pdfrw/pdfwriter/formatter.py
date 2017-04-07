# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

"""
This module contains formatters to convert PDF objects
into string representations suitable for streaming.
"""

import datetime
from ..errors import PdfOutputError
from ..objects import PdfString


class FormatHandlers(object):
    """
        Return a format handler for a given object type
    """

    formatters = [
        (bool, lambda obj: str(obj).lower()),
        (type(b''), PdfString.encode),   # Use type to account for Python 2/3
        (type(u''), PdfString.encode),   # Use type to account for Python 2/3
        (float, lambda obj: ('%.9f' % obj).rstrip('0').rstrip('.')),
        (datetime.datetime, lambda obj: PdfString.encode(obj.strftime('D:%Y%m%d%H%M%S'))),
        (datetime.date, lambda obj: PdfString.encode(obj.strftime('D:%Y%m%d'))),
        (type(None), lambda obj: 'null'),
        ]

    @classmethod
    def get_formatter(cls, obj_type):
        if issubclass(obj_type, (dict, list, tuple)):
            if hasattr(obj_type, 'encoded'):
                raise PdfOutputError("encoded not allowed for dicts or arrays")
            return dict if issubclass(obj_type, dict) else list
        elif hasattr(obj_type, 'encoded'):
            def handler(obj):
                value = obj.encoded
                return value if value is not None else obj
        elif hasattr(obj_type, 'indirect'):
            def handler(obj):
                return obj
        else:
            for superclass, handler in cls.formatters:
                if issubclass(obj_type, superclass):
                    break
            else:
                handler = str
        return handler
