from jsengine.abstract import AbstractJSEngine
from jsengine.exceptions import *
import jsengine.detect as _d
import json


class InternalJSEngine(AbstractJSEngine):
    '''Wrappered for Internal(DLL) Javascript interpreter.'''

    def __init__(self, *args, **kwargs):
        self._context = self.Context(self)
        AbstractJSEngine.__init__(self, *args, **kwargs)

    def _append(self, code):
        self._context.eval(code, eval=False, raw=True)

    def _eval(self, code):
        return self._context.eval(code)

    class Context:
        def __init__(self, engine):
            raise NotImplementedError('Class `Context` must be implemented by subclass')


class ChakraJSEngine(InternalJSEngine):
    '''Wrappered for system's built-in Chakra or PyChakra(ChakraCore).'''

    def __init__(self, *args, **kwargs):
        if not _d.chakra_available:
            msg = 'No supported Chakra binary found on your system!'
            if _d.quickjs_available:
                msg += ' Please install PyChakra or use QuickJSEngine.'
            elif _d.external_interpreter:
                msg += ' Please install PyChakra or use ExternalJSEngine.'
            else:
                msg += ' Please install PyChakra.'
            raise RuntimeError(msg)
        InternalJSEngine.__init__(self, *args, **kwargs)

    class Context:
        def __init__(self, engine):
            self._engine = engine
            self._context = _d.ChakraHandle()

        def eval(self, code, eval=True, raw=False):
            self._engine._append_source(code)
            ok, result = self._context.eval(code, raw=raw)
            if ok:
                if eval:
                    return result
            else:
                raise ProgramError(str(result))


class QuickJSEngine(InternalJSEngine):
    '''Wrappered for QuickJS python binding quickjs.'''

    def __init__(self, *args, **kwargs):
        if not _d.quickjs_available:
            msg = 'No supported QuickJS package found on custom python environment!'
            if _d.chakra_available:
                msg += ' Please install python package quickjs or use ChakraJSEngine.'
            elif _d.external_interpreter:
                msg += ' Please install python package quickjs or use ExternalJSEngine.'
            else:
                msg += ' Please install python package quickjs.'
            raise RuntimeError(msg)
        InternalJSEngine.__init__(self, *args, **kwargs)

    class Context:
        def __init__(self, engine):
            self._engine = engine
            self._context = _d.quickjs.Context()
            self.typeof = self.Function(self, self._context.eval(u'(obj => typeof obj)'))

        def eval(self, code, eval=True, raw=False):
            self._engine._append_source(code)
            try:
                result = self._context.eval(code)
            except _d.quickjs.JSException as e:
                raise ProgramError(*e.args)
            else:
                if eval:
                    if raw or not isinstance(result, _d.quickjs.Object):
                        return result
                    elif callable(result) and self.typeof(result) == u'function':
                        return self.Function(self, result)
                    else:
                        return json.loads(result.json())

        class Function:
            # PetterS/quickjs/Issue7
            # Escape StackOverflow when calling function outside
            def __init__(self, context, function):
                self._context = context
                self._function = function

            def __call__(self, *args):
                return self._function(*args)
