import re
from util import *
import wl_data as wl
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
        self.current_connection_id = None
        self.connection_list = []
        self.connections = {}
        self.commands = [
            Command('help', '[COMMAND]', self.help_command,
                'Show this help message, or get help for a specific command'),
            Command('show', '[MATCHER] [~ COUNT]', self.show_command,
                'Show messages matching given matcher (or show all messages, if no matcher provided)\n' +
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
            Command('resume', None, self.continue_command,
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

    def set_stopped(self, val):
        self.is_stopped = val

    def stopped(self):
        return self.is_stopped

    def quit(self):
        return self.should_quit

    def message(self, connection_id, message):
        if message == None:
            return
        self.is_stopped = False
        if not connection_id in self.connections:
            self.out.warn('connection_id ' + repr(connection_id) + ' never explicitly created')
            self.open_connection(connection_id)
        self.connections[connection_id].message(message)
        if connection_id == self.current_connection_id:
            if self.display_matcher.matches(message):
                message.show(self.out)
            if self.stop_matcher.matches(message):
                self.out.show(color('1;27', '    Stopped at ') + str(message).strip())
                self.is_stopped = True

    def open_connection(self, connection_id):
        self.close_connection(connection_id)
        if not self.connections:
            self.current_connection_id = connection_id
            self.out.show(color('1;32', 'First connection ' + repr(connection_id)))
        else:
            self.out.show(color('1;32', 'New connection ' + repr(connection_id)))
        self.connections[connection_id] = wl.Connection()
        self.connection_list.append(self.connections[connection_id])

    def close_connection(self, connection_id):
        if connection_id in self.connections:
            del self.connections[connection_id]
            self.out.show(color('1;31', 'Closed connection ' + repr(connection_id)))

    def show_messages(self, matcher, cap=None):
        self.out.show('Messages that match ' + str(matcher) + ':')
        matching, matched, didnt_match, not_searched = self._get_matching(matcher, cap)
        if not matching:
            if not self.connections:
                self.out.show(' ╰╴ No messages yet')
            else:
                assert didnt_match == len(self.messages)
                self.out.show(' ╰╴ None of the ' + color('1;31', str(didnt_match)) + ' messages so far')
        else:
            for message in matching:
                message.show(self.out)
            self.out.show(
                '(' +
                color(('1;32' if matched > 0 else '37'), str(matched)) + ' matched, ' +
                color(('1;31' if didnt_match > 0 else '37'), str(didnt_match)) + ' didn\'t' +
                (', ' + color(('37'), str(not_searched)) + ' not checked' if not_searched != 0 else '') +
                ')')

    def _get_matching(self, matcher, cap=None):
        if cap == 0:
            cap = None
        didnt_match = 0
        acc = []
        messages = self.connections[self.current_connection_id].messages
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
        cmd = args[0].strip()
        arg = None if len(args) < 2 else args[1].strip()
        if cmd == '':
            assert not arg
            self.out.error('No command specified')
            cmd = 'help'
        if cmd == 'w': # in case they use GDB style commands when not in GDB
            return self.command(arg)
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

    def show_command(self, arg):
        cap = None
        if arg:
            args = arg.split('~')
            if len(args) == 2:
                try:
                    cap = int(args[1])
                except ValueError:
                    self.out.error('Expected number after \'~\', got \'' + args[1] + '\'')
                    return
            m = self.parse_and_join(args[0], None)
            if not m:
                return
        else:
            m = matcher.always
        self.show_messages(m, cap)

    def connection_command(self, arg):
        if arg:
            arg = no_color(arg)
            if arg in self.connections:
                self.current_connection_id = arg
                self.out.show('Switched to connection ' + repr(arg))
            else:
                self.out.error(repr(arg) + ' is not a known connection')
        for k, v in self.connections.items():
            if k == self.current_connection_id:
                name = color('1;37', ' > ' + k)
            else:
                name = color('37', '   ' + k)
            self.out.show(name + ' (' + str(len(v.messages)) + ' messages)')

    def continue_command(self, arg):
        self.is_stopped = False
        self.out.log('Continuing...')

    def quit_command(self, arg):
        self.should_quit = True

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
