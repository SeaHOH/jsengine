from __future__ import print_function

from jsengine.abstract import AbstractJSEngine
from jsengine.exceptions import *
from jsengine.util import which, to_bytes, json_encoder, json_encoder_ensure_ascii
from subprocess import Popen, PIPE, list2cmdline
import jsengine.detect as _d
import tempfile
import os
import sys
import json

# The maximum length of command string
if os.name == 'posix':
    # Used in Unix is ARG_MAX in conf
    ARG_MAX = int(os.popen('getconf ARG_MAX').read())
else:
    # Used in Windows CreateProcess is 32K
    ARG_MAX = 32 * 1024


class ExternalJSEngine(AbstractJSEngine):
    '''Wrappered for external Javascript interpreter.'''

    def __init__(self, source=u'', init_global=False, init_del_gobjects=[],
                       interpreter=None, **kwargs):
        '''
            (interpreter, **kwargs):
                same as ExternalInterpreter.__init__
        '''
        if isinstance(interpreter, str):
            interpreter = ExternalInterpreter.get(interpreter, **kwargs)
        if isinstance(interpreter, ExternalInterpreter):
            self.interpreter = interpreter
        elif isinstance(_d.external_interpreter, ExternalInterpreter):
            self.interpreter = _d.external_interpreter
        else:
            msg = 'No supported external Javascript interpreter found on your system!'
            if _d.chakra_available:
                msg += ' Please install one or use ChakraJSEngine.'
            elif _d.quickjs_available:
                msg += ' Please install one or use QuickJSEngine.'
            else:
                msg += ' Please install one.'
            raise RuntimeError(msg)
        # Del 'exports' to ignore import error, e.g. Node.js
        init_del_gobjects = list(init_del_gobjects) + ['exports']
        AbstractJSEngine.__init__(self, source, init_global, init_del_gobjects)

    __init__.__doc__ = AbstractJSEngine.__init__.__doc__ + __init__.__doc__[9:]

    def _eval(self, code):
        code = self._inject_script()

        evalstring = False
        if self.interpreter.evalstring:
            try:
                output = self._run_interpreter_with_string(code)
                evalstring = True
            except ValueError:
                pass
            except RuntimeError:
                self.interpreter.evalstring = False

        if not evalstring and not self.interpreter.tempfile:
            try:
                output = self._run_interpreter_with_pipe(code)
            except RuntimeError:
                self.interpreter.tempfile = True

        while True:
            if not evalstring and self.interpreter.tempfile:
                output = self._run_interpreter_with_tempfile(code)

            output = output.replace(u'\r\n', u'\n').replace(u'\r', u'\n')
            # Search result in the last 5 lines of output
            for result_line in output.split(u'\n')[-5:]:
                if result_line[:9] == u'["result"':
                    break
            try:
                _, ok, result = json.loads(result_line)
            except json.decoder.JSONDecodeError as e:
                if not evalstring and self.interpreter.tempfile:
                    raise RuntimeError('%s:\n%s' % (e, output))
                else:
                    evalstring = False
                    self.interpreter.tempfile = True
                    continue
            if ok:
                return result
            else:
                raise ProgramError(result)

    def _run_interpreter(self, cmd, input=None):
        stdin = PIPE if input else None
        p = Popen(cmd, stdin=stdin, stdout=PIPE, stderr=PIPE)
        stdout_data, stderr_data = p.communicate(input=input)
        if p.returncode != 0:
            raise RuntimeError('%r returns non-zero value! Error msg: %s' %
                               (_d.external_interpreter, stderr_data.decode('utf8')))
        elif stderr_data:
            print("%r has warnings:" % _d.external_interpreter,
                  stderr_data.decode('utf8'), file=sys.stderr)
        # Output unicode
        return stdout_data.decode('utf8')

    def _run_interpreter_with_string(self, code):
        cmd = self.interpreter.command + [self.interpreter.evalstring, code]
        if len(list2cmdline(cmd)) > ARG_MAX:  # Direct compare, don't wait an Exception
            raise ValueError('code length is too long to run as a command')
        return self._run_interpreter(cmd)

    def _run_interpreter_with_pipe(self, code):
        # Input bytes
        return self._run_interpreter(self.interpreter.command, input=to_bytes(code))

    def _run_interpreter_with_tempfile(self, code):
        fd, filename = tempfile.mkstemp(prefix='execjs', suffix='.js')
        try:
            # Write bytes
            try:
                with os.fdopen(fd, 'wb') as fp:
                    fp.write(to_bytes(code))
            except BaseException:
                os.close(fd)
            return self._run_interpreter(self.interpreter.command + [filename])
        finally:
            os.remove(filename)

    def _inject_script(self):
        if self.interpreter.evalstring:
            source = json_encoder_ensure_ascii.encode(self.source)
        else:
            source = json_encoder.encode(self.source)
        return injected_script.format(source=source)


