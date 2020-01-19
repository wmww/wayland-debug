import subprocess
import re
import gdb
import util

def verify():
    '''Verifies libwayland debug symbols are available on the system'''
    # First, we use ldconfig to find libwayland
    cmd = ['ldconfig', '-p']
    util.log('Running `' + ' '.join(cmd) + '`')
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = sp.communicate()
    stdout = stdout.decode('utf-8') if stdout != None else ''
    if sp.returncode != 0:
        raise RuntimeError('`' + ' '.join(cmd) + '` exited with code ' + str(sp.returncode))
    # pull out libwayland-client and libwayland-server from the output of ldconfig
    result = re.findall('(libwayland\-(client|server).so) .*=> (/.*)[\n$]', stdout)
    if len(result) == 0:
        raise RuntimeError('Output of `' + ' '.join(cmd) + '` did not contain any Wayland libraries')
    else:
        util.log('Found ' + str(len(result)) + ' Wayland libraries')
    libwayland_paths = [i[2] for i in result]
    for path in libwayland_paths:
        util.log('Loading debug symbols from ' + path)
        result = gdb.execute('add-symbol-file ' + path, to_string=True)
        if result != 'add symbol table from file "' + path + '"\n':
            util.warning('Issue adding libwayland symbol file ' + path + ', output was ' + result)

    # check if it worked
    def check_symbol(symbol, lib):
        if gdb.lookup_global_symbol(symbol) is None:
            util.log(symbol + ' was supposed to be in ' + lib + ', but was not detected')
            raise RuntimeError(lib + ' debug symbols not detected')
            return False
        else:
            util.log(lib + ' debug symbols detected')
            return True

    check_symbol('wl_proxy_create', 'libwayland-client')
    check_symbol('wl_display_add_global', 'libwayland-server')
