import re
from util import *
import matcher

help_command_color = '1;37'

def command_format(cmd):
    if check_gdb():
        return '(gdb) wl' + color(help_command_color, cmd)
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

class Session():
    def __init__(self, display_matcher, stop_matcher, output):
        assert display_matcher
        assert stop_matcher
        self.messages = []
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
            Command('continue', None, self.continue_command,
                'Continue processing events'),
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

    def message(self, message):
        self.is_stopped = False
        self.messages.append(message)
        message.resolve_objects(self)
        if self.display_matcher.matches(message):
            message.show(self.out)
        if self.stop_matcher.matches(message):
            self.out.show(color('1;27', '    Stopped at ') + str(message).strip())
            self.is_stopped = True

    def show_messages(self, matcher, cap=None):
        self.out.show('Messages that match ' + str(matcher) + ':')
        matching, didnt_match = self.get_matching(matcher, cap)
        if not matching:
            if not self.messages:
                self.out.show(' ╰╴ No messages yet')
            else:
                assert didnt_match == len(self.messages)
                self.out.show(' ╰╴ None of the ' + color('1;31', str(didnt_match)) + ' messages so far')
        else:
            for message in matching:
                message.show(self.out)
            self.out.show(
                '(' +
                color(('1;32' if len(matching) != cap else '37'), str(len(matching))) +
                ' matched, ' +
                color(('1;31' if didnt_match else '37'), str(didnt_match)) +
                ' didn\'t)')

    def get_matching(self, matcher, cap=None):
        if cap == 0:
            cap = None
        didnt_match = 0
        acc = []
        for message in reversed(self.messages):
            if matcher.matches(message):
                acc.append(message)
                if cap and len(acc) >= cap:
                    break
            else:
                didnt_match += 1
        return (acc, didnt_match)

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

    def continue_command(self, arg):
        self.is_stopped = False
        self.out.log('Continuing...')

    def quit_command(self, arg):
        self.should_quit = True

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
