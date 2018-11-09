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

def str_matches(pattern, txt):
    pattern = re.escape(pattern)
    pattern = pattern.replace('\*', '.*')
    pattern = '^' + pattern + '$'
    return len(re.findall(pattern, txt)) == 1

class WlObject:

    # keys are ids, values are arrays of objects in the order they are created
    db = {}
    display = None
    registry = None

    def look_up_specific(obj_id, obj_generation, type_name = None):
        assert obj_id in WlObject.db, 'Id ' + str(obj_id) + ' of type ' + str(type_name) + ' not in object database'
        assert obj_generation >= 0 and len(WlObject.db[obj_id]) > obj_generation, (
            'Invalid generation ' + str(obj_generation) + ' for id ' + str(obj_id))
        obj = WlObject.db[obj_id][obj_generation]
        if type_name:
            if obj.type:
                assert str_matches(type_name, obj.type), str(obj) + ' expected to be of type ' + type_name
        return obj

    def look_up_most_recent(obj_id, type_name = None):
        obj_generation = 0
        if obj_id in WlObject.db:
            obj_generation = len(WlObject.db[obj_id]) - 1
        obj = WlObject.look_up_specific(obj_id, obj_generation, type_name)
        # This *would* be a useful warning, except somehow callback.done, delete(callback) (though sent in the right
        # order), arrive to the client in the wrong order. I don't know a better workaround then just turning off the check
        # if not obj.alive:
        #    warning(str(obj) + ' used after destroyed')
        return obj

    def __init__(self, obj_id, type_name, parent_obj, create_time):
        assert(isinstance(obj_id, int))
        if obj_id in self.db:
            last_obj = self.db[obj_id][-1]
            assert not last_obj.alive, 'Tried to create object of type ' + type_name + ' with the same id as ' + str(last_obj)
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

class WlMessage:
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
        self.destroyed_obj = None

    def resolve_objects(self, session):
        if self.obj.type == 'wl_registry' and self.name == 'bind':
            self.args[3].type = self.args[1].value
        if self.obj == WlObject.display and self.name == 'delete_id':
            self.destroyed_obj = WlObject.look_up_most_recent(self.args[0].value, None)
            self.destroyed_obj.destroy(self.timestamp)
        for i in self.args:
            if isinstance(i, WlArgs.Object):
                i.resolve(self.obj, self.timestamp)

    def used_objects(self):
        result = []
        for i in self.args:
            if isinstance(i, WlArgs.Object):
                if i.resolved:
                    result.append(i.obj)
                else:
                    warning('used_objects() called on message with unresolved object')
        if self.destroyed_obj:
            result.append(self.destroyed_obj)
        return result

    def __str__(self):
        destroyed = ''
        if self.destroyed_obj:
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

class Session():
    def __init__(self, input_file, matcher):
        self.messages = []
        while True:
            line = input_file.readline()
            if line == '':
                break
            line = line.strip() # be sure to strip after the empty check
            try:
                message = WlMessage(line)
                self.messages.append(message)
                message.resolve_objects(self)
                if matcher.matches(message):
                    print(message)
            except RuntimeError as e:
                if unparsable_output:
                    print(color('37', ' ' * 10 + ' |  ' + line))

def interactive(session, matcher):
    for i in session.messages:
        if matcher.matches(i):
            print(i)

