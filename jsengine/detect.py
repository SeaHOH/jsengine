from __future__ import print_function

import sys
import platform
from jsengine.util import which

# PyMiniRacer
from jsengine.v8 import v8_available

# PyChakra or Windows built-in Chakra
from jsengine.chakra import chakra_available

# PyQuickJS
try:
    import quickjs
except ImportError:
    quickjs_available = False
else:
    quickjs_available = True

external_interpreter = None

# macOS: built-in JavaScriptCore
if platform.system() == 'Darwin':
    # jsc lives on a new path since macOS Catalina
    jsc_paths = ['/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc',
                 '/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc']
    for interpreter in jsc_paths:
        external_interpreter = which(interpreter)
        if external_interpreter:
            break

# Windows: Node.js, QuickJS if installed
elif platform.system() == 'Windows':
    for interpreter in ('qjs', 'node', 'nodejs'):
        external_interpreter = which(interpreter)
        if external_interpreter:
            break

    if external_interpreter is None and \
            not v8_available and \
            not chakra_available and \
            not quickjs_available:
        print('Please install PyChakra, PyMiniRacer or Node.js!', file=sys.stderr)

# Linux: Gjs on Gnome, CJS on Cinnamon, or JavaScriptCore, Node.js if installed
else:
    for interpreter in ('gjs', 'cjs', 'jsc', 'qjs', 'nodejs', 'node'):
        external_interpreter = which(interpreter)
        if external_interpreter:
            break

    if external_interpreter is None and \
            not v8_available and \
            not chakra_available and \
            not quickjs_available:
        if platform.system() == 'Linux':
            print('''\
Please install at least one of the following Javascript interpreter.
python packages: quickjs, PyChakra, PyMiniRacer
applications: Gjs, CJS, QuickJS, JavaScriptCore, Node.js.''', file=sys.stderr)

        else:
            print('''\
Sorry, JSEngine is currently not supported officially on your system.
Please try install one of the following Javascript interpreter.
applications: Gjs, CJS, QuickJS, JavaScriptCore, Node.js.''', file=sys.stderr)
