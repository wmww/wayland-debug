import util
if util.check_gdb():
    from .plugin import main
    from .plugin import print_out, print_err
else:
    from .runner import main