class Matcher:

    def __init__(self, matcher, match_when_used):
        split_matches = re.findall('^([^\[]+)(\[\s*(.*)\])?$', matcher) # split the object matcher and the list of method matchers
        if len(split_matches) != 1:
            raise RuntimeError(
                'Failed to parse structure of matcher, ' +
                'should be in the form \'object_matcher\' or \'object_matcher[list_of_message_matchers]\'')
        obj_matcher = split_matches[0][0] # the object portion
        self._parse_obj_matcher(obj_matcher)
        message_matchers = split_matches[0][1] # the list of message matchers, can be an empty string
        self.messages = None
        if message_matchers:
            self.messages = re.findall('[\w\*]+', message_matchers)
        self.match_when_used = match_when_used

    def _parse_obj_matcher(self, matcher):
        id_matches = re.findall('(^|[^\w\.-])(\d+)(\.(\d+))?', matcher)
        obj_id = None
        obj_generation = None
        if id_matches:
            if len(id_matches) > 1:
                raise RuntimeError(
                    'Found multiple object IDs (' +
                    ', '.join(i[1] + ('.' + i[3] if i[3] else '') for i in id_matches) +
                    ')')
            obj_id = int(id_matches[0][1])
            if id_matches[0][3]:
                obj_generation = id_matches[0][3]
        obj_name_matches = re.findall('([a-zA-Z\*][\w\*-]*)', matcher)
        self.type = None
        if obj_name_matches:
            if len(obj_name_matches) > 1:
                raise RuntimeError(
                    'Found multiple object type names (' +
                    ', '.join(i for i in obj_name_matches) +
                    ')')
            self.type = obj_name_matches[0]
        self.obj = None
        self.obj_id = None # Only set if self.obj is None
        self.obj_generation = None # Only set if self.obj is None
        if obj_id:
            try:
                if obj_generation:
                    self.obj = WlObject.look_up_specific(obj_id, obj_generation, self.type)
                else:
                    self.obj = WlObject.look_up_most_recent(obj_id, self.type)
            except AssertionError as e:
                self.obj_id = obj_id
                self.obj_generation = obj_generation

    def _matches_obj(self, obj):
        if self.obj:
            return obj == self.obj
        else:
            if self.obj_id and self.obj_id != obj.id:
                return False
            elif self.obj_generation and self.obj_generation != obj.generation:
                return False
            elif self.type and not str_matches(self.type, obj.type):
                return False
            else:
                return True

    def _matches_message(self, message):
        if not self._matches_obj(message.obj):
            if not self.match_when_used:
                return False
            found_match = False
            for i in message.used_objects():
                if self._matches_obj(i):
                    found_match = True
                    break
            if not found_match:
                return False
        if self.messages == None:
            return True
        for i in self.messages:
            if str_matches(i, message.name):
                return True
        return False

    def matches(self, item):
        if isinstance(item, WlObject):
            return _matches_obj(item)
        elif isinstance(item, WlMessage):
            return self._matches_message(item)
        else:
            raise TypeError()

class MatcherCollection:
    def __init__(self, matchers, is_whitelist):
        self.matchers = []
        self.is_whitelist = is_whitelist
        for i in re.findall('([^\s;:,\[\]]+(\s*\[([^\]]*)\])?)', matchers):
            try:
                self.matchers.append(Matcher(i[0], is_whitelist))
            except RuntimeError as e:
                warning('Failed to parse \'' + i[0] + '\': ' + str(e))

    def matches(self, item):
        found = False
        for i in self.matchers:
            if i.matches(item):
                found = True
        return found == self.is_whitelist

    def match_none_matcher():
        return MatcherCollection('', True)

def main(file_path, matcher):
    if file_path:
        file = open(file_path)
        session = Session(file, MatcherCollection.match_none_matcher())
        # session = Session(file, matcher)
        file.close()
        interactive(session, matcher)
    else:
        Session(sys.stdin, matcher)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=
        'Debug Wayland protocol messages. ' +
        'To use, pipe in the stderr of a Wayland server or client run with WAYLAND_DEBUG=1. ' +
        'full usage looks like: ' +
        ' $ ' + color('1;37', example_usage))
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output, mostly used for debugging this program')
    parser.add_argument('-f', '--file', type=str, help='Read Wayland events from the specified file instead of stdin')
    parser.add_argument('-t', '--show-trash', action='store_true', help='show output as-is if it can not be parsed, default is to filter it')
    parser.add_argument('-b', '--blacklist', type=str, help=
        'colon seporated list (no spaces) of wayland types to hide.' +
        'you can also put a comma seporated list of messages to hide in brackets after the type. ' +
        'example: type_a:type_b[message_a,message_b]')
    parser.add_argument('-w', '--whitelist', type=str, help=
        'only show these objects (all objects are shown if not specified). ' +
        'messages that reference these objects will also be shown, and the optional message list is used to filter those as well.' +
        'same syntax as blacklist')

    args = parser.parse_args()

    if args.verbose:
        verbose = True
        log('Verbose output enabled')

    if args.show_trash:
        unparsable_output = True
        log('Showing unparsable output')

    use_whitelist = False
    matcher_list = ''
    if args.blacklist:
        matcher_list = args.blacklist
    if args.whitelist:
        if matcher_list:
            warning('blacklist is ignored when a whitelist is provided')
        matcher_list = args.whitelist
        use_whitelist = True

    matcher = MatcherCollection(matcher_list, use_whitelist)
    main(args.file, matcher)

