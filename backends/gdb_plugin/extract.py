import gdb

from core import wl
from core.util import time_now

type_codes = {i: True for i in ['i', 'u', 'f', 's', 'o', 'n', 'a', 'h']}

gdb_fast_access_map = {}
gdb_char_ptr_type = gdb.lookup_type('char').pointer()

# Check if a GDB value is null
# (there should be a better way, but I don't think there is)
def _is_null(val):
    return str(val) == '0x0'

# Like normal GDB property access,
# except caches the poitner offset of fields on types to make future lookups faster
# (measurably improves performance)
def _fast_access(value, field_name):
    assert value.type.code == gdb.TYPE_CODE_PTR
    assert value.type.target().name
    key = (value.type.target().name, field_name)
    if not key in gdb_fast_access_map:
        found = False
        for field in value.type.target().fields():
            if field.name == field_name:
                assert field.bitpos % 8 == 0
                gdb_fast_access_map[key] = (field.bitpos // 8, field.type.pointer())
                found = True
                break
        assert found
    offset, ret_type_ptr_ptr = gdb_fast_access_map[key]
    return (value.cast(gdb_char_ptr_type) + offset).cast(ret_type_ptr_ptr).dereference()

def extract_message(closure, object, is_sending):
    '''Returns a tuple containing…
    Message Name: str, the message being called
    Arguments: list of wl.Arg
    '''
    closure_message = _fast_access(closure, 'message')
    message_name = _fast_access(closure_message, 'name').string()
    # The signiture is that stupid '2uufo?i' thing that has the type info
    signiture = _fast_access(closure_message, 'signature').string()
    message_types = _fast_access(closure_message, 'types')
    closure_args = _fast_access(closure, 'args')
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
                if _is_null(value):
                    str_val = '[null string]'
                else:
                    str_val = value.string()
                args.append(wl.Arg.String(str_val))
            elif c == 'a':
                size = int(value['size'])
                elems = []
                int_type = gdb.lookup_type('int')
                for i in range(size // int_type.sizeof):
                    elem = value['data'].cast(int_type.pointer())[i]
                    elems.append(wl.Arg.Int(int(elem)))
                args.append(wl.Arg.Array(elems))
            elif c == 'h':
                args.append(wl.Arg.Fd(int(value)))
            else:
                assert c == 'n' or c == 'o'
                arg_type = message_types[i]
                arg_type_name = None
                if not _is_null(arg_type):
                    arg_type_name = arg_type['name'].string()
                if _is_null(value):
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
    return wl.Message(time_now(), object, is_sending, message_name, args)

def received_message():
    closure = gdb.selected_frame().read_var('closure')
    proxy = _fast_access(closure, 'proxy')
    if not _is_null(proxy):
        wl_object = _fast_access(proxy, 'object')
        wl_display = _fast_access(proxy, 'display')
        connection = _fast_access(wl_display, 'connection')
    else:
        wl_object = gdb.selected_frame().read_var('target')
        resource_type = gdb.lookup_type('struct wl_resource').pointer()
        resource = wl_object.cast(resource_type)
        connection = resource['client']['connection']
    connection_id = str(connection)
    object_id = int(closure['sender_id'])
    obj_type = _fast_access(wl_object['interface'], 'name').string()
    object = wl.Object.Unresolved(object_id, obj_type)
    message = extract_message(closure, object, False)
    return connection_id, message

def sent_message():
    closure = gdb.selected_frame().read_var('closure')
    # closure -> proxy is always null in wl_closure_send and wl_closure_queue
    connection = gdb.selected_frame().read_var('connection')
    connection_id = str(connection)
    object_id = int(closure['sender_id'])
    object = wl.Object.Unresolved(object_id, None)
    message = extract_message(closure, object, True)
    return connection_id, message
