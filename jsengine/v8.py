import os
import json
import ctypes
from jsengine.util import to_bytes, json_encoder

try:
    from py_mini_racer import py_mini_racer
    if not os.path.isfile(py_mini_racer.EXTENSION_PATH):
        raise RuntimeError
except (ImportError, RuntimeError):
    v8_available = False
else:
    v8_available = True

v8 = None

injected_script = u'''\
try {{
    JSON.stringify([true, eval({code})])
}}
catch (err) {{
    JSON.stringify([false, err.toString()])
}}
'''


class MiniRacer(object):

    def __init__(self):
        global v8
        if v8 is None:
            v8 = py_mini_racer._build_ext_handle()
        self.ctx = v8.mr_init_context(b'--single-threaded')  # disable background

    def eval(self, code, raw=False):
        if not raw:
            code = json_encoder.encode(code)
            code = injected_script.format(code=code)
        code = to_bytes(code)

        res = v8.mr_eval_context(self.ctx, code, len(code),
                                           ctypes.c_ulong(0),
                                           ctypes.c_size_t(0))
        if not res:
            raise py_mini_racer.JSConversionException()

        try:
            res = py_mini_racer.MiniRacerValue(self, res).to_python()
        except py_mini_racer.JSConversionException as e:
            if raw:
                return True, None
            return False, e
        except (py_mini_racer.JSParseException, py_mini_racer.JSEvalException) as e:
            return False, e

        if raw:
            return True, None

        return json.loads(res)

    def _free(self, res):
        v8.mr_free_value(self.ctx, res)

    def __del__(self):
        v8.mr_free_context(getattr(self, 'ctx', None))
