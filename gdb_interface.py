import subprocess
import time
import gdb
import wl_data as wl
import session as wl_session
import matcher as wl_matcher
import re

# # libwayland client functions
# wl_proxy_marshal
# wl_proxy_destroy
# wl_proxy_marshal_constructor

def gdb_is_null(val):
    return str(val) == '0x0'

type_codes = {i: True for i in ['i', 'u', 'f', 's', 'o', 'n', 'a', 'h']}

def process_closure(send):
    closure = gdb.selected_frame().read_var('closure')
    wl_object = None
    connection = None
    try:
        connection = gdb.selected_frame().read_var('connection')
    except ValueError:
        if int(gdb.selected_frame().read_var('flags')) == 1:
            proxy = closure['proxy']
            wl_object = proxy['object']
            connection = proxy['display']['connection']
        else:
            target = gdb.selected_frame().read_var('target')
            resource_type = gdb.lookup_type('struct wl_resource').pointer()
            resource = target.cast(resource_type)
            wl_object = resource['object']
            connection = resource['client']['connection']
    connection_addr = str(connection)
    obj_id = int(closure['sender_id'])
    obj_type = None
    if wl_object:
        obj_type = wl_object['interface']['name'].string()
    closure_message = closure['message']
    message_name = closure_message['name'].string()
    # The signiture is that stupid '2uufo?i' thing that has the type info
    signiture = closure_message['signature'].string()
    message_types = closure_message['types']
    closure_args = closure['args']
    args = []
    i = 0
    for c in signiture:
        # If its not a version number or '?' optional indicator
        if c in type_codes:
            # Pull out the right union member at the right index
            value = closure_args[i][c]
            if c == 'i' or c == 'u':
                args.append(wl.Arg.Int(int(value)))
            elif c == 'f':
                # Math is ripped out of wl_fixed_to_double() in libwayland
                f = float(gdb.parse_and_eval('(double)(void*)(((1023LL + 44LL) << 52) + (1LL << 51) + ' + str(value) + ') - (3LL << 43)'))
                args.append(wl.Arg.Float(f))
            elif c == 's':
                args.append(wl.Arg.String(value.string()))
            elif c == 'a':
                args.append(wl.Arg.Unknown('array'))
            elif c == 'h':
                args.append(wl.Arg.Fd(int(value)))
            else:
                assert c == 'n' or c == 'o'
                arg_type = message_types[i]
                arg_type_name = None
                if not gdb_is_null(arg_type):
                    arg_type_name = arg_type['name'].string()
                if gdb_is_null(value):
                    assert c == 'o'
                    args.append(wl.Arg.Null(arg_type_name))
                else:
                    if c == 'n':
                        arg_id = int(value)
                        is_new = True
                    else:
                        arg_id = int(value['id'])
                        is_new = False
                    args.append(wl.Arg.Object(wl.Object.Unresolved(arg_id, arg_type_name), is_new))
            i += 1
    timestamp = time.perf_counter()
    message = wl.Message(timestamp, wl.Object.Unresolved(obj_id, obj_type), send, message_name, args)
    return (connection_addr, message)

def invoke_wl_command(session, cmd):
    session.set_stopped(True)
    session.command(cmd)
    if session.quit():
        gdb.execute('quit')
    elif not session.stopped():
        gdb.execute('continue')

class WlConnectionDestroyBreakpoint(gdb.Breakpoint):
    def __init__(self, session):
        super().__init__('wl_connection_destroy', internal=True)
        self.session = session
    def stop(self):
        connection_id = str(gdb.selected_frame().read_var('connection'))
        self.session.close_connection(connection_id, 0)
        return False

class WlConnectionCreateBreakpoint(gdb.Breakpoint):
    def __init__(self, session):
        super().__init__('wl_connection_create', internal=True)
        self.session = session
    def stop(self):
        self.FinishBreakpoint(self.session)
        return False

    class FinishBreakpoint(gdb.FinishBreakpoint):
        def __init__(self, session):
            super().__init__(gdb.selected_frame(), internal=True)
            self.session = session
        def stop(self):
            connection_id = str(self.return_value)
            calling_function = str(gdb.selected_frame().function())
            if calling_function == 'wl_display_connect_to_fd':
                is_server = False
            elif calling_function == 'wl_client_create':
                is_server = True
            else:
                self.session.out.warn('Function ' + calling_function + '() called wl_connection_create()')
                is_server = None
            self.session.open_connection(connection_id, is_server, 0)
            return False

