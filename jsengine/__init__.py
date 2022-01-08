
# Copyright (c) 2019 coslyk
# Copyright (c) 2019 - 2021 SeaHOH <SeaHOH@gmail.com>


import platform
import jsengine.detect as _d
from jsengine.exceptions import *
from jsengine.internal import QuickJSEngine, ChakraJSEngine
from jsengine.external import ExternalJSEngine, ExternalInterpreter


__version__ = '1.0.1'

__all__ = ['JSEngine', 'ChakraJSEngine', 'QuickJSEngine', 'ExternalJSEngine',
           'ExternalInterpreter', 'set_external_interpreter',
           'Error', 'RuntimeError', 'ProgramError',
           'jsengine', 'eval']


def set_external_interpreter(interpreter, *args, **kwargs):
    '''
    Set default an external interpreter, return the result status.
    Same arguments as the ExternalInterpreter.
    '''
    interpreter = ExternalInterpreter.get(interpreter, *args, **kwargs)
    if interpreter:
        _d.external_interpreter = interpreter
    return interpreter


if _d.external_interpreter:
    _d.external_interpreter = ExternalInterpreter(_d.external_interpreter)

# Prefer InternalJSEngine (via dynamic library loading)
if _d.quickjs_available:
    JSEngine = QuickJSEngine
elif _d.chakra_available:
    JSEngine = ChakraJSEngine
elif _d.external_interpreter:
    JSEngine = ExternalJSEngine
else:
    JSEngine = None


def jsengine():
    '''Create a context of the default Javascript engine.'''
    if JSEngine:
        return JSEngine()

    if platform.system() in ('Darwin', 'Windows', 'Linux'):
        msg = 'No supported Javascript interpreter has been found'
    else:
        msg = 'Your system does not be supported officially'
    msg += ', please try install one of Gjs, CJS, QuickJS, JavaScriptCore, Node.js'
    raise RuntimeError(msg)

def eval(source):
    '''Run Javascript code use the default engine and return result.'''
    return jsengine().eval(source)

