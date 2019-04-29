import util
if util.check_gdb():
    from .plugin import main
else:
    from .runner import main
