from jsengine.util import to_unicode, json_encoder


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


class AbstractJSEngine(object):
    def __init__(self, source=u'', init_global=False, init_del_gobjects=None):
        self._source = []
        init_script = []
        if init_global:
            init_script.append(init_global_script)
        if init_del_gobjects:
            for gobject in init_del_gobjects:
                init_script.append(init_del_gobject_script.format(gobject=gobject))
        self._source.append(u''.join(init_script))
        self.append(source)

    @property
    def source(self):
        '''All the inputted Javascript code.'''
        return u'\n'.join(self._source)

    def _append_source(self, code):
        if code:
            self._source.append(code)

    def _check_code(self, code):
        # Input unicode
        code = to_unicode(code)
        first_c = code.lstrip()[:1]
        if first_c:
            # Simple separator check
            last_c = self._source and self._source[-1].rstrip()[-1:] or ''
            if last_c and (first_c in u'([`/' and last_c.isdecimal() or
                           first_c in u'`/' and last_c not in ',;}+-*/%!=<>&|'):
                code = u';' + code
            return code

    def append(self, code):
        '''Run Javascript code and return none.'''
        code = self._check_code(code)
        if code:
            self._append(code)

    def eval(self, code):
        '''Run Javascript code and return result.'''
        code = self._check_code(code)
        if code:
            return self._eval(code)

    def call(self, identifier, *args):
        '''Use name string and arguments to call Javascript function.'''
        chunks = json_encoder.iterencode(args, _one_shot=True)
        chunks = [to_unicode(chunk) for chunk in chunks]
        args = u''.join(chunks)[1:-1]
        code = u'{identifier}({args})'.format(**vars())
        return self._eval(code)

    def _append(self, code):
        raise NotImplementedError('Method must be implemented by subclass')

    def _eval(self, code):
        raise NotImplementedError('Method must be implemented by subclass')
