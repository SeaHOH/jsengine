from __future__ import print_function

import os
import sys
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
    {code}
    JSON.stringify([true, eval({expression})])
}}
catch (err) {{
    JSON.stringify([false, err.toString()])
}}
'''

try:
    esprima = True
    if v8_available:
        from esprima.parser import Parser
except ImportError:
    esprima = warned = False

    def escheck(code):
        return False

    def split_last_expr(code):
        global warned
        if not warned:
            print('There is a scope issue with calss declarations in PyMiniRacer,'
                  ' measures to relieve it result in degrade performance!'
                  ' Please install esprima to resolve the issue.',
                  file=sys.stderr)
            warned = True
        return u'', code
else:
    if v8_available:

        def escheck(code):
            try:
                Parser(code).parseScript()
            except Exception:
                return True # program errors
            else:
                return False

        def split_last_expr(code, options={'range': True}):
            try:
                nodes = Parser(code, options=options).parseScript().body
            except Exception:
                return u'', code  # program errors
            nodes.reverse()
            start = len(code)
            for node in nodes:
                if node.type == 'EmptyStatement':
                    continue
                if node.type != 'ExpressionStatement' or \
                        node.expression.value == u'use strict':
                    break
                start = node.range[0]
            return code[:start], code[start:]


class MiniRacer(object):

    def __init__(self):
        global v8
        if v8 is None:
            v8 = py_mini_racer._build_ext_handle()
        self.ctx = v8.mr_init_context(b'--single-threaded')  # disable background

    def eval(self, code, raw=False):
        jsonr = False
        expression = u''
        if not raw:
            code, expression = split_last_expr(code)
        elif escheck(code):
            # Get V8 errors instead of PyMiniRacer's Exception
            code, expression = expression, code
        if expression:
            expression = json_encoder.encode(expression)
            code = injected_script.format(code=code, expression=expression)
            jsonr = True
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

        if jsonr:
            return json.loads(res)

        return True, None if raw else res

    def _free(self, res):
        v8.mr_free_value(self.ctx, res)

    def __del__(self):
        v8.mr_free_context(getattr(self, 'ctx', None))
