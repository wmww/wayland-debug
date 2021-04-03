import os
import subprocess
import shutil

import main
from backends import gdb_plugin
from core.output import stream
from core.util import no_color

gdb_log_path = '/tmp/gdb_log.txt'

def get_project_path() -> str:
    project = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    # Use the presence of LICENSE to make sure the path is correct
    license = os.path.join(project, 'LICENSE');
    assert os.path.isfile(license), license + ' not found, this may indicate the project path is wrong'
    return project

def log_file_path(name) -> str:
    path = 'resources/libwayland_debug_logs/' + name + '.log'
    assert os.path.isfile(path), get_project_path() + '/' + path + ' is not a file'
    return path

def short_log_file() -> str:
    return log_file_path('short')

def server_obj_log_file() -> str:
    return log_file_path('gedit-with-server-owned-objects')

def find_bin(name: str) -> str:
    '''Returns the path to a program if it exists on the system, or an empty string otherwise'''
    path = shutil.which(name);
    if path is not None:
        return path
    else:
        return ''

def wayland_socket_exists():
    xdg_runtime_dir = os.getenv('XDG_RUNTIME_DIR')
    if not xdg_runtime_dir:
        xdg_runtime_dir = '/run/user/1000'
    return os.path.exists(xdg_runtime_dir + '/wayland-0')

def get_main_path():
    main_path = 'main.py'
    assert os.path.isfile(main_path), get_project_path() + '/' + main_path + ' is not a file'
    return main_path

def run_main(args):
    assert isinstance(args, list)
    args = [get_main_path()] + args
    out = stream.String()
    err = stream.String()
    input_func = lambda msg: 'q'
    main.main(out, err, args, input_func)
    assert err.buffer == '', err.buffer
    return out.buffer

def run_in_gdb(wldbg_args, gdb_args, also_run):
    assert isinstance(wldbg_args, list)
    assert isinstance(gdb_args, list)
    assert also_run is None or isinstance(also_run, list)

    if not os.environ.get('XDG_RUNTIME_DIR'):
        tmp_runtime_dir = '/tmp/wldbg-runtime-dir'
        try:
            os.mkdir(tmp_runtime_dir)
        except FileExistsError:
            pass
        print('XDG_RUNTIME_DIR not set. Setting to ' + tmp_runtime_dir)
        os.environ['XDG_RUNTIME_DIR'] = tmp_runtime_dir

    wayland_display_path = os.environ.get('XDG_RUNTIME_DIR') + '/wayland-wldbg-test'
    os.environ['WAYLAND_DISPLAY'] = os.path.basename(wayland_display_path)
    if os.path.exists(wayland_display_path):
        os.remove(wayland_display_path)
    if os.path.exists(wayland_display_path + '.lock'):
        os.remove(wayland_display_path + '.lock')

    gdb_args = ['-ex', 'set logging file ' + gdb_log_path, '-ex', 'set logging on'] + gdb_args
    args = gdb_plugin.runner.Args([get_main_path()] + wldbg_args, gdb_args)
    if os.path.exists(gdb_log_path):
        os.remove(gdb_log_path)

    if also_run:
        other_process = subprocess.Popen(also_run, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    gdb_plugin.run_gdb(args)

    if also_run:
        out, _ = other_process.communicate(timeout=1)
        out_str = out.decode('utf-8')
        if other_process.returncode != 0:
            raise RuntimeError('Server exit code: ' + str(other_process.returncode) + ', Output: ' + out_str)

    if os.path.exists(gdb_log_path):
        with open(gdb_log_path, 'r') as f:
            result = f.read()
            result = no_color(result) # I *think* Ubuntu 20.04 GDB strips color itself, but 18.04 GDB does not
    else:
        result = ''

    return result

mock_program_path = 'test/mock_program'

def build_mock_program():
    meson = find_bin('meson')
    ninja = find_bin('ninja')
    assert meson and ninja, 'meson and ninja needed to build mock program'
    build_dir = os.path.join(mock_program_path, 'build')
    if not os.path.isdir(build_dir):
        subprocess.run([meson, 'build'], cwd = mock_program_path).check_returncode()
    subprocess.run([ninja, '-C', build_dir]).check_returncode()
    bin_paths = (
        os.path.join(build_dir, 'mock-client'),
        os.path.join(build_dir, 'mock-server'))
    for path in bin_paths:
        assert os.path.isfile(path)
    return bin_paths
