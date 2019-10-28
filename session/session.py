import re
from util import *
import wl
import matcher

help_command_color = '1;37'

def command_format(cmd):
    if check_gdb():
        return '(gdb) ' + color(help_command_color, 'wl' + cmd)
    else:
        return '$ ' + color(help_command_color, cmd)

class Command:
    def __init__(self, name, arg, func, help_text):
        self.name = name
        self.arg = arg
        self.func = func
        self.help = help_text
    def matches(self, command):
        return self.name.startswith(command.lower())

class Session:
    def __init__(self, display_matcher, stop_matcher, output):
        assert display_matcher
        assert stop_matcher
        self.current_connection = None # The connection that is currently being shown
        self.connection_explicitly_selected = False # If the current connection was selected by the user
        # A list of connections in the order they were created
        # Each connection has a name (single letter) and id (string containing pointer address, if coming from libwayland)
        self.connection_list = []
        # Mapping of open connection ids to connection objects
        self.connections = {}
        self.connection_name_generator = wl.Connection.NameGenerator()
        self.commands = [
            Command('help', '[COMMAND]', self.help_command,
                'Show this help message, or get help for a specific command'),
            Command('list', '[CONN:] [MATCHER] [~ COUNT]', self.list_command,
                'List messages matching given matcher (or list all messages, if no matcher provided)\n' +
                'Prepend "CONN:" to show messages from a different connection than the one currently active\n' +
                'Append "~ COUNT" to show at most the last COUNT messages that match\n' +
                'See ' + command_format('help matcher') + ' for matcher syntax'),
            Command('filter', '[MATCHER]', self.filter_command,
                'Show the current output filter matcher, or add a new one\n' +
                'See ' + command_format('help matcher') + ' for matcher syntax'),
            Command('breakpoint', '[MATCHER]', self.break_point_command,
                'Show the current breakpoint matcher, or add a new one\n' +
                'Use an inverse matcher (^) to disable existing breakpoints\n' +
                'See ' + command_format('help matcher') + ' for matcher syntax'),
            Command('matcher', '[MATCHER]', self.matcher_command,
                'Parse a matcher, and show it unsimplified'),
            Command('connection', '[CONNECTION]', self.connection_command,
                'Show Wayland connections, or switch to another connection'),
            Command('resume', None, self.resume_command,
                'Resume processing events\n' +
                'In GDB you can also use the continue gdb command'),
            Command('quit', None, self.quit_command,
                'Quit the program'),
        ]
        self.is_stopped = False
        self.should_quit = False
        self.display_matcher = display_matcher
        self.stop_matcher = stop_matcher
        self.out = output
        self.last_shown_timestamp = None

    def set_stopped(self, val):
        self.is_stopped = val

    def stopped(self):
        return self.is_stopped

    def quit(self):
        return self.should_quit

    def message(self, connection_id, message):
        try:
            if message == None:
                return
            self.is_stopped = False
            if not connection_id in self.connections:
                self.out.warn('connection_id ' + repr(connection_id) + ' never explicitly created')
                self.open_connection(connection_id, None, message.timestamp)
            connection = self.connections.get(connection_id, None)
            if connection == None:
                self.out.warn('connection_id ' + repr(connection_id) + ' never explicitly created')
                connection = self.open_connection(connection_id, None, message.timestamp)
            connection.message(message)
            if connection == self.current_connection:
                if self.display_matcher.matches(message):
                    self._show_message(message)
                if self.stop_matcher.matches(message):
                    self.out.show(color('1;37', '    Stopped at ') + str(message).strip())
                    self.is_stopped = True
        except Exception as e:
            self.out.warn(e)

    def open_connection(self, connection_id, is_server, time):
        # is_server can be none if the value is unknown
        self.close_connection(connection_id, time)
        name = self.connection_name_generator.next()
        connection = wl.Connection(name, is_server, None, time, self.out)
        connection.id = connection_id
        # Compositors running nested will open up a client connection first,
        # We should switch to the server as that's the one we're likely interested in
        if (
            not self.current_connection or
            (not self.current_connection.is_server and is_server) or
            not self.connection_explicitly_selected and (is_server or not self.current_connection.is_server)):
            self.current_connection = connection
            self.out.show(color('1;32', 'Switching to new ' + connection.description() + ' connection ' + name))
        else:
            self.out.show(color('1;32', 'New ' + connection.description() + ' connection ' + name))
        self.connections[connection_id] = connection
        self.connection_list.append(connection)
        return connection

    def close_connection(self, connection_id, time):
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            del self.connections[connection_id]
            # Connection will still be in connection list
            connection.close(time)
            self.out.show(color('1;31', 'Closed ' + connection.description() + ' connection ' + connection.name))

    def show_messages(self, connection, matcher, cap=None):
        msg = 'Messages that match ' + str(matcher)
        if connection != self.current_connection:
            msg += ' on connection ' + connection.name
        msg += ':'
        self.out.show(msg)
        if connection == None:
            self.out.show(' ╰╴ No connection')
            return
        matching, matched, didnt_match, not_searched = self._get_matching(connection, matcher, cap)
        if not matching:
            if not self.connections:
                self.out.show(' ╰╴ No messages yet')
            else:
                assert didnt_match == len(self.messages)
                self.out.show(' ╰╴ None of the ' + color('1;31', str(didnt_match)) + ' messages so far')
        else:
            self.last_shown_timestamp = None
            for message in matching:
                self._show_message(message)
            self.out.show(
                '(' +
                color(('1;32' if matched > 0 else '37'), str(matched)) + ' matched, ' +
                color(('1;31' if didnt_match > 0 else '37'), str(didnt_match)) + ' didn\'t' +
                (', ' + color(('37'), str(not_searched)) + ' not checked' if not_searched != 0 else '') +
                ')')
            self.last_shown_timestamp = None

    def _show_message(self, message):
        delta = message.timestamp - self.last_shown_timestamp if self.last_shown_timestamp != None else 0
        if delta > 1.0:
            self.out.show(color('37', '    ───┤ {:0.4f}s ├───'.format(delta)))
        self.last_shown_timestamp = message.timestamp
        message.show(self.out)

    def _get_matching(self, connection, matcher, cap=None):
        if cap == 0:
            cap = None
        didnt_match = 0
        acc = []
        if connection:
            messages = connection.messages
        else:
            messages = []
        for message in reversed(messages):
            if matcher.matches(message):
                acc.append(message)
                if cap and len(acc) >= cap:
                    break
            else:
                didnt_match += 1
        return (reversed(acc), len(acc), didnt_match, len(messages) - len(acc) - didnt_match)

    def command(self, command):
        assert isinstance(command, str)
        command = command.strip()
        args = re.split('\s', command, 1)
        if len(args) == 0:
            return False
        cmd = no_color(args[0]).strip()
        arg = None if len(args) < 2 else no_color(args[1]).strip()
        if cmd == '':
            assert not arg
            self.out.error('No command specified')
            cmd = 'help'
        if cmd == 'w' or cmd == 'wl': # in case they use GDB style commands when not in GDB
            return self.command(arg)
        if cmd.startswith('wl'): # in case they use GDB style commands when not in GDB
            cmd = cmd[2:]
        cmd = self._get_command(cmd)
        if cmd:
            self.out.log('Got ' + cmd.name + ' command' + (' with \'' + arg + '\'' if arg else ''))
            cmd.func(arg)

    def _get_command(self, command):
        found = []
        for c in self.commands:
            if c.name.startswith(command):
                found.append(c)
        if len(found) == 1:
            return found[0]
        else:
            if len(found) > 1:
                self.out.error('\'' + command + '\' could refer to multiple commands: ' + ', '.join(c.name for c in found))
            else:
                self.out.error('Unknown command \'' + command + '\'')
            return None

    def help_command(self, arg):
        if arg:
            if arg.startswith('wl'):
                arg = arg[2:].strip()
            if arg == 'matcher':
                import matcher
                matcher.print_help()
                return
            else:
                cmd = self._get_command(arg)
                if cmd:
                    start = command_format(cmd.name) + ': '
                    body = cmd.help.replace('\n', '\n' + ' ' * len(no_color(start)))
                    self.out.show(start + body)
                    return
        self.out.show('Usage: ' + command_format('<COMMAND> [ARGUMENT]'))
        self.out.show('Commands can be abbreviated (down to just the first unique letter)')
        self.out.show('Help with matcher syntax: ' + command_format('help matcher'))
        self.out.show('Commands:')
        for c in self.commands:
            s = c.name
            if c.arg:
                s += ' ' + c.arg
            self.out.show('  ' + command_format(s))

    # Old can be None
    def parse_and_join(self, new_unparsed, old):
        try:
            parsed = matcher.parse(new_unparsed)
            if old:
                return matcher.join(parsed, old).simplify()
            else:
                return parsed.simplify()
        except RuntimeError as e:
            self.out.error('Failed to parse "' + new_unparsed + '":\n    ' + str(e))
            return old

    def filter_command(self, arg):
        if arg:
            self.display_matcher = self.parse_and_join(arg, self.display_matcher)
            self.out.show('Only showing messages that match ' + str(self.display_matcher))
        else:
            self.out.show('Output filter: ' + str(self.display_matcher))

    def break_point_command(self, arg):
        if arg:
            self.stop_matcher = self.parse_and_join(arg, self.stop_matcher)
            self.out.show('Breaking on messages that match: ' + str(self.stop_matcher))
        else:
            self.out.show('Breakpoint matcher: ' + str(self.stop_matcher))

    def matcher_command(self, arg):
        if arg:
            try:
                parsed = matcher.parse(arg)
                unsimplified_str = str(parsed)
                self.out.show('Unsimplified: ' + unsimplified_str)
                self.out.show('  Simplified: ' + str(parsed.simplify()))
                self.out.show('    Reparsed: ' + str(matcher.parse(unsimplified_str).simplify()))
            except RuntimeError as e:
                self.out.error('Failed to parse "' + arg + '":\n    ' + str(e))
        else:
            self.out.show('No matcher to parse')

    def list_command(self, arg):
        cap = None
        connection = self.current_connection
        if arg:
            args = arg.split('~')
            if len(args) == 2:
                try:
                    cap = int(args[1])
                except ValueError:
                    self.out.error('Expected number after \'~\', got \'' + args[1] + '\'')
                    return
            arg = args[0]
            args = arg.split(':')
            if len(args) == 2:
                c = self._get_connection(args[0])
                if c == None:
                    self.out.error('"' + args[0] + '" does not name a connection')
                    return
                connection = c
                arg = args[1]
            else:
                arg = args[0]
            m = self.parse_and_join(arg, None)
            if not m:
                return
        else:
            m = matcher.always
        self.show_messages(connection, m, cap)

    def _get_connection(self, name):
        name = name.lower()
        found = None
        for c in self.connection_list:
            l = [c.name, c.id, c.title]
            for i in l:
                if i and name == i.lower():
                    return c
        return None

    def connection_command(self, arg):
        if arg:
            c = self._get_connection(arg)
            if c:
                self.current_connection = c
                self.out.show('Switched to connection ' + color('1;37', self.current_connection.name))
                self.connection_explicitly_selected = True
                return
            else:
                self.out.error('"' + arg + '" does not name a connection')
        for c in self.connection_list:
            delim = ', '
            if c == self.current_connection:
                clr = '1;37'
                line = ' => '
            else:
                clr = '37'
                line = '    '
            line += c.name + ' (' + c.description() + '): '
            line = color(clr, line)
            if c.id:
                line += color('35', '"' + (c.id) + '"') + delim
            if c.open:
                line += color('1;32', 'open')
            else:
                line += color('1;31', 'closed')
            line += delim
            line += color('1;34', str(len(c.messages))) + ' messages'
            self.out.show(line)

    def resume_command(self, arg):
        self.is_stopped = False
        self.out.log('Resuming...')

    def quit_command(self, arg):
        self.should_quit = True

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
