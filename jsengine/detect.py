from __future__ import print_function

import os
import sys
import platform
from jsengine.util import which


chakra_available = False
quickjs_available = False
external_interpreter = None

# PyChakra
try:
    from PyChakra import Runtime as ChakraHandle, get_lib_path
    if not os.path.isfile(get_lib_path()):
        raise RuntimeError
except (ImportError, RuntimeError):
    pass
else:
    chakra_available = True

# PyQuickJS
try:
    import quickjs
except ImportError:
    pass
else:
    quickjs_available = True

# macOS: built-in JavaScriptCore
if platform.system() == 'Darwin':
    # jsc lives on a new path since macOS Catalina
    jsc_paths = ['/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Resources/jsc',
                 '/System/Library/Frameworks/JavaScriptCore.framework/Versions/A/Helpers/jsc']
    for interpreter in jsc_paths:
        external_interpreter = which(interpreter)
        if external_interpreter:
            break

# Windows: built-in Chakra, or Node.js, QuickJS if installed
elif platform.system() == 'Windows':
    if not chakra_available:
        from jsengine.chakra_win import ChakraHandle, chakra_available

    for interpreter in ('qjs', 'node', 'nodejs'):
        external_interpreter = which(interpreter)
        if external_interpreter:
            break

    if not chakra_available and not quickjs_available and external_interpreter is None:
        print('Please install PyChakra or Node.js!', file=sys.stderr)

# Linux: Gjs on Gnome, CJS on Cinnamon, or JavaScriptCore, Node.js if installed
else:
    for interpreter in ('gjs', 'cjs', 'jsc', 'qjs', 'nodejs', 'node'):
        external_interpreter = which(interpreter)
        if external_interpreter:
            break

    if not chakra_available and not quickjs_available and external_interpreter is None:
        if platform.system() == 'Linux':
            print('''\
Please install at least one of the following Javascript interpreter.
python packages: PyChakra, quickjs
applications: Gjs, CJS, QuickJS, JavaScriptCore, Node.js.''', file=sys.stderr)

        else:
            print('''\
Sorry, JSEngine is currently not supported officially on your system.
Please try install one of the following Javascript interpreter.
applications: Gjs, CJS, QuickJS, JavaScriptCore, Node.js.''', file=sys.stderr)
