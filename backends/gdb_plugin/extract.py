import gdb

from core import wl
from core.util import time_now

type_codes = {i: True for i in ['i', 'u', 'f', 's', 'o', 'n', 'a', 'h']}

wl_resource_ptr_type = None
gdb_fast_access_map = {}
gdb_char_ptr_type = gdb.lookup_type('char').pointer()

# Check if a GDB value is null
# (there should be a better way, but I don't think there is)
def _is_null(val):
    return str(val) == '0x0'

def lazy_get_wl_resource_ptr_type():
    global wl_resource_ptr_type
    if wl_resource_ptr_type is None:
        wl_resource_ptr_type = gdb.lookup_type('struct wl_resource').pointer()
    return wl_resource_ptr_type

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

def extract_message(closure, object, is_sending, new_id_is_actually_an_object):
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
            elif c == 'o':
                arg_type = message_types[i]
                if _is_null(arg_type):
                    arg_type_name = None
                else:
                    arg_type_name = arg_type['name'].string()
                if _is_null(value):
                    args.append(wl.Arg.Null(arg_type_name))
                else:
                    arg_id = int(_fast_access(value, 'id'))
                    args.append(wl.Arg.Object(wl.Object.Unresolved(arg_id, arg_type_name), False))
            elif c == 'n':
                arg_type = message_types[i]
                if _is_null(arg_type):
                    arg_type_name = None
                else:
                    arg_type_name = arg_type['name'].string()
                if new_id_is_actually_an_object:
                    arg_id = int(_fast_access(closure_args[i]['o'], 'id'))
                else:
                    arg_id = int(value)
                args.append(wl.Arg.Object(wl.Object.Unresolved(arg_id, arg_type_name), True))
            else:
                raise RuntimeError('Invalid type code ' + c)
            i += 1
    return wl.Message(time_now(), object, is_sending, message_name, args)

def received_message():
    frame = gdb.selected_frame()
    closure = frame.read_var('closure')
    wl_object = frame.read_var('target')
    calling_func = frame.older().name()
    # NOTE: closure->proxy is often null but technically undefined in the server case
    # Using it to detect server vs client works for the tests but fails on Mir
    if calling_func == 'dispatch_event':
        # Client connection
        new_id_is_actually_an_object = True
        proxy = _fast_access(closure, 'proxy')
        wl_display = _fast_access(proxy, 'display')
        connection = _fast_access(wl_display, 'connection')
    elif calling_func == 'wl_client_connection_data':
        # Server connection
        new_id_is_actually_an_object = False
        resource_type = lazy_get_wl_resource_ptr_type()
        resource = wl_object.cast(resource_type)
        connection = _fast_access(_fast_access(resource, 'client'), 'connection')
    else:
        raise RuntimeError('Unknown libwayland calling function ' + calling_func)
    connection_id = str(connection)
    object_id = int(_fast_access(closure, 'sender_id'))
    # wl_object is not a pointer, so can't use _fast_access() to get interface
    obj_type = _fast_access(wl_object['interface'], 'name').string()
    object = wl.Object.Unresolved(object_id, obj_type)
    message = extract_message(closure, object, False, new_id_is_actually_an_object)
    return connection_id, message

def sent_message():
    frame = gdb.selected_frame()
    closure = frame.read_var('closure')
    # closure -> proxy is always null in wl_closure_send and wl_closure_queue
    connection = frame.read_var('connection')
    connection_id = str(connection)
    object_id = int(_fast_access(closure, 'sender_id'))
    object = wl.Object.Unresolved(object_id, None)
    message = extract_message(closure, object, True, False)
    return connection_id, message
