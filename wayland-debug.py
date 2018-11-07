#!/usr/bin/python3

import sys
import re

verbose = False

base_time = None

# all currently live objects by id
live_objects = {}

# if we print with colors and such
color_output = hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()

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

class WaylandObject:
    def __init__(self, type_name, obj_id):
        self.type = type_name
        self.id = obj_id

    def __str__(self):
        return color('1;37', '(' + str(self.id) + ': ' + self.type + ')')

class WaylandFd:
    def __init__(self, val):
        self.value = val

    def __str__(self):
        return color('36', 'fd ' + str(self.value))

class WaylandArgument:
    def __init__(self, value_str):
        int_matches = re.findall('^-?\d+$', value_str)
        if int_matches:
            self.value = int(value_str)
            return
        float_matches = re.findall('^-?\d+(\.\d+)?([eE][+-]?\d+)?$', value_str)
        if float_matches:
            self.value = float(value_str)
            return
        nil_matches = re.findall('^nil$', value_str)
        if nil_matches:
            self.value = None
            return
        fd_matches = re.findall('^fd (\d+)$', value_str)
        if fd_matches:
            self.value = WaylandFd(int(fd_matches[0]))
            return
        str_matches = re.findall('^"(.*)"$', value_str)
        if str_matches:
            self.value = str_matches[0]
            return
        new_id_matches = re.findall('^new id (\w+)@(\d+)$', value_str)
        if new_id_matches:
            self.value = WaylandObject(new_id_matches[0][0], int(new_id_matches[0][1]))
            self.is_new = True
            return
        obj_matches = re.findall('^(\w+)@(\d+)$', value_str)
        if obj_matches:
            self.value = WaylandObject(obj_matches[0][0], int(obj_matches[0][1]))
            self.is_new = False
            return
        else:
            class Unknown:
                def __init__(self, val):
                    self.str = val
                def __str__(self):
                    return repr(self.str)
            self.value = Unknown(value_str)

    def __str__(self):
        if isinstance(self.value, int):
            return color('1;34', str(self.value))
        elif isinstance(self.value, float):
            return color('1;35', str(self.value))
        elif isinstance(self.value, str):
            return color('1;33', repr(self.value))
        elif isinstance(self.value, WaylandFd):
            return str(self.value)
        elif isinstance(self.value, WaylandObject):
            return (color('1;32', 'new ') if self.is_new else '') + str(self.value)
        elif self.value == None:
            return color('37', 'null')
        else:
            return color('33', type(self.value).__name__ + ': ' + str(self.value))

def parse_message_args(args_str):
    args = []
    start = 0
    i = 0
    while i < len(args_str):
        if args_str[i] == ',':
            arg = args_str[start:i].strip()
            args.append(WaylandArgument(arg))
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
        abs_timestamp = float(match[0]) / 1000.0
        type_name = match[1]
        obj_id = int(match[2])
        message_name = match[3]
        message_args_str = match[4]
        message_args = parse_message_args(message_args_str)
        global base_time
        if base_time == None:
            base_time = abs_timestamp
        self.sent = sent
        self.timestamp = abs_timestamp - base_time
        self.obj = WaylandObject(type_name, obj_id)
        self.name = message_name
        self.args = message_args

    def __str__(self):
        s = None
        return (
            color('37', '{:10.4f}'.format(self.timestamp) + (' →  ' if self.sent else ' ') +
            str(self.obj) + ' ' +
            color(s, self.name + ' [') +
            color(s, ', ').join([str(i) for i in self.args]) + color(s, ']')) +
            color('37', ' ↲' if not self.sent else ''))

def main(input_file):
    while True:
        line = input_file.readline()
        if line == '':
            break
        line = line.strip() # be sure to strip after the empty check
        try:
            message = WaylandMessage(line)
            print(message)
        except RuntimeError as e:
            log('Parse error: ' + str(e))

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
        'Debug Wayland protocol messages. ' +
        'To use, pipe in the stderr of a Wayland server or client run with WAYLAND_DEBUG=1. ' +
        'full usage looks like: ' +
        ' $ ' + color('1;37', example_usage))
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')
    parser.add_argument('-f', '--file', type=str, help='Read Wayland events from the specified file instead of stdin')
    args = parser.parse_args()

    if args.verbose:
        verbose = True
        log('Verbose output enabled')

    input_file = sys.stdin
    if args.file:
        input_file = open(args.file)

    main(input_file)

