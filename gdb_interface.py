import gdb
import wl_data as wl
import session as wl_session

# # libwayland client functions
# wl_proxy_marshal
# wl_proxy_destroy
# wl_proxy_marshal_constructor

def gdb_is_null(val):
    return str(val) == '0x0'

type_codes = {i: True for i in ['i', 'u', 'f', 's', 'o', 'n', 'a', 'h']}

def process_closure(session, closure, send):
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
    session.message(message)

class WlClosureCallBreakpoint(gdb.Breakpoint):
    def __init__(self, session, name, send):
        super().__init__('wl_closure_' + name)
        self.session = session
        self.send = send
    def stop(self):
        closure = gdb.selected_frame().read_var('closure')
        process_closure(self.session, closure, self.send)
        return False

def main(matcher):
    gdb.execute('set python print-stack full')
    session = wl_session.Session(matcher)
    WlClosureCallBreakpoint(session, 'invoke', False)
    WlClosureCallBreakpoint(session, 'dispatch', False)
    WlClosureCallBreakpoint(session, 'send', True)
    WlClosureCallBreakpoint(session, 'queue', True)
    gdb.write('breakpoints: ' + repr(gdb.breakpoints()) + '\n')
    gdb.write('GDB main\n')
