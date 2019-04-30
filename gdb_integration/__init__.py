import util
if util.check_gdb():
    from .plugin import main
    from .plugin import output_streams
else:
    from .runner import main
