import threading as _threading
import os
import platform

try:
    import queue
except ImportError:
    import Queue as queue


threading = False
chakra_available = False

if platform.system() == 'Windows':
    from jsengine import chakra_win
    chakra_available = chakra_win.chakra_available

    def _ChakraHandle(threading):
        chakra_win.threading = threading
        return chakra_win.ChakraHandle()

# PyChakra
if not chakra_available:
    try:
        import PyChakra
        if not os.path.isfile(PyChakra.get_lib_path()):
            raise RuntimeError
    except (ImportError, RuntimeError):
        pass
    else:
        chakra_available = True

        def _ChakraHandle(threading):
            return PyChakra.Runtime(threading=threading)


def FIFOQueue():
    try:
        return queue.SimpleQueue()
    except AttributeError:
        return queue.Queue(-1)

def ChakraHandle(threading):
    '''Return a ChakraHandle object or its agent (use in multithreading).'''
    if threading:
        return ChakraHandleAgent()
    else:
        return _ChakraHandle(False)

class ChakraHandleAgent(object):
    '''A ChakraHandle agent (.eval), every JsContext works with its own thread.
    Because it can ONLY run with the thread where it has been created.
        see https://github.com/chakra-core/ChakraCore/issues/5599
    '''

    def __init__(self):
        self.task = FIFOQueue()
        self.result = FIFOQueue()
        _threading._start_new_thread(self.run, ())

    def run(self):
        self.context = _ChakraHandle(True)
        while True:
            args = self.task.get()
            try:
                result = self.context.eval(*args)
            except Exception as e:
                result = e
            self.result.put((id(args), result))

    def eval(self, script, raw=False):
        args = script, raw
        self.task.put(args)
        tid, task_id = None, id(args)
        while tid != task_id:
            tid, result = self.result.get()
        if isinstance(result, Exception):
            raise result
        return result
