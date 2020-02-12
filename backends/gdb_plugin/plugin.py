import time
import logging
import gdb

import interfaces
from core import wl, output, PersistentUIState
from . import libwayland_symbols
from . import extract

logger = logging.getLogger(__name__)

def time_now():
    return time.perf_counter()

class Stream(output.stream.Base):
    def __init__(self, stream):
        self.stream = stream
    def override_write(self, string):
        gdb.write(string + '\n', self.stream)

def output_streams():
    # Both are stderr, because stdout does the annoying "enter to continue" thing
    return (Stream(gdb.STDERR), Stream(gdb.STDERR))

class WlConnectionDestroyBreakpoint(gdb.Breakpoint):
    def __init__(self, plugin):
        super().__init__('wl_connection_destroy', internal=True)
        self.plugin = plugin
    def stop(self):
        connection_id = str(gdb.selected_frame().read_var('connection'))
        self.plugin.close_connection(connection_id)
        return False

class WlConnectionCreateBreakpoint(gdb.Breakpoint):
    def __init__(self, plugin):
        super().__init__('wl_connection_create', internal=True)
        self.plugin = plugin
    def stop(self):
        self.FinishBreakpoint(self.plugin)
        return False

    class FinishBreakpoint(gdb.FinishBreakpoint):
        def __init__(self, plugin):
            super().__init__(gdb.selected_frame(), internal=True)
            self.plugin = plugin
        def stop(self):
            connection_id = str(self.return_value)
            calling_function = str(gdb.selected_frame().function())
            if calling_function == 'wl_display_connect_to_fd':
                is_server = False
            elif calling_function == 'wl_client_create':
                is_server = True
            else:
                logger.warning(
                    'Unexpected function ' + calling_function + '() called wl_connection_create(), ' +
                    'unable to determine if connection is a client or server at this time')
                is_server = None
            self.plugin.open_connection(connection_id, is_server)
            return False

class WlClosureCallBreakpoint(gdb.Breakpoint):
    def __init__(self, plugin, name, is_sending):
        super().__init__('wl_closure_' + name, internal=True)
        self.plugin = plugin
        self.is_sending = is_sending
    def stop(self):
        self.plugin.process_message(self.is_sending)
        return self.plugin.paused()

class WlCommand(gdb.Command):
    'Issue a subcommand to Wayland Debug, use \'wl help\' for details'
    def __init__(self, plugin, prefix):
        super().__init__(prefix, gdb.COMMAND_DATA)
        self.plugin = plugin
    def invoke(self, arg, from_tty):
        self.plugin.invoke_command(arg)
    def complete(text, word):
        return None

class WlSubcommand(gdb.Command):
    'A Wayland debug command, use \'wl help\' for detail'
    def __init__(self, plugin, command):
        super().__init__('wl' + command, gdb.COMMAND_DATA)
        self.plugin = plugin
        self.command = command
    def invoke(self, arg, from_tty):
        self.plugin.invoke_command(self.command + ' ' + arg)
    def complete(text, word):
        return None

class Plugin:
    '''A GDB plugin (should only be instantiated when inside GDB)'''
    def __init__(self, out, connection_id_sink, command_sink, ui_state):
        assert isinstance(out, output.Output)
        assert isinstance(connection_id_sink, interfaces.ConnectionIDSink)
        assert isinstance(command_sink, interfaces.CommandSink)
        assert isinstance(ui_state, interfaces.UIState)
        self.out = out
        self.connection_id_sink = connection_id_sink
        self.command_sink = command_sink
        self.state = PersistentUIState(ui_state)
        # maps connection ids to thread numbers
        self.connection_threads = {}
        self.catch = False # catch exceptions instead of letting them kill the plugin
        # Show full error messages in the case of a crash
        gdb.execute('set python print-stack full')
        if not self.out.show_unprocessed:
            # Suppress GDB output
            gdb.execute('set inferior-tty /dev/null')
        try:
            # GDB will automatically load the symbols when needed, but if we do it first we get to detect problems
            libwayland_symbols.verify()
        except RuntimeError as e:
            self.out.warn('Loading libwayland symbols failed: ' + str(e))
            self.out.warn('libwayland debug symbols were not found, so Wayland messages may not be detected in GDB mode')
            self.out.warn('See https://github.com/wmww/wayland-debug/blob/master/libwayland_debug_symbols.md for more information')
        WlConnectionCreateBreakpoint(self)
        WlConnectionDestroyBreakpoint(self)
        WlClosureCallBreakpoint(self, 'invoke', False)
        WlClosureCallBreakpoint(self, 'dispatch', False)
        WlClosureCallBreakpoint(self, 'send', True)
        WlClosureCallBreakpoint(self, 'queue', True)
        WlCommand(self, 'w')
        WlCommand(self, 'wl')
        WlCommand(self, 'wayland')
        for command in command_sink.toplevel_commands():
            WlSubcommand(self, command)
        logger.info('Breakpoints: ' + repr(gdb.breakpoints()))

    def open_connection(self, connection_id, is_server):
        try:
            self.connection_threads[connection_id] = gdb.selected_thread().global_num
            self.connection_id_sink.open_connection(time_now(), connection_id, is_server)
        except Exception as e:
            if not self.catch: raise
            self.out.error(repr(e) + ' raised closing connection ' + str(connection_id))

    def close_connection(self, connection_id):
        try:
           self.connection_id_sink.close_connection(time_now(), connection_id)
        except Exception as e:
            if not self.catch: raise
            self.out.error(repr(e) + ' raised closing connection ' + str(connection_id))

    def process_message(self, is_sending):
        if self.state.paused():
            self.state.resume_requested()
        try:
            closure = extract.closure()
            connection_id, object_id, object_type = extract.object(closure)
            message_name, message_args = extract.message(closure)
            object = wl.Object.Unresolved(object_id, object_type)
            message = wl.Message(time_now(), object, is_sending, message_name, message_args)
            current_thread_num = gdb.selected_thread().global_num
            connection_thread_num = self.connection_threads.get(connection_id)
            if connection_thread_num != current_thread_num:
                self.out.warn(
                    'Got message ' + str(message) +
                    ' on thread ' + str(current_thread_num) +
                    ' instead of connection\'s main thread ' + str(connection_thread_num))
        except Exception as e:
            if not self.catch: raise
            self.out.error(repr(e) + ' raised extracting message from GDB')
        try:
            self.connection_id_sink.message(connection_id, message)
        except Exception as e:
            if not self.catch: raise
            self.out.error(repr(e) + ' raised processing message ' + str(message))

    def invoke_command(self, command):
        try:
            self.state.pause_requested()
            self.command_sink.process_command(command)
            if self.state.should_quit():
                gdb.execute('quit')
            elif not self.state.paused():
                gdb.execute('continue')
        except Exception as e:
            if not self.catch: raise
            self.out.error(repr(e) + ' raised invoking command `' + command + '`')

    def paused(self):
        return self.state.paused()
