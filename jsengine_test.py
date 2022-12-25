#!/usr/bin/env python
#-*- coding: UTF-8 -*-

import unittest
import platform
import threading
from jsengine import *
import jsengine


print_source_code = False

def skip_or_reinit(func):
    def newfunc(*args, **kwargs):
        global ctx
        if ctx:
            try:
                func(*args, **kwargs)
            except:
                ctx = JSEngine()
                raise
        else:
            raise unittest.SkipTest('init failed')
    return newfunc

class JSEngineES6Tests(unittest.TestCase):

    expected_exceptions = ProgramError, RuntimeError

    def test_00_init(self):
        global ctx
        ctx = JSEngine()

    @skip_or_reinit
    def test_01_keyword_let(self):
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            let vlet
            let vlet''')
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            var vlet = 1
            let vlet''')
        self.assertEqual(ctx.eval('''
        var vlet = 1
        function flet() {
            let vlet = 2
        }
        flet(), vlet'''), 1)

    @skip_or_reinit
    def test_02_keyword_const(self):
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('const vconst')
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            const vconst = 1
            const vconst = 1''')
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            const vconst = 1
            vconst = 1''')
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            var vconst
            const vconst = 1''')
        self.assertEqual(ctx.eval('''
        var vconst = 1
        function fconst() {
            const vconst = 2
        }
        fconst(), vconst'''), 1)

    @skip_or_reinit
    def test_03_keyword_for_of(self):
        ctx.eval('for (n of []) {}')

    @skip_or_reinit
    def test_04_operator_power(self):
        self.assertEqual(ctx.eval('3 ** 3'), 27)

    @skip_or_reinit
    def test_05_operator_spread_rest(self):
        self.assertEqual(ctx.eval('''
        function foo(first, ...args) {return [first, args]}
        foo(...[1, 2, 3])'''), [1, [2, 3]])

    @skip_or_reinit
    def test_06_function_arrow(self):
        self.assertEqual(ctx.eval(';(arg => arg)(1)'), 1)
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            foo = arg => arg
            obj = new foo()''')

    @skip_or_reinit
    def test_07_function_default_arguments(self):
        ctx.eval('function foo(agr = "default") {}')

    @skip_or_reinit
    def test_08_class_super(self):
        ctx.eval('''
        class C1 {
            constructor() {this.id = 1}
            method() {return 2}
        }
        var c1 = new C1()''')
        ctx.append('''
        class C2 extends C1 {
            constructor() {
                super()
                this.id += super.method()}
        }
        ''')
        self.assertEqual(ctx.eval('new C2().id'), 3)
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('''
            var c3 = new C3()
            class C3 {}''')

    @skip_or_reinit
    def test_09_type_symbol(self):
        ctx.eval('''
        var sym1 = Symbol('foo')
        var sym2 = Symbol('foo')''')
        self.assertFalse(ctx.eval('sym1 === sym2'))
        _ctx = JSEngine()
        with self.assertRaises(self.expected_exceptions):
            _ctx.eval('new Symbol()')

    @skip_or_reinit
    def test_10_type_set_map(self):
        ctx.eval('''
        new Set()
        new Map()''')

    @skip_or_reinit
    def test_11_type_typedarray(self):
        ctx.eval('''
        new Int8Array(2)
        new Uint8Array(2)
        new Uint8ClampedArray(2)
        new Int16Array(2)
        new Uint16Array(2)
        new Int32Array(2)
        new Uint32Array(2)
        new Float32Array(2)
        new Float64Array(2)''')

    @skip_or_reinit
    def test_12_deconstruction(self):
        ctx.eval('''
        var arr = [1, 2, 3]
        var [n1, n2, n3] = arr''')
        ctx.eval('''
        var obj = {id1: 1, id2: 2, id3: 3}
        var {id1, id2, id3} = obj''')
        ctx.eval('''
        var [n1, n2, n3, n4] = arr
        var n1 = undefined
        var [n1] = arr''')
        ctx.eval('''
        var {id1, id2, id3, id4} = obj
        var id1 = undefined
        var {id1} = obj''')
        self.assertEqual(ctx.eval('n1'), 1)
        self.assertEqual(ctx.eval('n4'), None)
        self.assertEqual(ctx.eval('id1'), 1)
        self.assertEqual(ctx.eval('id4'), None)

    @skip_or_reinit
    def test_13_string_template(self):
        self.assertEqual(ctx.eval('''
`123
456`'''), '123\n456')
        self.assertEqual(ctx.eval('`123456${3 + 4}`'), '1234567')

    @skip_or_reinit
    def test_14_literal(self):
        self.assertEqual(ctx.eval('0b11'), 3)
        self.assertEqual(ctx.eval('0B11'), 3)
        self.assertEqual(ctx.eval('0o11'), 9)
        self.assertEqual(ctx.eval('0O11'), 9)

    @skip_or_reinit
    def test_95_engine_scope(self):
        ctx.eval('let escope = 5')
        self.assertEqual(ctx.eval('escope'), 5)

    @skip_or_reinit
    def test_96_engine_threading(self):
        set_threading(True)
        try:
            _ctx = JSEngine('''
            function ping(o) {
                return o
            }''')

            class TT(threading.Thread):
                def run(s):
                    for i in range(9):
                        self.assertEqual(_ctx.call('ping', i), i)

            t_list = []
            for _ in range(9):
                t = TT()
                t.daemon = True
                t.start()
                t_list.append(t)
            for p in t_list:
                p.join()
        finally:
            set_threading(False)

    @skip_or_reinit
    def test_97_engine_in_out_string(self):
        us = u'αβγ'
        rs = u'"αβγ"'
        self.assertEqual(ctx.eval('"αβγ"'), us)
        self.assertEqual(ctx.eval(rs), us)
        self.assertEqual(ctx.eval(rs.encode('utf8')), us)
        self.assertEqual(ctx.eval(bytearray(rs.encode('utf8'))), us)
        ctx.append('''
        function ping(s1, s2, s3, s4) {
            return [s1, s2, s3, s4]
        }''')
        self.assertEqual(ctx.call('ping', 'αβγ',
                                          us,
                                          us.encode('utf8'),
                                bytearray(us.encode('utf8'))), [us] * 4)

    @skip_or_reinit
    def test_98_return_none(self):
        self.assertEqual(ctx.eval('null'), None)
        self.assertEqual(ctx.eval('undefined'), None)

    @skip_or_reinit
    def test_99_engine_get_source(self):
        if print_source_code:
            print('\nSOURCE CODE:')
            print(ctx.source)
            print('SOURCE CODE END\n')
        else:
            ctx.source

    #@skip_or_reinit
    #def test_FF_performance(self):
    #    if JSEngine is ExternalJSEngine:
    #        return
    #    ctx.eval('for ( let i = 1; i < 1e7; i ++ ) { i + 1 }')


