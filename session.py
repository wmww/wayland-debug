import re
from util import *
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

class Session():
    def __init__(self, display_matcher, stop_matcher, output):
        assert display_matcher
        assert stop_matcher
        self.messages = []
        self.commands = [
            Command('help', '[COMMAND]', self.help_command,
                'Show this help message, or get help for a specific command'),
            Command('show', '[MATCHER]', self.show_command,
                'Show messages matching given matcher (or all messages so far if no matcher provided)' +
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

    def show_messages(self, matcher):
        for message in self.messages:
            if matcher.matches(message):
                message.show(self.out)

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

    def show_matcher_parse_failed(self, arg, error):
        self.out.error('Failed to parse "' + arg + '":\n    ' + str(error))

    def filter_command(self, arg):
        if arg:
            try:
                m = matcher.parse(arg)
                self.display_matcher = matcher.join(m, self.display_matcher)
            except RuntimeError as e:
                self.show_matcher_parse_failed(arg, e)
        else:
            self.out.show('Output filter: ' + str(self.display_matcher))

    def break_point_command(self, arg):
        if arg:
            try:
                m = matcher.parse(arg)
                self.stop_matcher = matcher.join(m, self.stop_matcher)
            except RuntimeError as e:
                self.show_matcher_parse_failed(arg, e)
        else:
            self.out.show('Breakpoint matcher: ' + str(self.stop_matcher))

    def show_command(self, arg):
        if arg:
            try:
                m = matcher.parse(arg)
                self.show_messages(m)
            except RuntimeError as e:
                self.show_matcher_parse_failed(arg, e)
        else:
            self.show_messages(matcher.ConstMatcher.always)

    def continue_command(self, arg):
        self.is_stopped = False
        self.out.log('Continuing...')

    def quit_command(self, arg):
        self.should_quit = True

if __name__ == '__main__':
    print('File meant to be imported, not run')
    exit(1)
