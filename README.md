# JSEngine

This is a simple wrapper of Javascript engines, it wraps the Javascript
interpreter for Python use.

There are two ways to call interpreters, via dynamic library loading is internal
call which is faster than the other one, via subprocess is external call.

- System's built-in Javascript interpreter:

    **macOS**: JavascriptCore  
    **Linux**: Gjs on Gnome, CJS on Cinnamon, etc.  
    **Windows**: Chakra (internal call, but not applicable to Windows 7)  

- Python bindings (Recommend, internal call):

    [QuickJS](https://github.com/PetterS/quickjs)  
    [PyChakra](https://github.com/zhengrenzhe/PyChakra)  
    [PyMiniRacer (V8)](https://github.com/sqreen/PyMiniRacer)
    (Caused by [a scope issue](https://github.com/sqreen/PyMiniRacer/issues/148),
    its work process is similar to external call now, to fix the scope issue,
    [Esprima](https://github.com/Kronuz/esprima-python) is needed)  

- Any installed external Javascript interpreters, e.g.

    SpiderMonkey, Node.js, QuickJS, etc.

JSEngine used to be part of [YKDL](https://github.com/SeaHOH/ykdl),
which created by [@coslyk](https://github.com/coslyk).


# Installation
Install from 
[![version](https://img.shields.io/pypi/v/jsengine)](https://pypi.org/project/jsengine/)
[![package format](https://img.shields.io/pypi/format/jsengine)](https://pypi.org/project/jsengine/#files)
[![monthly downloads](https://img.shields.io/pypi/dm/jsengine)](https://pypi.org/project/jsengine/#files)

    pip install jsengine

Or download and Install from source code

    python setup.py install

# Compatibility
- Python >= 2.7


# Usage

```python
import jsengine
jsengine.eval('"Hello, world!"')  # => 'Hello, world!'
```

Use a JSEngine context.

```python
try:
    ctx1 = jsengine.jsengine()
except jsengine.RuntimeError:
    ...  # do something if useless

if jsengine.JSEngine is None:
    ...  # do something if useless
else:
    ctx2 = jsengine.JSEngine("""
            function add(x, y) {
                return x + y;
            }
            """)

ctx1.eval('1 + 1')  # => 2

# call funtion
ctx2.call("add", 1, 2)  # => 3

# append new script
ctx1.append("""
    function square(x) {
        return x ** 2;
    }
    """)
ctx1.call("square", 9)  # => 81
```

Use a specified external Javascript interpreter.

```python
binary = binary_name or binary_path
kwargs = {
    'name': 'None or any string',  # see ExternalInterpreterNameAlias.keys()
    'tempfile': True,              # use tempfile or not. Default is False, fallback is True
    'evalstring': True,            # can run command string as Javascript or can not,
                                   # just like '-e script_code'
                                   # instead of True, supported argument can be passed,
                                   # e.g. '--eval', '--execute'
    'args': [args1, args2, ...]    # arguments used for interpreter
}

# case 1
interpreter = jsengine.ExternalInterpreter.get(binary, **kwargs)
if interpreter:
    # found
    ctx = jsengine.ExternalJSEngine(interpreter)

# case 2
if jsengine.set_external_interpreter(binary, **kwargs):
    # set default external interpreter OK
    ctx = jsengine.ExternalJSEngine()

# case 3, maybe get default fallback instead of your specified
try:
    ctx = jsengine.ExternalJSEngine(interpreter=binary, **kwargs)
except jsengine.RuntimeError:
    ...  # do something if useless
```

Use threading lock. Javascript source itself always be ran in single threaded,
that just make the APIs can be used in multithreadeding.
```python
jsengine.set_threading(True)   # MUST enable befor using, it's disabled by default

ctx_quickjs = jsengine.QuickJSEngine()
ctx_chakra = jsengine.ChakraJSEngine()   # internal chakra will create an extra thread per context
ctx_v8 = jsengine.V8JSEngine()
ctx_exter = jsengine.ExternalJSEngine()  # external interpreter will be called one by one with context

...  # do multithreading

jsengine.set_threading(False)  # disable is not necessary
```


# Internal VS. External
|                 | QuickJSEngine  | ChakraJSEngine | V8JSEngine (esprima) | V8JSEngine \**       | ExternalJSEngine     |
| --------------- | :------------: | :------------: | :------------------: | :------------------: | :------------------: |
| Load backend on | import         | import or init | init                 | init                 | every fetch result   |
| Loading speed   | fastest        | fast           | very slow with py3   | fast                 | very slow            |
| Performance     |                | highest        | high                 | low, if much results | low, if much results |
| Fetch result    | run the passed | run the passed | run the passed       | run all/full source  | run all/full source  |

\* Fetch results means call `eval()/call()`.  
\** V8JSEngine is now similar to ExternalJSEngine which caused by scope issue.  


# License
JSEngine is released under the [MIT License](https://github.com/SeaHOH/jsengine/blob/master/LICENSE).