class WlClosureCallBreakpoint(gdb.Breakpoint):
    def __init__(self, session, name, send):
        super().__init__('wl_closure_' + name, internal=True)
        self.session = session
        self.send = send
    def stop(self):
        connection_id, message = process_closure(self.send)
        self.session.message(connection_id, message)
        return self.session.stopped()

class WlCommand(gdb.Command):
    'Issue a subcommand to Wayland Debug, use \'wl help\' for details'
    def __init__(self, name, session):
        super().__init__(name, gdb.COMMAND_DATA)
        self.session = session
    def invoke(self, arg, from_tty):
        invoke_wl_command(self.session, arg)
    def complete(text, word):
        return None

class WlSubcommand(gdb.Command):
    'A Wayland debug command, use \'wl help\' for detail'
    def __init__(self, name, session):
        super().__init__('wl' + name, gdb.COMMAND_DATA)
        self.session = session
        self.cmd = name
    def invoke(self, arg, from_tty):
        invoke_wl_command(self.session, self.cmd + ' ' + arg)
    def complete(text, word):
        return None

def load_libwayland_symbols(session):
    # First, we use ldconfig to find libwayland
    cmd = ['ldconfig', '-p']
    session.out.log('Running `' + ' '.join(cmd) + '`')
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sp.communicate()
    stdout = stdout.decode('utf-8') if stdout != None else ''
    if sp.returncode != 0:
        raise RuntimeError('`' + ' '.join(cmd) + '` exited with code ' + str(sp.returncode))
    # pull out libwayland-client and libwayland-server from the output of ldconfig
    result = re.findall('(libwayland\-(client|server).so) .*=> (/.*)[\n$]', stdout)
    if len(result) == 0:
        raise RuntimeError('Output of `' + ' '.join(cmd) + '` did not contain any Wayland libraries')
    else:
        session.out.log('Found ' + str(len(result)) + ' Wayland libraries')
    libwayland_paths = [i[2] for i in result]
    for path in libwayland_paths:
        session.out.log('Loading debug symbols from ' + path)
        result = gdb.execute('add-symbol-file ' + path, to_string=True)
        if result != 'add symbol table from file "' + path + '"\n':
            session.out.warn('Issue adding libwayland symbol file ' + path + ', output was ' + result)

def check_libwayland_symbols(session):
    def check_symbol(symbol, lib):
        if gdb.lookup_global_symbol(symbol) is None:
            session.out.log(symbol + ' was supposed to be in ' + lib + ', but was not detected')
            session.out.error(lib + ' debug symbols not detected')
            return False
        else:
            session.out.log(lib + ' debug symbols detected')
            return True
    client = check_symbol('wl_proxy_create', 'libwayland-client')
    server = check_symbol('wl_display_add_global', 'libwayland-server')
    return client and server


def main(session):
    gdb.execute('set python print-stack full')
    if not session.out.show_unprocessed:
        gdb.execute('set inferior-tty /dev/null')
    try:
        # GDB will automatically load the symbols when needed, but if we do it first we get to detect problems
        load_libwayland_symbols(session)
    except RuntimeError as e:
        session.out.warn('Loading libwayland symbols failed: ' + str(e))
    WlConnectionCreateBreakpoint(session)
    WlConnectionDestroyBreakpoint(session)
    WlClosureCallBreakpoint(session, 'invoke', False)
    WlClosureCallBreakpoint(session, 'dispatch', False)
    WlClosureCallBreakpoint(session, 'send', True)
    WlClosureCallBreakpoint(session, 'queue', True)
    WlCommand('w', session)
    WlCommand('wl', session)
    WlCommand('wayland', session)
    for c in session.commands:
        WlSubcommand(c.name, session)
    session.out.log('Breakpoints: ' + repr(gdb.breakpoints()))
    if not check_libwayland_symbols(session):
        session.out.warn('All debug symbols were not found, so Wayland messages may not be detected in GDB mode')
        session.out.warn('Depending on your distro, please install the *-dbgsym package, compile libwayland without stripping, etc')