def test_engine(engine):
    global JSEngine, ctx
    name = engine.__name__
    if engine is ExternalJSEngine:
        name += str(jsengine._d.external_interpreter)
    print('\nStart test %s' % name)
    JSEngine = engine
    ctx = None
    unittest.TestProgram(exit=False)
    print('End test %s\n' % name)
    
def test_main(external_interpreters):
    print('Default JSEngine is %r' % jsengine.JSEngine)
    print('Default external_interpreter is %r' % jsengine._d.external_interpreter)

    for JSEngine in (V8JSEngine, ChakraJSEngine, QuickJSEngine):
        test_engine(JSEngine)

    for external_interpreter in external_interpreters:
        if set_external_interpreter(external_interpreter):
            test_engine(ExternalJSEngine)

    if platform.system() == 'Windows':
        import msvcrt
        print('Press any key to continue ...')
        msvcrt.getch()

default_external_interpreters = [
    # test passed
    'chakra',       # ChakraCore
    'cjs',          # CJS
    'gjs',          # Gjs
    'jsc',          # JavaScriptCore
    'node',         # Node.js
    'nodejs',       # Node.js
    'qjs',          # QuickJS
    'spidermonkey', # SpiderMonkey
    'xst',          # XS

    # test passed, but unceremonious names
    #'ch',          # ChakraCore
    #'js',          # SpiderMonkey
    #'d8',          # V8
    #'xs':          # XS

    # test failed
    #'duk',         # Duktape
    #'hermes',      # Hermes
    #'cscript',     # JScript
    #'phantomjs',   # PhantomJS
]


if __name__ == '__main__':
    import sys
    try:
        sys.argv.remove('-psc')
    except ValueError:
        pass
    else:
        print_source_code = True
    external_interpreters = sys.argv[1:] or default_external_interpreters
    del sys.argv[1:]  # clear arguments
    test_main(external_interpreters)