class ExternalInterpreter(object):
    '''External interpreter setting.'''

    @classmethod
    def get(cls, *args, **kwargs):
        '''Same as cls.__init__, the fallback is None.'''
        try:
            return cls(*args, **kwargs)
        except Exception as e:
            print(e, file=sys.stderr)

    def __init__(self, interpreter, name=None, tempfile=False, evalstring=False, args=None):
        '''Create an external interpreter setting.

        params:
            interpreter:
                None means default interpreter by detected,
                or the filename/filepath of a interpreter,
                or a ExternalInterpreter instance.
            name:
                use to get default setting, see ExternalInterpreterNameAlias.
            tempfile:
                whether to use tempfile or not to pass Javascript code.
            evalstring:
                whether to use shell cmd or not to pass Javascript code.
                if set True, default param is `-e`.
                here also accept other valid params likes `--execute`
            args:
                any valid params of the interpreter.
        '''
        path = which(interpreter)
        if path is None:
            raise ValueError('Can not find the given interpreter: %r' % interpreter)
        filename = os.path.basename(path).rsplit('.', 1)[0]
        if name is None:
            name = filename
        name = ExternalInterpreterNameAlias.get(name.lower().replace('.', ''), name)
        if name in DefaultExternalInterpreterOptions:
            tempfile, evalstring, _args = DefaultExternalInterpreterOptions[name]
            if not args:
                args = _args
        self.name = name
        self.path = path
        self.tempfile = tempfile
        # `-e`, `-eval` means run command string as Javascript
        # But some interpreters don't use `-eval`
        if isinstance(evalstring, str) and evalstring.startswith('-'):
            self.evalstring = evalstring
        else:
            self.evalstring = evalstring and '-e' or False
        self.command = [path]
        if args:
            self.command += list(args)

    def __repr__(self):
        return '<ExternalInterpreter %s @ %r>' % (self.name, self.path)


DefaultExternalInterpreterOptions = {
                # tempfile, evalstring, args
    'ChakraCore': [ True, False, []],
       'Node.js': [ True,  True, []],
       'QuickJS': [ True,  True, []],
            'V8': [ True,  True, []],
            'XS': [ True,  True, []],
}

ExternalInterpreterNameAlias = {
    # *1 Unceremonious name is not recommended to be used as the binary name
        'chakracore': 'ChakraCore',
            'chakra': 'ChakraCore',
                'ch': 'ChakraCore',    # *1
               'cjs': 'CJS',
               'gjs': 'Gjs',
    'javascriptcore': 'JavaScriptCore',
               'jsc': 'JavaScriptCore',
            'nodejs': 'Node.js',
              'node': 'Node.js',
           'quickjs': 'QuickJS',
               'qjs': 'QuickJS',
              'qjsc': 'QuickJS',
           'jsshell': 'SpiderMonkey',
      'spidermonkey': 'SpiderMonkey',
                'sm': 'SpiderMonkey',  # *1
                'js': 'SpiderMonkey',  # *1
                'v8': 'V8',            # *1
                'd8': 'V8',            # *1
                'xs': 'XS',            # *1
               'xst': 'XS',
    # Don't use these interpreters
    # They are not compatible with the most used ES6 features
           'duktape': 'Duktape(incompatible)',
               'duk': 'Duktape(incompatible)',
            'hermes': 'Hermes(incompatible)',
           'cscript': 'JScript(incompatible)',
         'phantomjs': 'PhantomJS(incompatible)',
}

# Inject to the script to let it return jsonlized value to python
# Fixed our helper objects
injected_script = u'''\
Object.defineProperty((typeof global !== 'undefined') && global ||
                      (typeof globalThis !== 'undefined') && globalThis ||
                      this, '_JSEngineHelper', {{
    value: {{}},
    writable: false,
    configurable: false
}})
Object.defineProperty(_JSEngineHelper, 'print', {{
    value: function(s) {{
        if (typeof console !== 'undefined' && typeof console.log !== 'undefined')
            console.log(s)
        else if (typeof print === 'function')
            print(s)
    }},
    writable: false,
    configurable: false
}})
Object.defineProperty(_JSEngineHelper, 'jsonStringify', {{
    value: JSON.stringify,
    writable: false,
    configurable: false
}})
Object.defineProperty(_JSEngineHelper, 'result', {{
    value: null,
    writable: true,
    configurable: false
}})
Object.defineProperty(_JSEngineHelper, 'status', {{
    value: false,
    writable: true,
    configurable: false
}})
try {{
    _JSEngineHelper.result = eval({source}), _JSEngineHelper.status = true
}}
catch (err) {{
    _JSEngineHelper.result = err.toString(), _JSEngineHelper.status = false
}}
try {{
    _JSEngineHelper.print('\\n' + _JSEngineHelper.jsonStringify(
        ["result", _JSEngineHelper.status, _JSEngineHelper.result]))
}}
catch (err) {{
    _JSEngineHelper.print(
        '\\n["result", false, "Script returns a value with an unsupported type"]')
}}
'''
