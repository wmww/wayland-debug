import re

import interfaces
from core import wl
from core.util import *

class WlPatterns:
    instance = None

    def __init__(self):
        int_re = r'(?P<int>-?\d+)'
        float_re = r'(?P<float>-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)'
        fd_re = r'(?:fd (?P<fd>\d+))'
        str_re = r'(?:"(?P<str>.*)")'
        new_id_re = r'(?:new id (?:(?P<new_type>\w+)|(?:\[unknown\]))@(?P<new_id>\d+))'
        obj_re = r'(?P<obj_type>\w+)@(?P<obj_id>\d+)'
        array_re = r'(?P<array>array)'
        nil_re = r'(?P<nil>nil)'
        all_args_re = (
            r'^(?:' +
            int_re + '|' +
            obj_re + '|' +
            new_id_re + '|' +
            nil_re + '|' +
            str_re + '|' +
            float_re + '|' +
            array_re + '|' +
            fd_re + r')$')
        self.arg_re = re.compile(all_args_re)
        self.any_arg_re = re.compile(r'((?<=,)|^)\s*("[^"]*"|[^,]+)($|(?=,))')
        timestamp_regex = r'\[(\d+\.\d+)\]'
        message_regex = r'(\w+)@(\d+)\.(\w+)\((.*)\)$'
        self.out_msg_re = re.compile(timestamp_regex + '  -> ' + message_regex)
        self.in_msg_re = re.compile(timestamp_regex + ' ' + message_regex)

    @staticmethod
    def lazy_get_instance():
        if not WlPatterns.instance:
            WlPatterns.instance = WlPatterns()
        return WlPatterns.instance

def argument(p, value_str):
    match = p.arg_re.match(value_str)
    if match:
        if match.group('int'):
            return wl.Arg.Int(int(value_str))
        elif match.group('obj_id'):
            return wl.Arg.Object(wl.Object.Unresolved(int(match.group('obj_id')), match.group('obj_type')), False)
        elif match.group('new_id'):
            type_name = match.group('new_type')
            if not type_name:
                type_name = None
            return wl.Arg.Object(wl.Object.Unresolved(int(match.group('new_id')), type_name), True)
        elif match.group('nil'):
            return wl.Arg.Null()
        elif match.group('str'):
            return wl.Arg.String(match.group('str'))
        elif match.group('float'):
            return wl.Arg.Float(float(value_str))
        elif match.group('fd'):
            return wl.Arg.Fd(int(match.group('fd')))
        elif match.group('array'):
            return wl.Arg.Array()
    return wl.Arg.Unknown(value_str)

def argument_list(p, args_str):
    return [argument(p, match[1]) for match in p.any_arg_re.findall(args_str)]

def message(raw):
    p = WlPatterns.lazy_get_instance()
    sent = True
    conn_id = 'PARSED'
    matches = p.out_msg_re.findall(raw)
    if not matches:
        sent = False
        matches = p.in_msg_re.findall(raw)
    if len(matches) != 1:
        raise RuntimeError(raw)
    match = matches[0]
    assert isinstance(match, tuple), repr(match)
    abs_timestamp = float(match[0]) / 1000.0
    type_name = match[1]
    obj_id = int(match[2])
    message_name = match[3]
    message_args_str = match[4]
    message_args = argument_list(p, message_args_str)
    return conn_id, wl.Message(abs_timestamp, wl.Object.Unresolved(obj_id, type_name), sent, message_name, message_args)

def file(input_file, out):
    parse = True
    while True:
        try:
            line = input_file.readline()
        except KeyboardInterrupt:
            break
        if line == '':
            break
        line = line.strip() # be sure to strip after the empty check
        try:
            conn_id, msg = message(line)
            if parse:
                yield conn_id, msg
        except RuntimeError as e:
            out.unprocessed(str(e))
        except:
            import traceback
            out.show(traceback.format_exc())
            parse = False

def into_sink(input_file, out, sink):
    assert isinstance(sink, interfaces.ConnectionIDSink)
    known_connections = {}
    last_time = 0
    for conn_id, msg in file(input_file, out):
        last_time = msg.timestamp
        if not conn_id in known_connections:
            known_connections[conn_id] = True
            is_server = None
            if msg.name ==  'get_registry':
                is_server = not msg.sent
            sink.open_connection(last_time, conn_id, is_server)
        sink.message(conn_id, msg)
    for conn_id in known_connections.keys():
        sink.close_connection(last_time, conn_id)

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
