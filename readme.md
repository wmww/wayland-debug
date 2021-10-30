# Wayland debug

![Wayland Debug sample output](https://i.imgur.com/CliJAqn.png)

A tool for debugging Wayland protocol messages. It integrates directly with with GDB, or can parse the output of a wayland app/compositor run with `WAYLAND_DEBUG=1`

## Examples

### Using GDB (recomended)
This will spin up an instance of GDB with your program
```bash
./main.py -g program
```
In the resulting GDB prompt, just enter `run` to run the program

> Note: to use this mode, you need libwayland debug symbols installed. See [libwayland_debug_symbols.md](libwayland_debug_symbols.md)

### Piping messages from stdin
This parses libwayland's default debugging output
```bash
WAYLAND_DEBUG=1 program 2>&1 | ./main.py
```

### Loading from a file
Similar to the last example, but loads libwayland output from a file
```bash
WAYLAND_DEBUG=1 program 2>path/to/file.log
./main.py -l path/to/file.log
```

## Options
(for a complete list, run `wayland-debug -h`)
```
-h, --help            show this help message and exit

--matcher-help        show how to write matchers and exit

-l ..., --load ...    load Wayland events from a file instead of stdin

-f ..., --filter ...  only show these objects/messages (see --matcher-help for syntax)

-b ..., --break ...   stop on these objects/messages (see --matcher-help for syntax)

-g, --gdb             run as a GDB extension, all subsequent arguments are sent to gdb
```

## Commands
When execution is paused (ie you've hit a breakpoint in GDB), you can issue a number of commands. If you're in GDB, wayland debug commands must be prefixed with 'wl'. When loading from a file, the wl can be dropped.
```
$ help COMMAND               Show this help message, or get help for a specific command

$ show MATCHER [~COUNT]      Show messages matching given matcher (or show all messages, if no matcher provided)
                             Append "~ COUNT" to show at most the last COUNT messages that match
                             See help matcher for matcher syntax

$ filter MATCHER             Show the current output filter matcher, or add a new one
                             See help matcher for matcher syntax

$ breakpoint MATCHER         Show the current breakpoint matcher, or add a new one
                             Use an inverse matcher (^) to disable existing breakpoints
                             See help matcher for matcher syntax

$ matcher MATCHER            Parse a matcher, and show it unsimplified

$ connection CONNECTION      Show Wayland connections, or switch to another connection

$ resume                     Resume processing events
                             In GDB you can also use the continue gdb command

$ quit                       Quit the program
```

## Matchers
Matchers are used through out the program to show and hide messages. A matcher looks similar to how a Wayland message is displayed by this program and libwayland's `WAYLAND_DEBUG=1` output. Matchers can drop components of a message to leave them unspecified, and use wildcards.

Examples of objects:

| Matcher | Description |
| --- | --- |
| `wl_surface`   | Matches any message on a `wl_surface` |
| `xdg_*`        | Matches any message on an XDG type (using a wildcard) |
| `5`            | Matches any message on objects with ID `5` |
| `4#12`         | Matches any message on the `12`th object with ID `4` |
| `.commit`      | Matches any `commit` message |
| `wl_surface.commit`   | Matches `commit` messages on `wl_surface`s |
| `.[motion, button]`   | Matches both `motion` and `button` messages |

TODO: document ! logic

## More examples
```bash
# Spin up an instance of GDB, and run the program inside it.
# Show all messages, but break when an XDG thing is configured or when object ID 12 is used
./main.py -b 'xdg_*.configure, 12' -g program
...
(gdb) run

# Run with piped input only showing pointer, surface.commit and surface.destroy messages
WAYLAND_DEBUG=1 program 2>&1 1>/dev/null | ./main.py -f 'wl_pointer, wl_surface.[commit, destroy]'

# Load a file showing everything but callbacks and frame messages
./main.py -l dir/file.log -f '! wl_callback, .frame'
```

## Running the tests
Run the python3 version of pytest (`pytest-3` on Ubuntu) in the project's root directory. The integration tests will attempt to build a Wayland C program, so you'll need the Wayland development libraries as well as meson and ninja.

To install all test dependencies on Ubuntu, run `sudo apt install python3-pytest libwayland-dev wayland-protocols libwayland-server0-dbgsym libwayland-client0-dbgsym gdb meson ninja-build`. If you haven't enabled [debug symbols](libwayland_debug_symbols.md), you'll need to do that first.
