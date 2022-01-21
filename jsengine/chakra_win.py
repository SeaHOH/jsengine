'''This is a Python binding to Microsoft Chakra Javascript engine.
Forked from PyChakra (https://github.com/zhengrenzhe/PyChakra) to support
Windows' built-in Chakra.
'''


import ctypes as _ctypes
import threading as _threading
import json


# load Windows' built-in chakra binary
try:
    chakra = _ctypes.windll.Chakra
except:
    chakra_available = False
else:
    chakra_available = True
    chakra._current_runtime = None


threading = False
_lock = None

def _enable_lock():
    global _lock
    if _lock is not None:
        return
    _lock = _threading.Lock()

def _disable_lock():
    global _lock
    if _lock is None:
        return
    try:
        _lock.release()
    except:
        pass
    _lock = None


class ChakraHandle(object):

    def _acquire(self):
        if threading:
            _enable_lock()
            _lock.acquire()
        else:
            _disable_lock()
        self.set_current_runtime()

    def _release(self):
        if threading:
            try:
                _lock.release()
            except:
                pass
        else:
            _disable_lock()

    def set_current_runtime(self):
        runtime = id(self)
        if chakra._current_runtime != runtime:
            chakra._current_runtime = runtime
            chakra.JsSetCurrentContext(self.__context)

    def __init__(self):
        # create chakra runtime and context
        runtime = _ctypes.c_void_p()
        chakra.JsCreateRuntime(0, 0, point(runtime))

        context = _ctypes.c_void_p()
        chakra.JsCreateContext(runtime, point(context))
        chakra.JsSetCurrentContext(context)

        self.__runtime = runtime
        self.__context = context

        # get JSON.stringify reference, and create its called arguments array
        stringify = self.eval('JSON.stringify', raw=True)[1]
        undefined = _ctypes.c_void_p()
        chakra.JsGetUndefinedValue(point(undefined))
        args = (_ctypes.c_void_p * 2)()
        args[0] = undefined

        self.__jsonStringify = stringify
        self.__jsonStringifyArgs = args

    def __del__(self):
        chakra.JsDisposeRuntime(self.__runtime)

    def eval(self, script, raw=False):
        '''Eval javascript string

        Examples:
            .eval('(()=>2)()') // (True, 2)
            .eval('(()=>a)()') // (False, "ReferenceError: 'a' is not defined")

        Parameters:
            script(str): javascript code string
            raw(bool?): whether return result as chakra JsValueRef directly
                        (optional, default is False)

        Returns:
            (bool, result)
            bool: indicates whether javascript is running successfully.
            result: if bool is True, result is the javascript running
                        return value.
                    if bool is False and result is string, result is the
                        javascript running exception
                    if bool is False and result is number, result is the
                        chakra internal error code
        '''

        self._acquire()

        js_source = _ctypes.c_wchar_p('')
        js_script = _ctypes.c_wchar_p(script)

        result = _ctypes.c_void_p()
        err = chakra.JsRunScript(js_script, 0, js_source, point(result))

        try:
            # eval success
            if err == 0:
                if raw:
                    return True, result
                else:
                    return self.__js_value_to_py_value(result)

            return self.__get_error(err)

        finally:
            self._release()

    def __js_value_to_py_value(self, js_value):
        args = self.__jsonStringifyArgs
        args[1] = js_value

        # value => json
        result = _ctypes.c_void_p()
        err = chakra.JsCallFunction(
            self.__jsonStringify, point(args), 2, point(result))

        if err == 0:
            result = self.__js_value_to_str(result)
            if result == 'undefined':
                result = None
            else:
                # json => value
                result = json.loads(result)
            return True, result

        return self.__get_error(err)

    def __get_error(self, err):
        # js exception or other error
        # 0x30000, JsErrorCategoryScript
        # 0x30001, JsErrorScriptException
        # 0x30002, JsErrorScriptCompile

        if 0x30000 ^ err < 3:
            err = self.__get_exception()
        return False, err

    def __get_exception(self):
        exception = _ctypes.c_void_p()
        chakra.JsGetAndClearException(point(exception))
        return self.__js_value_to_str(exception)

    def __js_value_to_str(self, js_value):
        js_value_ref = _ctypes.c_void_p()
        chakra.JsConvertValueToString(js_value, point(js_value_ref))

        str_p = _ctypes.c_wchar_p()
        str_l = _ctypes.c_size_t()
        chakra.JsStringToPointer(js_value_ref, point(str_p), point(str_l))
        return str_p.value


def point(any):
    return _ctypes.byref(any)
