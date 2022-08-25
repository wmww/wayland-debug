import re
from typing import IO, Iterator, Optional, List, Tuple, Set

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
        timestamp_regex = r'\[\s*(?P<timestamp>\d+[\.,]\d+)\s*\]'
        message_regex = r'(?P<type>\w+)@(?P<id>\d+)\.(?P<message>\w+)\((?P<args>.*)\)$'
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

def argument_list_strs(args_str: str) -> List[str]:
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

def argument_list(p: WlPatterns, args_str: str) -> Tuple[wl.Arg.Base, ...]:
    str_list = argument_list_strs(args_str)
    return tuple(argument(p, s) for s in str_list)

def message(raw: str) -> Tuple[str, wl.Message]:
    p = WlPatterns.lazy_get_instance()
    sent = True
    conn_id = 'PARSED'
    match = p.out_msg_re.search(raw)
    if not match:
        sent = False
        match = p.in_msg_re.search(raw)
    if not match:
        raise RuntimeError(raw)
    abs_timestamp = float(match.group('timestamp').replace(',', '.')) / 1000.0
    type_name = match.group('type')
    obj_id = int(match.group('id'))
    message_name = match.group('message')
    message_args_str = match.group('args')
    message_args = argument_list(p, message_args_str)
    return conn_id, wl.Message(abs_timestamp, wl.UnresolvedObject(obj_id, type_name), sent, message_name, message_args)

class Parser:
    def __init__(self, out: Output, sink: ConnectionIDSink):
        self.out = out
        self.sink = sink
        self.known_connections: Set[str] = set()
        self.last_time = 0.0

    def handle_message(self, conn_id: str, msg: wl.Message):
        self.last_time = msg.timestamp
        if not conn_id in self.known_connections:
            self.known_connections.add(conn_id)
            is_server = None
            if msg.name ==  'get_registry':
                is_server = not msg.sent
            self.sink.open_connection(self.last_time, conn_id, is_server)
        self.sink.message(conn_id, msg)

    def parse_all(self, input_file: IO):
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
                    self.handle_message(conn_id, msg)
            except RuntimeError as e:
                self.out.unprocessed(str(e))
            except Exception as e:
                import traceback
                self.out.show(traceback.format_exc())
                self.out.error(e)
                parse = False

    def cleanup(self):
        for conn_id in self.known_connections:
            self.sink.close_connection(self.last_time, conn_id)

def into_sink(input_file: IO, out: Output, sink: ConnectionIDSink) -> None:
    parser = Parser(out, sink)
    parser.parse_all(input_file)
    parser.cleanup()

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
