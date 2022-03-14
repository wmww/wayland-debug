# Wayland debug

![Wayland Debug sample output](https://i.imgur.com/x95mkA8.png)

A CLI for viewing, filtering, and setting breakpoints on Wayland protocol messages.

## Quickstart
```
$ sudo snap install wayland-debug
$ wayland-debug -g gedit
(gdb) r
Starting program: /usr/bin/gedit
Switching to new client connection A
 0.0000 → wl_display@1a.get_registry(registry=new wl_registry@2a)
 0.0008 → wl_display@1a.sync(callback=new wl_callback@3a)
 0.0015 wl_display@1a.delete_id(id=3) -- wl_callback@3a.destroyed after 0.0007s ↲
…
```

[![Install from the Snap store](https://raw.githubusercontent.com/snapcore/snap-store-badges/master/EN/%5BEN%5D-snap-store-black.png)](https://snapcraft.io/wayland-debug)

## GDB mode (recomended)
Enabled with `-g`/`--gdb`. All subsequent command line arguments are sent directly to a new GDB instance with `wayland-debug` running as a plugin. GDB mode supports setting breakpoints on Wayland messages and handling a single process that creates multiple Wayland connections.

GDB mode requires a libwayland that is built with debug symbols and no inlining (ie a debug build). The `wayland-debug` snap comes with such a libwayland, however if you're using `wayland-debug` some other way or on a system with an older libc, you may need to build libwayland yourself to use GDB mode.

## Pipe/file modes
libwayland has native support for dumping a simplified version of protocol messages. This is enabled by running a Wayland application with the `WAYLAND_DEBUG` environment variable set to `1` (or `client` or `server`). `wayland-debug` can parse these messages (either by loading them from a file, or receiving them via stdin). Note that if a program opens multiple Wayland connections the information becomes ambiguous and `wayland-debug` can't process it (see [#5](https://github.com/wmww/wayland-debug/issues/5)).

## Further info
For a list of command line arguments, run:
```
$ wayland-debug -h
```

Message matchers are used to filter messages and set breakpoints. For matcher syntax documentation, run:
```
$ wayland-debug --matcher-help
```

For a list of GDB mode commands, start GDB mode and run:
```
(gdb) wlh
```

To run in GDB mode without using the snap, or if the libwayland from the snap doesn't work for some reason, you need to [build libwayland from source](https://github.com/wmww/wayland-debug/blob/master/libwayland_debug_symbols.md).

## Examples
In these examples `program` can be any native Wayland app or server, such as `gedit`, `weston-terminal` or `sway`. `wayland-debug` can be replaced with `./main.py` if you're not using the snap.

### Piping messages from stdin
This parses libwayland's default debugging output.
```bash
WAYLAND_DEBUG=1 program 2>&1 | wayland-debug -p
```

### Loading from a file
Similar to the last example, but loads libwayland output from a file.
```bash
WAYLAND_DEBUG=1 program 2>path/to/file.log
wayland-debug -l path/to/file.log
```

### GDB breakpoint
Spin up an instance of GDB, and run the program inside it. Show all messages, but break when an XDG thing is configured or when object ID 12 is used.
```bash
wayland-debug -b 'xdg_*.configure, 12' -g program
(gdb) run
```

### Filtering piped input
Run with piped input only showing pointer, surface.commit and surface.destroy messages.
```bash
WAYLAND_DEBUG=1 program 2>&1 1>/dev/null | wayland-debug -p -f 'wl_pointer, wl_surface.[commit, destroy]'
```

### Negative filter
Load a file showing everything but callbacks and frame messages.
```bash
wayland-debug -l dir/file.log -f '! wl_callback, .frame'
```

## Running the tests
Run the python3 version of pytest (`pytest-3` on Ubuntu) in the project's root directory. The integration tests will attempt to build a Wayland C program, so you'll need the Wayland development libraries as well as meson and ninja.

To install all test dependencies on Ubuntu, run `sudo apt install python3-pytest libwayland-dev wayland-protocols gdb meson ninja-build`. You'll also need your [debug libwayland](libwayland_debug_symbols.md) built (`./resources/get-libwayland.sh`).
