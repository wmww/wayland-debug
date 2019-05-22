import re

import wl
import session
from util import *

class WlPatterns:
    instance = None

    def __init__(self):
        self.int_re = re.compile('^-?\d+$')
        self.float_re = re.compile('^-?\d+(\.\d+)?([eE][+-]?\d+)?$')
        self.fd_re = re.compile('^fd (\d+)$')
        self.str_re = re.compile('^"(.*)"$')
        self.new_id_unknown_re = re.compile('^new id \[unknown\]@(\d+)$')
        self.new_id_re = re.compile('^new id (\w+)@(\d+)$')
        self.obj_re = re.compile('^(\w+)@(\d+)$')
        self.any_arg_re = re.compile('((?<=,)|^)\s*(([^,"]*("[^"]*")?)+)($|(?=,))')
        timestamp_regex = '\[(\d+\.\d+)\]'
        message_regex = '(\w+)@(\d+)\.(\w+)\((.*)\)$'
        self.out_msg_re = re.compile(timestamp_regex + '  -> ' + message_regex)
        self.in_msg_re = re.compile(timestamp_regex + ' ' + message_regex)

    def lazy_get_instance():
        if not WlPatterns.instance:
            WlPatterns.instance = WlPatterns()
        return WlPatterns.instance

def argument(p, value_str):
    int_matches = p.int_re.findall(value_str)
    if int_matches:
        return wl.Arg.Int(int(value_str))
    float_matches = p.float_re.findall(value_str)
    if float_matches:
        return wl.Arg.Float(float(value_str))
    if value_str == 'nil':
        return wl.Arg.Null()
    fd_matches = p.fd_re.findall(value_str)
    if fd_matches:
        return wl.Arg.Fd(int(fd_matches[0]))
    str_matches = p.str_re.findall(value_str)
    if str_matches:
        return wl.Arg.String(str_matches[0])
    if value_str == 'array':
        return wl.Arg.Array()
    new_id_unknown_matches = p.new_id_unknown_re.findall(value_str)
    if new_id_unknown_matches:
        return wl.Arg.Object(wl.Object.Unresolved(int(new_id_unknown_matches[0]), None), True)
    new_id_matches = p.new_id_re.findall(value_str)
    if new_id_matches:
        return wl.Arg.Object(wl.Object.Unresolved(int(new_id_matches[0][1]), new_id_matches[0][0]), True)
    obj_matches = p.obj_re.findall(value_str)
    if obj_matches:
        return wl.Arg.Object(wl.Object.Unresolved(int(obj_matches[0][1]), obj_matches[0][0]), False)
    return wl.Arg.Unknown(value_str)

def argument_list(p, args_str):
    if args_str:
        return [argument(p, match[1]) for match in p.any_arg_re.findall(args_str)]
    else:
        return []

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

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
