from typing import Callable

from interfaces import CommandSink, UIState
from core import PersistentUIState

class TerminalUI:
    def __init__(self, command_sink: CommandSink, ui_state: UIState, input_func: Callable[[str], str]) -> None:
        self.command_sink = command_sink
        self.state = PersistentUIState(ui_state)
        self.input_func = input_func

    def run_until_stopped(self) -> None:
        self.state.pause_requested()
        while self.state.paused() and not self.state.should_quit():
            cmd = self.input_func('wl debug $ ')
            self.command_sink.process_command(cmd)
