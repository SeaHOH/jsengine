from jsengine.util import to_unicode, json_encoder, lockmethod
import threading


# Some simple compatibility processing
init_global_script = u'''\
if (typeof global === 'undefined')
    if (typeof Proxy === 'function')
        global = new Proxy(this, {})
    else
        global = this
if (typeof globalThis === 'undefined')
    globalThis = this
'''

init_del_gobject_script = u'''\
if (typeof {gobject} !== 'undefined')
    delete {gobject}
'''


class AbstractJSEngine(object):  # Just a naming, no abc

    threading = False

    def __init__(self, source=u'', init_global=False, init_del_gobjects=[]):
        '''Create a JSEngine content.

        Params:
            source:
                any valid Javescript.
            init_global:
                set True to ensure `global` and `globalThis` are available.
            init_del_gobjects:
                use to delete some variables in the global.
        '''
        if self.threading:
            self._lock = threading.RLock()
        else:
            self._lock = None
        self._source = []
        self._stand_source = []
        init_script = []
        if init_global:
            init_script.append(init_global_script)
        if init_del_gobjects:
            for gobject in init_del_gobjects:
                init_script.append(init_del_gobject_script.format(gobject=gobject))
        self.append(u''.join(init_script))
        self.append(source)

    @property
    @lockmethod
    def source(self):
        '''All the inputted Javascript code.'''
        self._append_stand_source()
        return u'\n'.join(self._source)

    @staticmethod
    def _check_code(code, last_source):
        # Input unicode
        code = to_unicode(code)
        first_c = code.lstrip()[:1]
        if first_c:
            # Simple separator check
            last_c = last_source and last_source[-1].rstrip()[-1:]
            if last_c and (first_c in u'([`/' and last_c.isdecimal() or
                           first_c in u'`/' and last_c not in u',;}+-*/%!=<>&|'):
                code = u';' + code
            return code

    def _append_stand_source(self):
        if self._stand_source:
            code = u'\n'.join(self._stand_source)
            self._stand_source = []
            self._source.append(code)
            self._append(code)

    @lockmethod
    def append(self, code):
        '''Run Javascript code and return none.'''
        code = self._check_code(code, self._stand_source or self._source)
        if code:
            self._stand_source.append(code)

    @lockmethod
    def eval(self, code):
        '''Run Javascript code and return result.'''
        self._append_stand_source()
        code = self._check_code(code, self._source)
        if code:
            if code[-1] != u';':
                code += u';'  # eval code MUST be standalone
            self._source.append(code)
            return self._eval(code)

    @lockmethod
    def call(self, identifier, *args):
        '''Use name string and arguments to call Javascript function.'''
        chunks = json_encoder.iterencode(args, _one_shot=True)
        chunks = [to_unicode(chunk) for chunk in chunks]
        args = u''.join(chunks)[1:-1]
        code = u'{identifier}({args})'.format(**vars())
        return self.eval(code)

    def _append(self, code):
        pass

    def _eval(self, code):
        raise NotImplementedError('Method must be implemented by subclass')
