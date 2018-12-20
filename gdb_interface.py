import gdb
import wl_data as wl
import session as wl_session
import matcher as wl_matcher
from gdb_runner import check_libwayland

# # libwayland client functions
# wl_proxy_marshal
# wl_proxy_destroy
# wl_proxy_marshal_constructor

def gdb_is_null(val):
    return str(val) == '0x0'

type_codes = {i: True for i in ['i', 'u', 'f', 's', 'o', 'n', 'a', 'h']}

def process_closure(closure, send):
    obj_id = int(closure['sender_id'])
    proxy_class = None
    if not send:
        proxy = closure['proxy']
        proxy_obj = proxy['object']
        proxy_class = proxy_obj['interface']['name'].string()
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
                args.append(wl.Arg.Primitive(int(value)))
            elif c == 'f':
                # Math is ripped out of wl_fixed_to_double() in libwayland
                # This may be my favorite line of code I've ever written
                f = float(gdb.parse_and_eval('(double)(void*)(((1023LL + 44LL) << 52) + (1LL << 51) + ' + str(value) + ') - (3LL << 43)'))
                args.append(wl.Arg.Primitive(f))
            elif c == 's':
                args.append(wl.Arg.Primitive(value.string()))
            elif c == 'a':
                args.append(wl.Arg.Unknown('array'))
            elif c == 'h':
                args.append(wl.Arg.Fd(int(value)))
            elif gdb_is_null(value):
                assert c == 'o'
                args.append(wl.Arg.Primitive(None))
            else:
                assert c == 'n' or c == 'o'
                arg_type = message_types[i]
                arg_type_name = None
                if not gdb_is_null(arg_type):
                    arg_type_name = arg_type['name'].string()
                if c == 'n':
                    arg_id = int(value)
                else:
                    arg_id = int(value['id'])
                args.append(wl.Arg.Object(arg_id, arg_type_name, c == 'n'))
            i += 1

    message = wl.Message(0, obj_id, proxy_class, send, message_name, args)
    return message

def invoke_wl_command(session, cmd):
    session.set_stopped(True)
    session.command(cmd)
    if session.quit():
        gdb.execute('quit')
    elif not session.stopped():
        gdb.execute('continue')

class WlClosureCallBreakpoint(gdb.Breakpoint):
    def __init__(self, session, name, send):
        super().__init__('wl_closure_' + name)
        self.session = session
        self.send = send
    def stop(self):
        closure = gdb.selected_frame().read_var('closure')
        message = process_closure(closure, self.send)
        self.session.message(message)
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

def main(session):
    gdb.execute('set python print-stack full')
    if not session.out.show_unprocessed:
        gdb.execute('set inferior-tty /dev/null')
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
    try:
        result = check_libwayland()
        if result == None:
            session.out.log('libwayland found with debug symbols')
        else:
            session.out.log(result)
            session.out.error('Installed libwayland lacks debug symbols, GDB mode will not function')
    except RuntimeError as e:
        session.out.warn('Checking libwayland failed: ' + str(e))
