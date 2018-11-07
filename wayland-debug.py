#!/usr/bin/python3

import sys
import re

verbose = False
unparsable_output = False

base_time = None

# if we print with colors and such
color_output = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()
timestamp_color = '37'
object_color = '1;37'
message_color = None

program_name = 'wayland-debug'
example_usage = 'WAYLAND_DEBUG=1 server-or-client-program 2>&1 1>/dev/null | ' + program_name

# if string is not None, resets to normal at end
def color(color, string):
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

def log(msg):
    if verbose:
        print(color('37', msg))

def warning(msg):
    print(color('1;33', 'Warning: ') + msg)

class WlObject:

    # keys are ids, values are arrays of objects in the order they are created
    db = {}
    display = None
    registry = None

    def look_up_most_recent(obj_id, type_name = None):
        assert obj_id in WlObject.db, 'Id ' + str(obj_id) + ' of type ' + str(type_name) + ' not in object database'
        obj = WlObject.db[obj_id][-1]
        if not obj.alive:
            warning(str(obj) + ' has been destroyed')
        if type_name:
            if obj.type:
                assert obj.type == type_name, 'Object of wrong type'
            # Should work but is not needed
            # else:
            #    obj.type = type_name
        return obj

    def __init__(self, obj_id, type_name, parent_obj, create_time):
        assert(isinstance(obj_id, int))
        if obj_id in self.db:
            assert not self.db[obj_id][-1].alive, 'Tried to create an object with the same ID as an existing one'
        else:
            self.db[obj_id] = []
        self.generation = len(self.db[obj_id])
        self.db[obj_id].append(self)
        self.type = type_name
        self.id = obj_id
        self.parent = parent_obj
        self.create_time = create_time
        self.destroy_time = None
        self.alive = True

    def destroy(self, time):
        self.destroy_time = None
        self.alive = False

    def type_str(self):
        if self.type:
            return self.type
        else:
            return color('1;31', '[unknown]')

    def __str__(self):
        assert self.db[self.id][self.generation] == self, 'Database corrupted'
        return color('1;37', self.type_str() + '@' + str(self.id) + '.' + str(self.generation))

WlObject.display = WlObject(1, 'wl_display', None, 0)

class WlArgs:

    error_color = '2;33'

    # ints, floats, strings and nulls
    class Primitive:
        def __init__(self, value):
            self.value = value
        def __str__(self):
            if isinstance(self.value, int):
                return color('1;34', str(self.value))
            elif isinstance(self.value, float):
                return color('1;35', str(self.value))
            elif isinstance(self.value, str):
                return color('1;33', repr(self.value))
            elif self.value == None:
                return color('37', 'null')
            else:
                return color(WlArgs.error_color, type(self.value).__name__ + ': ' + repr(self.value))

    class Object:
        def __init__(self, obj_id, type_name, is_new):
            self.id = obj_id
            self.type = type_name
            self.is_new = is_new
            self.resolved = False
        def resolve(self, parent_obj, time):
            if self.resolved:
                return True
            if self.is_new:
                self.obj = WlObject(self.id, self.type, parent_obj, time)
            else:
                self.obj = WlObject.look_up_most_recent(self.id, self.type)
            del self.id
            del self.type
            self.resolved = True
        def __str__(self):
            if self.resolved:
                return (color('1;32', 'new ') if self.is_new else '') + str(self.obj)
            else:
                return color(WlArgs.error_color, ('New u' if self.is_new else 'U') + 'nresolved object: ' + self.type + '@' + str(self.id))

    class Fd:
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return color('36', 'fd ' + str(self.value))

    class Unknown:
        def __init__(self, string):
            assert isinstance(string, str)
            self.string = string
        def __str__(self):
            return color(WlArgs.error_color, 'Unknown: ' + repr(self.string))

    def parse_single(value_str):
        int_matches = re.findall('^-?\d+$', value_str)
        if int_matches:
            return WlArgs.Primitive(int(value_str))
        float_matches = re.findall('^-?\d+(\.\d+)?([eE][+-]?\d+)?$', value_str)
        if float_matches:
            return WlArgs.Primitive(float(value_str))
        nil_matches = re.findall('^nil$', value_str)
        if nil_matches:
            return WlArgs.Primitive(None)
        fd_matches = re.findall('^fd (\d+)$', value_str)
        if fd_matches:
            return WlArgs.Fd(int(fd_matches[0]))
        str_matches = re.findall('^"(.*)"$', value_str)
        if str_matches:
            return WlArgs.Primitive(str_matches[0])
        new_id_unknown_matches = re.findall('^new id \[unknown\]@(\d+)$', value_str)
        if new_id_unknown_matches:
            return WlArgs.Object(int(new_id_unknown_matches[0]), None, True)
        new_id_matches = re.findall('^new id (\w+)@(\d+)$', value_str)
        if new_id_matches:
            return WlArgs.Object(int(new_id_matches[0][1]), new_id_matches[0][0], True)
        obj_matches = re.findall('^(\w+)@(\d+)$', value_str)
        if obj_matches:
            return WlArgs.Object(int(obj_matches[0][1]), obj_matches[0][0], False)
        else:
            return WlArgs.Unknown(value_str)

    def parse_list(args_str):
        args = []
        start = 0
        i = 0
        while i <= len(args_str):
            if i == len(args_str) or args_str[i] == ',':
                arg = args_str[start:i].strip()
                if (arg):
                    args.append(WlArgs.parse_single(arg))
                start = i + 1
            elif args_str[i] == '"':
                i += 1
                while args_str[i] != '"':
                    if args_str[i] == '\\':
                        i += 1
                    i += 1
            i += 1
        return args

