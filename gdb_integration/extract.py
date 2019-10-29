import gdb
import wl

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

def closure():
    '''Returns the closure pointer for the current stack frame'''
    return gdb.selected_frame().read_var('closure')

def object(closure):
    '''Returns a tuple containing…
    Connection ID: str, specifically the address of the connection struct
    Object ID: int, the Wayland object ID of the object the current method was called on
    Object Type: str or None, the type of the object, or None if it is not known
    '''
    wl_object = None
    try:
        connection = gdb.selected_frame().read_var('connection')
    except ValueError:
        if int(gdb.selected_frame().read_var('flags')) == 1:
            proxy = _fast_access(closure, 'proxy')
            wl_object = _fast_access(proxy, 'object')
            wl_display = _fast_access(proxy, 'display')
            connection = _fast_access(wl_display, 'connection')
        else:
            target = gdb.selected_frame().read_var('target')
            resource_type = gdb.lookup_type('struct wl_resource').pointer()
            resource = target.cast(resource_type)
            wl_object = resource['object']
            connection = resource['client']['connection']
    connection_id = str(connection)
    obj_id = int(closure['sender_id'])
    if wl_object:
        obj_type = _fast_access(wl_object['interface'], 'name').string()
    else:
        obj_type = None
    return (connection_id, obj_id, obj_type)

def message(closure):
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
    return (message_name, args)

