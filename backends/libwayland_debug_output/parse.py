import re
from typing import IO, Iterator, Optional

from interfaces import ConnectionIDSink
from core import wl
from core.output import Output
from core.util import *

class WlPatterns:
    instance = None

    def __init__(self) -> None:
        int_re = r'(?P<int>-?\d+)'
        float_re = r'(?P<float>-?\d+(?:[\.,]\d+)?(?:[eE][+-]?\d+)?)'
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
        timestamp_regex = r'\[(\d+[\.,]\d+)\]'
        message_regex = r'(\w+)@(\d+)\.(\w+)\((.*)\)$'
        self.out_msg_re = re.compile(timestamp_regex + '  -> ' + message_regex)
        self.in_msg_re = re.compile(timestamp_regex + ' ' + message_regex)

    @staticmethod
    def lazy_get_instance() -> 'WlPatterns':
        if not WlPatterns.instance:
            WlPatterns.instance = WlPatterns()
        return WlPatterns.instance

def argument(p: WlPatterns, value_str: str) -> wl.Arg.Base:
    match = p.arg_re.match(value_str)
    if match:
        if match.group('int'):
            return wl.Arg.Int(int(value_str))
        elif match.group('obj_id'):
            return wl.Arg.Object(wl.UnresolvedObject(int(match.group('obj_id')), match.group('obj_type')), False)
        elif match.group('new_id'):
            type_name: Optional[str] = match.group('new_type')
            if not type_name:
                type_name = None
            return wl.Arg.Object(wl.UnresolvedObject(int(match.group('new_id')), type_name), True)
        elif match.group('nil'):
            return wl.Arg.Null()
        elif match.group('str'):
            return wl.Arg.String(match.group('str'))
        elif match.group('float'):
            return wl.Arg.Float(float(value_str.replace(',', '.')))
        elif match.group('fd'):
            return wl.Arg.Fd(int(match.group('fd')))
        elif match.group('array'):
            return wl.Arg.Array()
    return wl.Arg.Unknown(value_str)

def end_of_str(args_str: str, i: int) -> int:
    i += 1
    while i < len(args_str) and args_str[i] != '"':
        if args_str[i] == '\\':
            i += 1
        i += 1
    return i

def argument_list_strs(args_str: str) -> list[str]:
    result = []
    i = 0
    start = 0
    while i < len(args_str):
        if args_str[i:].startswith(', '):
            result.append(args_str[start:i])
            start = i + 2
        if args_str[i] == '"':
            i = end_of_str(args_str, i)
        i += 1
    if i != start:
        result.append(args_str[start:i])
    return result

def argument_list(p: WlPatterns, args_str: str) -> list[wl.Arg.Base]:
    str_list = argument_list_strs(args_str)
    return [argument(p, s) for s in str_list]

def message(raw: str) -> tuple[str, wl.Message]:
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
    abs_timestamp = float(match[0].replace(',', '.')) / 1000.0
    type_name = match[1]
    obj_id = int(match[2])
    message_name = match[3]
    message_args_str = match[4]
    message_args = argument_list(p, message_args_str)
    return conn_id, wl.Message(abs_timestamp, wl.UnresolvedObject(obj_id, type_name), sent, message_name, message_args)

def file(input_file: IO, out: Output) -> Iterator[tuple[str, wl.Message]]:
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

def into_sink(input_file: IO, out: Output, sink: ConnectionIDSink):
    known_connections = {}
    last_time = 0.0
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
