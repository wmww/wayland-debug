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
        return color('1;34', '(' + str(self.id) + ': ' + self.type + ')')

class WaylandArgument:
    def __init__(self, value_str):
        self.value = value_str

    def __str__(self):
        if isinstance(self.value, int):
            return color('1;35', str(self.value))
        elif isinstance(self.value, str):
            return color('1;33', repr(self.value))
        else:
            return color('1;31', type(self.value).__name__ + ': ' + repr(self.value))

def parse_message_args(args_str):
    args = [WaylandArgument(i.strip()) for i in args_str.split(',') if i]
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
        self.timestamp = abs_timestamp - base_time
        self.obj = WaylandObject(type_name, obj_id)
        self.name = message_name
        self.args = message_args

    def __str__(self):
        return (
            color('1;37', '{:10.4f}'.format(self.timestamp)) + ' ' +
            str(self.obj) + ' ' +
            color('1;36', self.name + ' [') +
            color('1;36', ', ').join([str(i) for i in self.args]) + color('1;36', ']'))

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

