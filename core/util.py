import sys
import re
import os
import types
import logging
import time
from typing import Any, Optional

def check_gdb() -> bool:
    '''Check if the gdb module is available, and thus if we are inside a running instance of GDB'''
    import importlib.util
    return importlib.util.find_spec("gdb") is not None

verbose = False

# if we print with colors and such
color_output = False
timestamp_color = '2;37'
object_type_color = '1;96'
object_id_color = '36'
message_color = '1;94'
symbol_color = None

int_color = '95'
int_symbol_color = '2;35'
float_color = '93'
string_color = '1;33'
fd_color = '35'
array_color = '1;37'
null_color = '1;37'

good_color = '1;92'
bad_color = '1;91'
alert_color = '93'

def set_color_output(val: bool) -> None:
    global color_output
    assert isinstance(val, bool)
    color_output = val

# if string is not None, resets to normal at end
def color(color: Optional[str], string: str) -> str:
    string = str(string)
    result = ''
    if string == '':
        return ''
    if color_output:
        if color is not None:
            result += '\x1b[' + color + 'm'
        else:
            result += '\x1b[0m'
    if string:
        result += string
        if color_output and color:
            result += '\x1b[0m'
    return result

def no_color(string: str) -> str:
    return re.sub(r'\x1b\[[\d;]*m', '', string)

def set_verbose(new_verbose: bool) -> None:
    global verbose
    verbose = new_verbose
    logging.getLogger().setLevel(logging.DEBUG if new_verbose else logging.WARN)

cached_project_root = None
def project_root() -> str:
    global cached_project_root
    if not cached_project_root:
        cached_project_root = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    return cached_project_root

def generate_disseminator(Listener: type) -> type:
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
    setattr(Listener, 'Disseminator', diss_class)

    def init(self, *args, **kwargs):
        super(diss_class, self).__init__(*args, **kwargs)
        self.listeners = []
    setattr(diss_class, '__init__', init)

    return Listener

def new_disseminator_of_type(Listener: type, *args, **kwargs) -> Any:
    '''Creates a Disseminator for the given listener interface.
    The disseminator implements that interface, and will relay calls to an arbitrary number of listeners.
    Use disseminator.add_listener(listener) and disseminator.remove_listener(listener) to control notifications.
    '''
    if not hasattr(Listener, 'Disseminator'):
        generate_disseminator(Listener)
    return getattr(Listener, 'Disseminator')(*args, **kwargs)

def time_now() -> float:
    return time.perf_counter()

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
