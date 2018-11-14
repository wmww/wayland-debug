import gdb

# # libwayland client functions
# wl_proxy_marshal
# wl_proxy_destroy
# wl_proxy_marshal_constructor

def proxy_to_str(proxy):
    # gdb.parse_and_eval('wl_proxy_get_class(proxy)')
    proxy_id = proxy['object']['id']
    proxy_class = proxy['object']['interface']['name'].string()
    return str(proxy_class) + '@' + str(int(proxy_id))

class WlProxyCreateBp(gdb.Breakpoint):
    def __init__(self):
        super().__init__('wl_proxy_create')
    def stop(self):
        gdb.write('Created proxy with ID ' + str(int(gdb.parse_and_eval('wl_proxy_get_id(proxy)'))) + '\n')
        return False

class WlProxyMarshalBp(gdb.Breakpoint):
    def __init__(self):
        super().__init__('wl_proxy_marshal')
    def stop(self):
        proxy = gdb.selected_frame().read_var('proxy')
        gdb.write('wl_proxy_marshal(proxy: ' + proxy_to_str(proxy) + ')\n')
        return False

class WlProxyMarshalConstructorBp(gdb.Breakpoint):
    def __init__(self):
        super().__init__('wl_proxy_marshal_constructor')
    def stop(self):
        # return True
        proxy = gdb.selected_frame().read_var('proxy')
        gdb.write('wl_proxy_marshal_constructor(proxy: ' + proxy_to_str(proxy) + ')\n')
        return False

def main(matcher):
    gdb.execute('set python print-stack full')
    WlProxyCreateBp()
    WlProxyMarshalBp()
    WlProxyMarshalConstructorBp()
    gdb.write('breakpoints: ' + repr(gdb.breakpoints()) + '\n')
    gdb.write('GDB main\n')
