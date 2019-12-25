import sys
import re
import os
import types

def check_gdb():
    '''Check if the gdb module is available, and thus if we are inside a running instance of GDB'''
    import importlib.util
    return importlib.util.find_spec("gdb") is not None

verbose = False

# if we print with colors and such
color_output = False
timestamp_color = '37'
object_color = '1;37'
message_color = None

def set_color_output(val):
    global color_output
    assert isinstance(val, bool)
    color_output = val

# if string is not None, resets to normal at end
def color(color, string):
    string = str(string)
    result = ''
    if string == '':
        return ''
    if color_output:
        if color:
            result += '\x1b[' + color + 'm'
        else:
            result += '\x1b[0m'
    if string:
        result += string
        if color_output and color:
            result += '\x1b[0m'
    return result

def no_color(string):
    return re.sub('\x1b\[[\d;]*m', '', string)

def log(msg):
    if verbose:
        if check_gdb():
            print(color('1;34', 'wl log: '), end='')
        print(color('37', str(msg)))

def set_verbose(val):
    global verbose
    assert isinstance(val, bool)
    verbose = val

def warning(msg):
    print(color('1;33', 'Warning: ') + str(msg))

def str_matches(pattern, txt):
    assert isinstance(pattern, str)
    assert isinstance(txt, str)
    pattern = re.escape(pattern)
    pattern = pattern.replace('\*', '.*')
    pattern = '^' + pattern + '$'
    return len(re.findall(pattern, txt)) == 1

cached_project_root = None
def project_root():
    global cached_project_root
    if not cached_project_root:
        cached_project_root = os.path.dirname(os.path.realpath(__file__))
    return cached_project_root

def generate_disseminator(Listener):
    assert isinstance(Listener, type)
    assert not hasattr(Listener, 'Disseminator')

    class_name = Listener.__name__ + 'Disseminator'
    class_dict = {}

    # Must wrap disseminate in a function as so because the name varibale can only have one value per stack frame
    def generate_method(name):
        def disseminate(self, *args, **kwargs):
            for listener in self.listeners:
                getattr(listener, name)(*args, **kwargs)
        return disseminate

    for name, value in Listener.__dict__.items():
        if isinstance(value, types.FunctionType) and not name.startswith('_'):
            class_dict[name] = generate_method(name)

    def add_listener(self, listener):
        assert isinstance(listener, Listener)
        for l in self.listeners:
            assert listener != l
        self.listeners.append(listener)
    class_dict['add_listener'] = add_listener

    def remove_listener(self, listener):
        self.listeners.remove(listener)
    class_dict['remove_listener'] = remove_listener

    diss_class = type(class_name, (Listener,), class_dict)
    Listener.Disseminator = diss_class

    def init(self, *args, **kwargs):
        super(diss_class, self).__init__(*args, **kwargs)
        self.listeners = []
    diss_class.__init__ = init

    return Listener

def new_disseminator_of_type(Listener, *args, **kwargs):
    '''Creates a Disseminator for the given listener interface.
    The disseminator implements that interface, and will relay calls to an arbitrary number of listeners.
    Use disseminator.add_listener(listener) and disseminator.remove_listener(listener) to control notifications.
    '''
    if not hasattr(Listener, 'Disseminator'):
        generate_disseminator(Listener)
    return Listener.Disseminator(*args, **kwargs)

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
