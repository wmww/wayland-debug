import gdb
import wl_data as wl
import session as wl_session

# # libwayland client functions
# wl_proxy_marshal
# wl_proxy_destroy
# wl_proxy_marshal_constructor

def gdb_not_null(val):
    try:
        val.dereference()
        val.fetch_lazy()
        return True
    except:
        return False

def process_closure(session, closure, send):
    obj_id = int(closure['sender_id'])
    proxy_class = None
    if not send:
        proxy = closure['proxy']
        proxy_obj = proxy['object']
        proxy_class = proxy_obj['interface']['name'].string()
    message_name = closure['message']['name'].string()

    message = wl.Message(0, obj_id, proxy_class, send, message_name, [])
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
