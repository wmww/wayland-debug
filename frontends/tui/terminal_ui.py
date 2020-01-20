import interfaces
from core import PersistentUIState

class TerminalUI:
    def __init__(self, command_sink, ui_state, input_func):
        assert isinstance(command_sink, interfaces.CommandSink)
        assert isinstance(ui_state, interfaces.UIState)
        assert callable(input_func)
        self.command_sink = command_sink
        self.state = PersistentUIState(ui_state)
        self.input_func = input_func

    def run_until_stopped(self):
        self.state.pause_requested()
        while self.state.paused() and not self.state.should_quit():
            cmd = self.input_func('wl debug $ ')
            self.command_sink.process_command(cmd)
