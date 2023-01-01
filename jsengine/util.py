import os
import sys
import json
import locale
from functools import wraps

try:
    from shutil import which
except ImportError:
    from distutils.spawn import find_executable

    def which(cmd, mode=os.X_OK, path=None):
        cmd = find_executable(cmd, path)
        if cmd and os.access(cmd, mode):
            return cmd


unicode = u''.__class__
fallback_encodings = set((sys.getfilesystemencoding(),
                          hasattr(locale,'getencoding') and
                          locale.getencoding() or
                          locale.getdefaultlocale()[1],
                          locale.getpreferredencoding(False)))
fallback_encodings.discard(None)
fallback_encodings.discard('utf-8')
fallback_encodings = list(fallback_encodings)

def to_unicode(s):
    if isinstance(s, unicode):
        return s
    try:
        return s.decode('utf8')
    except UnicodeDecodeError:
        for encoding in fallback_encodings:
            try:
                return s.decode(encoding)
            except UnicodeDecodeError:
                pass
        raise

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
