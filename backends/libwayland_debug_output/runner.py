import subprocess
import os
import threading
import logging
from typing import List, Dict, Callable

from interfaces import UIState, ConnectionIDSink, CommandSink
from frontends.tui import Arguments, TerminalUI
from core.output import Output
from . import parse

class _Subprocess:
    def __init__(self, args: Arguments, stderr_fd: int):
        self.args = args
        self.stderr_fd = stderr_fd
        self.returncode: int = 99

    def run(self) -> None:
        env = os.environ.copy()
        # Add libwayland libs to LD_PRELOAD
        env['LD_PRELOAD'] = ':'.join([env.get('LD_PRELOAD', '')] + self.args.wayland_libs)
        env['WAYLAND_DEBUG'] = '1'
        logging.info('Running ' + repr(self.args.command_args))
        self.returncode = subprocess.run(
            self.args.command_args,
            stderr=self.stderr_fd,
            env=env,
            bufsize=1,
        ).returncode
        logging.info('Program finished with exit code ' + str(self.returncode))
        os.close(self.stderr_fd)

def run_program(
    output: Output,
    args: Arguments,
    connection_id_sink: ConnectionIDSink,
    command_sink: CommandSink,
    ui_state: UIState,
    input_func: Callable[[str], str]
) -> int:
    ui = TerminalUI(command_sink, ui_state, input_func)
    readable, writable = os.pipe()
    subprocess = _Subprocess(args, writable)
    thread = threading.Thread(name='subprocess', target=subprocess.run)
    thread.start()
    with os.fdopen(readable, 'r') as spicket:
        parse.into_sink(spicket, output, connection_id_sink)
    thread.join(timeout=1)
    assert not thread.is_alive(), 'Failed to join subprocess thread'
    ui.run_until_stopped()
    return subprocess.returncode
