import util
if util.check_gdb():
    from .plugin import Plugin
    from .plugin import output_streams
else:
    from .runner import run_gdb