class WaylandMessage:
    def __init__(self, raw):
        timestamp_regex = '\[(\d+\.\d+)\]'
        message_regex = '(\w+)@(\d+)\.(\w+)\((.*)\)$'
        sent = True
        matches = re.findall(timestamp_regex + '  -> ' + message_regex, raw)
        if not matches:
            sent = False
            matches = re.findall(timestamp_regex + ' ' + message_regex, raw)
        if len(matches) != 1:
            raise RuntimeError(
                'Could not parse "' + raw + '" as Wayland debug message' +
                (' (' + str(len(matches)) + ' regex matches)' if len(matches) > 1 else ''))
        match = matches[0]
        assert isinstance(match, tuple), repr(match)
        abs_timestamp = float(match[0]) / 1000.0
        global base_time
        if base_time == None:
            base_time = abs_timestamp
        timestamp = abs_timestamp - base_time
        type_name = match[1]
        obj_id = int(match[2])
        message_name = match[3]
        message_args_str = match[4]
        message_args = WlArgs.parse_list(message_args_str)
        self.sent = sent
        self.timestamp = timestamp
        self.obj = WlObject.look_up_most_recent(obj_id, type_name)
        self.name = message_name
        self.args = message_args

    def resolve_objects(self):
        if self.obj.type == 'wl_registry' and self.name == 'bind':
            self.args[3].type = self.args[1].value
        if self.obj == WlObject.display and self.name == 'delete_id':
            self.destroyed_obj = WlObject.look_up_most_recent(self.args[0].value, None)
            self.destroyed_obj.destroy(self.timestamp)
        for i in self.args:
            if isinstance(i, WlArgs.Object):
                i.resolve(self.obj, self.timestamp)

    def __str__(self):
        destroyed = ''
        if hasattr(self, 'destroyed_obj'):
            destroyed = (
                color(timestamp_color, ' [') +
                color('1;31', 'destroyed ') +
                str(self.destroyed_obj) +
                color(timestamp_color, ']'))
        return (
            color('37', '{:10.4f}'.format(self.timestamp) + (' →  ' if self.sent else ' ') +
            str(self.obj) + ' ' +
            color(message_color, self.name + '(') +
            color(message_color, ', ').join([str(i) for i in self.args]) + color(message_color, ')')) +
            destroyed +
            color(timestamp_color, ' ↲' if not self.sent else ''))

def main(input_file):
    while True:
        line = input_file.readline()
        if line == '':
            break
        line = line.strip() # be sure to strip after the empty check
        try:
            message = WaylandMessage(line)
            message.resolve_objects()
            print(message)
        except RuntimeError as e:
            if unparsable_output:
                print(color('37', ' ' * 10 + ' |  ' + line))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
        'Debug Wayland protocol messages. ' +
        'To use, pipe in the stderr of a Wayland server or client run with WAYLAND_DEBUG=1. ' +
        'full usage looks like: ' +
        ' $ ' + color('1;37', example_usage))
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-f', '--file', type=str, help='Read Wayland events from the specified file instead of stdin')
    parser.add_argument('-a', '--show-all', action='store_true', help='show output as-is if it can not be parsed, default is to filter it')
    args = parser.parse_args()

    if args.verbose:
        verbose = True
        log('Verbose output enabled')

    if args.show_all:
        unparsable_output = True
        log('Showing unparsable output')

    input_file = sys.stdin
    if args.file:
        input_file = open(args.file)

    main(input_file)

