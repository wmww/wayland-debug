import re

import wl_data as wl
import session
from util import *

def argument(value_str):
    int_matches = re.findall('^-?\d+$', value_str)
    if int_matches:
        return wl.Arg.Primitive(int(value_str))
    float_matches = re.findall('^-?\d+(\.\d+)?([eE][+-]?\d+)?$', value_str)
    if float_matches:
        return wl.Arg.Primitive(float(value_str))
    nil_matches = re.findall('^nil$', value_str)
    if nil_matches:
        return wl.Arg.Primitive(None)
    fd_matches = re.findall('^fd (\d+)$', value_str)
    if fd_matches:
        return wl.Arg.Fd(int(fd_matches[0]))
    str_matches = re.findall('^"(.*)"$', value_str)
    if str_matches:
        return wl.Arg.Primitive(str_matches[0])
    new_id_unknown_matches = re.findall('^new id \[unknown\]@(\d+)$', value_str)
    if new_id_unknown_matches:
        return wl.Arg.Object(wl.Object.Unresolved(int(new_id_unknown_matches[0]), None), True)
    new_id_matches = re.findall('^new id (\w+)@(\d+)$', value_str)
    if new_id_matches:
        return wl.Arg.Object(wl.Object.Unresolved(int(new_id_matches[0][1]), new_id_matches[0][0]), True)
    obj_matches = re.findall('^(\w+)@(\d+)$', value_str)
    if obj_matches:
        return wl.Arg.Object(wl.Object.Unresolved(int(obj_matches[0][1]), obj_matches[0][0]), False)
    else:
        return wl.Arg.Unknown(value_str)

def argument_list(args_str):
    args = []
    start = 0
    i = 0
    while i <= len(args_str):
        if i == len(args_str) or args_str[i] == ',':
            arg = args_str[start:i].strip()
            if (arg):
                args.append(argument(arg))
            start = i + 1
        elif args_str[i] == '"':
            i += 1
            while args_str[i] != '"':
                if args_str[i] == '\\':
                    i += 1
                i += 1
        i += 1
    return args

def message(raw):
    timestamp_regex = '\[(\d+\.\d+)\]'
    message_regex = '(\w+)@(\d+)\.(\w+)\((.*)\)$'
    sent = True
    conn_id = 'PARSED'
    matches = re.findall(timestamp_regex + '  -> ' + message_regex, raw)
    if not matches:
        sent = False
        matches = re.findall(timestamp_regex + ' ' + message_regex, raw)
    if len(matches) != 1:
        raise RuntimeError(raw)
    match = matches[0]
    assert isinstance(match, tuple), repr(match)
    abs_timestamp = float(match[0]) / 1000.0
    type_name = match[1]
    obj_id = int(match[2])
    message_name = match[3]
    message_args_str = match[4]
    message_args = argument_list(message_args_str)
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
