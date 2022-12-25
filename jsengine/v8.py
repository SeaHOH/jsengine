from __future__ import print_function

import os
import json
import ctypes
from jsengine.util import to_bytes

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
{code}
JSON.stringify([({expression})])
'''

try:
    esprima = True
    if v8_available:
        from esprima.parser import Parser
except ImportError:
    esprima = warned = False

    def split_last_expr(code):
        global warned
        if not warned:
            import sys
            print('There is a scope issue with class declarations in PyMiniRacer,'
                  ' measures to relieve it result in degrade performance!'
                  ' Please install esprima to resolve the issue.',
                  file=sys.stderr)
            warned = True
        return u'', u'eval(%r)' % code
else:
    if v8_available:

        import re
        _strip_ending = re.compile('[\s;]*$', re.UNICODE).sub

        def split_last_expr(code, options={'range': True}):
            try:
                nodes = Parser(code, options=options).parseScript().body
            except Exception:
                return code, u''  # program errors
            nodes.reverse()
            start = len(code)
            for node in nodes:
                if node.type == 'ExpressionStatement':
                    start = node.range[0]
                    break
            code, expression = code[:start], code[start:]
            expression = _strip_ending(u'', expression, 1)
            return code, expression

class MiniRacer(object):

    def __init__(self):
        global v8
        if v8 is None:
            v8 = py_mini_racer._build_ext_handle()
        self.ctx = v8.mr_init_context(b'--single-threaded')  # disable background

    def eval(self, code, raw=False):
        if raw:
            expression = u''
        else:
            code, expression = split_last_expr(code)
            if expression:
                code = injected_script.format(code=code, expression=expression)
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
            return False, e.args[0]

        if expression:
            return True, json.loads(res)[0]

        return True, None if raw else res

    def _free(self, res):
        v8.mr_free_value(self.ctx, res)

    def __del__(self):
        v8.mr_free_context(getattr(self, 'ctx', None))
