from jsengine.abstract import AbstractJSEngine
from jsengine.chakra import ChakraHandle
from jsengine.v8 import MiniRacer, esprima
from jsengine.exceptions import *
import jsengine.detect as _d
import json


class InternalJSEngine(AbstractJSEngine):
    '''Wrappered for Internal(DLL) Javascript interpreter.'''

    def __init__(self, *args, **kwargs):
        self._context = self.Context()
        AbstractJSEngine.__init__(self, *args, **kwargs)

    def _append(self, code):
        self._context.eval(code, eval=False, raw=True)

    def _eval(self, code):
        return self._context.eval(code)

    class Context(object):
        def __init__(self):
            raise NotImplementedError('Class `Context` must be implemented by subclass')

        def eval(self, code, eval=True, raw=False):
            pass


class V8JSEngine(InternalJSEngine):
    '''Wrappered for V8 python binding PyMiniRacer.'''

    def __init__(self, source=u'', init_global=False, init_del_gobjects=[]):
        if not _d.v8_available:
            msg = ('No supported V8 package found on current python environment!'
                   ' Please install python package PyMiniRacer')
            if _d.quickjs_available:
                msg += ' or use QuickJSEngine.'
            elif _d.chakra_available:
                msg += ' or use ChakraJSEngine.'
            elif _d.external_interpreter:
                msg += ' or use ExternalJSEngine.'
            else:
                msg += '.'
            raise RuntimeError(msg)
        InternalJSEngine.__init__(self, source, init_global, init_del_gobjects)

    __init__.__doc__ = AbstractJSEngine.__init__.__doc__

    # Here is a scope issue now, we MUST execute all codes at once, if there has
    # no esprima package which use to split source code.
    # see https://github.com/sqreen/PyMiniRacer/issues/148
    if not esprima:
        def _append(self, code):
            pass

        def _eval(self, code):
            return self._context.eval(self.source)

    class Context(object):
        def __init__(self):
            if esprima:
                self._context = MiniRacer()
        
        if esprima:
            @property
            def context(self):
                return self._context
        else:
            @property
            def context(self):
                return MiniRacer()

        def eval(self, code, eval=True, raw=False):
            ok, result = self.context.eval(code, raw)
            if ok:
                if eval:
                    return result
            else:
                raise ProgramError(str(result))


class ChakraJSEngine(InternalJSEngine):
    '''Wrappered for system's built-in Chakra or PyChakra(ChakraCore).'''

    def __init__(self, source=u'', init_global=False, init_del_gobjects=[]):
        if not _d.chakra_available:
            msg = ('No supported Chakra binary found on your system!'
                   ' Please install python package PyChakra')
            if _d.quickjs_available:
                msg += ' or use QuickJSEngine.'
            elif _d.v8_available:
                msg += ' or use V8JSEngine.'
            elif _d.external_interpreter:
                msg += ' or use ExternalJSEngine.'
            else:
                msg += '.'
            raise RuntimeError(msg)
        InternalJSEngine.__init__(self, source, init_global, init_del_gobjects)

    __init__.__doc__ = AbstractJSEngine.__init__.__doc__

    class Context(object):
        def __init__(self):
            self._context = ChakraHandle(ChakraJSEngine.threading)

        def eval(self, code, eval=True, raw=False):
            ok, result = self._context.eval(code, raw=raw)
            if ok:
                if eval:
                    return result
            else:
                raise ProgramError(str(result))


class QuickJSEngine(InternalJSEngine):
    '''Wrappered for QuickJS python binding quickjs.'''

    def __init__(self, source=u'', init_global=False, init_del_gobjects=[]):
        if not _d.quickjs_available:
            msg = ('No supported QuickJS package found on current python environment!'
                   ' Please install python package quickjs')
            if _d.chakra_available:
                msg += ' or use ChakraJSEngine.'
            elif _d.v8_available:
                msg += ' or use V8JSEngine.'
            elif _d.external_interpreter:
                msg += ' or use ExternalJSEngine.'
            else:
                msg += '.'
            raise RuntimeError(msg)
        InternalJSEngine.__init__(self, source, init_global, init_del_gobjects)

    __init__.__doc__ = AbstractJSEngine.__init__.__doc__

    class Context(object):
        def __init__(self):
            self._context = _d.quickjs.Context()
            self.typeof = self._context.eval(u'(obj => typeof obj)')
            if hasattr(self, 'Function'):
                self.typeof = self.Function(self.typeof)

        def eval(self, code, eval=True, raw=False):
            try:
                result = self._context.eval(code)
            except _d.quickjs.JSException as e:
                raise ProgramError(*e.args)
            else:
                if eval:
                    if raw or not isinstance(result, _d.quickjs.Object):
                        return result
                    elif callable(result) and self.typeof(result) == u'function':
                        if hasattr(self, 'Function'):
                            result = self.Function(result)
                        return result
                    else:
                        return json.loads(result.json())

        if _d.quickjs_available and \
                not hasattr(_d.quickjs.Context, 'execute_pending_job'):
            # this is < v1.17.0
            # It was fixed in v1.16.0, but there is no version string to judge.
            class Function(object):
                # https://github.com/PetterS/quickjs/issues/7
                # Escape StackOverflow when calling function outside
                def __init__(self, function):
                    self._function = function

                def __call__(self, *args):
                    return self._function(*args)
