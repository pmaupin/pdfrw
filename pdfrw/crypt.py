# A part of pdfrw (https://github.com/pmaupin/pdfrw)
# Copyright (C) 2017  Jon Lund Steffensen
# MIT license -- See LICENSE.txt for details

from __future__ import division

import hashlib
import struct

try:
    from Crypto.Cipher import ARC4, AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

from .objects import PdfDict, PdfName

_PASSWORD_PAD = (
    '(\xbfN^Nu\x8aAd\x00NV\xff\xfa\x01\x08'
    '..\x00\xb6\xd0h>\x80/\x0c\xa9\xfedSiz')


def streamobjects(mylist, isinstance=isinstance, PdfDict=PdfDict):
    for obj in mylist:
        if isinstance(obj, PdfDict) and obj.stream is not None:
            yield obj


def create_key(password, doc):
    """Create an encryption key (Algorithm 2 in PDF spec)."""
    key_size = int(doc.Encrypt.Length or 40) // 8
    padded_pass = (password + _PASSWORD_PAD)[:32]
    hasher = hashlib.md5()
    hasher.update(padded_pass)
    hasher.update(doc.Encrypt.O.to_bytes())
    hasher.update(struct.pack('<i', int(doc.Encrypt.P)))
    hasher.update(doc.ID[0].to_bytes())
    temp_hash = hasher.digest()

    if int(doc.Encrypt.R or 0) >= 3:
        for _ in range(50):
            temp_hash = hashlib.md5(temp_hash[:key_size]).digest()

    return temp_hash[:key_size]


def create_user_hash(key, doc):
    """Create the user password hash (Algorithm 4/5)."""
    revision = int(doc.Encrypt.R or 0)
    if revision < 3:
        cipher = ARC4.new(key)
        return cipher.encrypt(_PASSWORD_PAD)
    else:
        hasher = hashlib.md5()
        hasher.update(_PASSWORD_PAD)
        hasher.update(doc.ID[0].to_bytes())
        temp_hash = hasher.digest()

        for i in range(20):
            temp_key = ''.join(chr(i ^ ord(x)) for x in key)
            cipher = ARC4.new(temp_key)
            temp_hash = cipher.encrypt(temp_hash)

        return temp_hash


def check_user_password(key, doc):
    """Check that the user password is correct (Algorithm 6)."""
    expect_user_hash = create_user_hash(key, doc)
    revision = int(doc.Encrypt.R or 0)
    if revision < 3:
        return doc.Encrypt.U.to_bytes() == expect_user_hash
    else:
        return doc.Encrypt.U.to_bytes()[:16] == expect_user_hash


class AESCryptFilter(object):
    """Crypt filter corresponding to /AESV2."""
    def __init__(self, key):
        self._key = key

    def decrypt_data(self, num, gen, data):
        """Decrypt data (string/stream) using key (Algorithm 1)."""
        key_extension = struct.pack('<i', num)[:3]
        key_extension += struct.pack('<i', gen)[:2]
        key_extension += 'sAlT'
        temp_key = self._key + key_extension
        temp_key = hashlib.md5(temp_key).digest()

        iv = data[:AES.block_size]
        cipher = AES.new(temp_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(data[AES.block_size:])

        # Remove padding
        pad_size = ord(decrypted[-1])
        assert 1 <= pad_size <= 16
        return decrypted[:-pad_size]


class RC4CryptFilter(object):
    """Crypt filter corresponding to /V2."""
    def __init__(self, key):
        self._key = key

    def decrypt_data(self, num, gen, data):
        """Decrypt data (string/stream) using key (Algorithm 1)."""
        new_key_size = min(len(self._key) + 5, 16)
        key_extension = struct.pack('<i', num)[:3]
        key_extension += struct.pack('<i', gen)[:2]
        temp_key = self._key + key_extension
        temp_key = hashlib.md5(temp_key).digest()[:new_key_size]

        cipher = ARC4.new(temp_key)
        return cipher.decrypt(data)


class IdentityCryptFilter(object):
    """Identity crypt filter (pass through with no encryption)."""
    def decrypt_data(self, num, gen, data):
        return data


def decrypt_objects(objects, default_filter, filters):
    """Decrypt list of stream objects.

    The parameter default_filter specifies the default filter to use. The
    filters parameter is a dictionary of alternate filters to use when the
    object specfies an alternate filter locally.
    """
    for obj in streamobjects(objects):
        if getattr(obj, 'decrypted', False):
            continue

        filter = default_filter

        # Check whether a locally defined crypt filter should override the
        # default filter.
        ftype = obj.Filter
        if ftype is not None:
            if not isinstance(ftype, list):
                ftype = [ftype]
            if len(ftype) >= 1 and ftype[0] == PdfName.Crypt:
                ftype = ftype[1:]
                parms = obj.DecodeParms or obj.DP
                filter = filters[parms.Name]

        num, gen = obj.indirect
        obj.stream = filter.decrypt_data(num, gen, obj.stream)
        obj.private.decrypted = True
        obj.Filter = ftype or None
