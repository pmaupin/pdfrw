# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2006-2017 Patrick Maupin, Austin, Texas
# MIT license -- See LICENSE.txt for details

"""
This module contains a class that streams data out
to a file for the serializer.

If desirable, we could add variants for better looking
PDFs (for debugging) and/or worse looking PDFs (for reduced
file size).  The output of the initial streamer is not
particularly verbose or dense.
"""

from ..py23_diffs import convert_store


class StreamWriter(list):
    """
        This class writes out PDF streams.
        It essentially buffers on a per-indirect-object basis,
        because it doesn't pay any attention to the actual data
        until it's time to figure out what the file location is.

        To write, add to the list.
        To figure out where you are, call tell().
        To flush everything to the file object, call flush().

        Instances of this class do some formatting that is a balance
        between readability, efficiency, and output file size.
    """
    left_delim = '<[\n'
    right_delim = '>]\n'
    max_width = 71  # Might be one wider with added space

    def __init__(self, f):
        self._write = f.write
        self._tell = f.tell
        self.line_pos = 0
        self.need_space = 0

    # Normal way to stream data
    write = list.append

    def flush(self, len=len):
        left_delim = self.left_delim
        right_delim = self.right_delim
        max_width = self.max_width
        line_pos = self.line_pos
        need_space = self.need_space

        outs = []
        append = outs.append
        for s in self:
            old_pos = line_pos
            line_pos += len(s)
            if old_pos:
                if line_pos > max_width:
                    if s[0] != '\n':
                        append('\n')
                    line_pos -= old_pos
                elif need_space and s[0] not in right_delim:
                    append(' ')
                    line_pos += 1
            append(s)
            last_ch = s[-1]
            need_space = last_ch not in left_delim
            line_pos = 0 if last_ch == '\n' else line_pos

        self._write(convert_store(''.join(outs)))
        self[:] = []
        self.line_pos = line_pos
        self.need_space = need_space

    def tell(self):
        self.flush()
        return self._tell()
