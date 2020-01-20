'''
This backend runs wayland-debug as a GDB plugin
This allows detection of multiple Wyland connections and GDB breakpoints on Wayland messages
Note that when running as a GDB plugin, two instances of wayland-debug will be running
- The instance started by the user, which runs GDB (the runner instance)
- The instance insided GDB (the plugin instance)
This module holds logic for both
'''
from core.util import check_gdb

from . import runner

if check_gdb():
    from .plugin import Plugin
    from .plugin import output_streams
else:
    from .runner import run_gdb
