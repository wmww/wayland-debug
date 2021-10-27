import subprocess
import re
import logging
import gdb # type: ignore

def verify() -> None:
    '''Verifies libwayland debug symbols are available on the system'''
    # First, we use ldconfig to find libwayland
    cmd = ['ldconfig', '-p']
    logging.info('Running `' + ' '.join(cmd) + '`')
    sp = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_bytes, stderr_bytes = sp.communicate()
    stdout = stdout_bytes.decode('utf-8') if stdout_bytes is not None else ''
    if sp.returncode != 0:
        raise RuntimeError('`' + ' '.join(cmd) + '` exited with code ' + str(sp.returncode))
    # pull out libwayland-client and libwayland-server from the output of ldconfig
    result = re.findall('(libwayland\-(client|server).so) .*=> (/.*)[\n$]', stdout)
    if len(result) == 0:
        raise RuntimeError('Output of `' + ' '.join(cmd) + '` did not contain any Wayland libraries')
    else:
        logging.info('Found ' + str(len(result)) + ' Wayland libraries')
    libwayland_paths = [i[2] for i in result]
    for path in libwayland_paths:
        logging.info('Loading debug symbols from ' + path)
        result = gdb.execute('add-symbol-file ' + path, to_string=True)
        if result != 'add symbol table from file "' + path + '"\n':
            logging.warning('Issue adding libwayland symbol file ' + path + ', output was ' + result)

    # check if it worked
    def check_symbol(symbol: str, lib: str) -> bool:
        if gdb.lookup_global_symbol(symbol) is None:
            logging.info(symbol + ' was supposed to be in ' + lib + ', but was not detected')
            raise RuntimeError(lib + ' debug symbols not detected')
            return False
        else:
            logging.info(lib + ' debug symbols detected')
            return True

    check_symbol('wl_proxy_create', 'libwayland-client')
    check_symbol('wl_display_add_global', 'libwayland-server')
