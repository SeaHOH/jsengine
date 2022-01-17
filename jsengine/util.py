import os
import sys
import json
from functools import wraps

try:
    from shutil import which
except ImportError:
    from distutils.spawn import find_executable

    def which(cmd, mode=os.X_OK, path=None):
        cmd = find_executable(cmd, path)
        if cmd and os.access(cmd, mode):
            return cmd


if sys.version_info > (3,):
    unicode = str

def to_unicode(s):
    if not isinstance(s, unicode):
        s = s.decode('utf8')
    return s

def to_bytes(s):
    if isinstance(s, unicode):
        s = s.encode('utf8')
    return s

def json_encoder_fallback(o):
    if isinstance(o, (bytes, bytearray)):
        return to_unicode(o)
    return json.JSONEncoder.default(json_encoder, o)

json_encoder = json.JSONEncoder(
    skipkeys=True,
    ensure_ascii=False,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    default=json_encoder_fallback,
)

json_encoder_ensure_ascii = json.JSONEncoder(
    skipkeys=True,
    ensure_ascii=True,
    check_circular=True,
    allow_nan=True,
    indent=None,
    separators=None,
    default=None,
)

def lockmethod(func):
    @wraps(func)
    def newfunc(self, *args, **kwargs):
        if self._lock is None:
            return func(self, *args, **kwargs)
        self._lock.acquire()
        try:
            return func(self, *args, **kwargs)
        finally:
            self._lock.release()
    return newfunc
