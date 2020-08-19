project('layer-shell-proxy',
    ['c'],
    version: '0.1.0',
    license: 'MIT',
    meson_version: '>=0.45.1',
    default_options: ['c_std=gnu11', 'warning_level=3'])

add_project_arguments(
    ['-Wno-pedantic', '-Wno-unused-parameter'],
    language: 'c')

wayland_client = dependency('wayland-client', version: '>=1.10.0')
wayland_server = dependency('wayland-server', version: '>=1.10.0')

client_srcs = files(
    'mock_client.c',
    'common.c',
    'client_args.c')

example = executable('mock-client',
    client_srcs,
    dependencies: [wayland_client])

server_srcs = files(
    'mock_server.c',
    'common.c')

example = executable('mock-server',
    server_srcs,
    dependencies: [wayland_server])
